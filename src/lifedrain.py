# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Union

from . import settings
from .database import DeckConf, GlobalConf
from .deck_manager import DeckManager
from .decorators import must_be_enabled

if TYPE_CHECKING:
    from anki.cards import Card
    from aqt.main import AnkiQt, MainWindowState


class Lifedrain:
    """The main class of the Life Drain add-on.

    Implements some basic functions of the Life Drain. Also intermediates some
    complex functionalities implemented in other classes.

    Attributes:
        config: An instance of GlobalConf.
        deck_manager: An instance of DeckManager.
        status: A dictionary that keeps track the events on Anki.
    """

    def __init__(self, mw: AnkiQt, qt: Any):
        """Initializes DeckManager and Settings, and add-on initial setup.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._qt = qt
        self._mw = mw
        self.config = GlobalConf(mw)
        self._deck_config = DeckConf(mw)
        self.deck_manager = DeckManager(mw, qt, self.config, self._deck_config)
        self.status: dict[str, Any] = {
            'action': None,  # Flag for bury, suspend, delete
            'reviewed': False,
            'review_response': 0,
            'screen': None,
            'shortcuts': [],
            'card_type': None,
        }

    def reset_daily(self) -> None:
        """Resets the lifedrain bar for all decks once per day.

        Uses Anki's rollover hour instead of a hard-coded 4am.
        """
        # Safely get the rollover hour from Anki's config.
        # Default to 4 if it's not set.
        if self._mw.col is None:
            exp = 'Collection is not loaded'
            raise RuntimeError(exp)
        rollover_hour = self._mw.col.conf.get('rollover', 4)

        effective_date = (datetime.now().astimezone() - timedelta(hours=rollover_hour)).date()
        if not hasattr(self, '_last_reset_date') or self._last_reset_date != effective_date:
            for bar_info in self.deck_manager.bar_infos.values():
                self.deck_manager.recover(bar_info)
            self._last_reset_date = effective_date

    def global_settings(self) -> None:
        """Opens a dialog with the Global Settings."""
        drain_enabled = self.deck_manager.timer.isActive()
        self.toggle_drain(enable=False)
        settings.global_settings(
            aqt=self._qt,
            mw=self._mw,
            config=self.config,
            deck_manager=self.deck_manager,
        )
        config = self.config.get()
        if config['enable']:
            self.update_global_shortcuts()
            self.toggle_drain(drain_enabled)
            self.deck_manager.update(self.status['screen'])
        else:
            self.update_global_shortcuts()
            self.deck_manager.hide_life_bar()

    def deck_settings(self) -> None:
        """Opens a dialog with the Deck Settings."""
        drain_enabled = self.deck_manager.timer.isActive()
        self.toggle_drain(enable=False)
        settings.deck_settings(
            aqt=self._qt,
            mw=self._mw,
            config=self._deck_config,
            global_config=self.config,
            deck_manager=self.deck_manager,
        )
        self.toggle_drain(drain_enabled)
        self.deck_manager.update(self.status['screen'])

    def update_global_shortcuts(self) -> None:
        """Update the global shortcuts."""
        for shortcut in self.status['shortcuts']:
            self._qt.sip.delete(shortcut)
        self.status['shortcuts'] = []

        config = self.config.get()
        if config['globalSettingsShortcut']:
            self.status['shortcuts'] = self._mw.applyShortcuts(
                [
                    (config['globalSettingsShortcut'], self.global_settings),
                ],
            )

    def review_shortcuts(self, shortcuts: list[tuple]) -> None:
        """Generates the review screen shortcuts."""
        config = self.config.get()
        if config['deckSettingsShortcut']:
            shortcuts.append((config['deckSettingsShortcut'], self.deck_settings))
        if config['enable'] and config['pauseShortcut']:
            shortcuts.append((config['pauseShortcut'], self.toggle_drain))

    def overview_shortcuts(self, shortcuts: list[tuple]) -> None:
        """Generates the overview screen shortcuts."""
        config = self.config.get()
        if config['deckSettingsShortcut']:
            shortcuts.append((config['deckSettingsShortcut'], self.deck_settings))
        if config['enable'] and config['recoverShortcut']:

            def start_recover() -> None:
                self.deck_manager.recovering = True
                self.toggle_drain()

            shortcuts.append((config['recoverShortcut'], start_recover))

    def screen_change(self, state: MainWindowState) -> None:
        """Updates Life Drain when the screen changes.

        Args:
            state: The name of the current screen.
        """
        if state not in ['deckBrowser', 'overview', 'review']:
            return

        # Check for a new day (using 4am boundary) and reset if needed
        self.reset_daily()

        self.status['screen'] = state
        config = self.config.get()
        if not config['enable']:
            return

        self.deck_manager.update(state)
        if state != 'review':
            self.toggle_drain(enable=False)
            self.status['prev_card'] = None
        if state != 'overview':
            self.deck_manager.recovering = False
        if state != 'deckBrowser' and self.status['reviewed']:
            self.deck_manager.answer(
                self.status['review_response'],
                self.status['card_type'],
            )
        self.status['reviewed'] = False

    @must_be_enabled
    def opened_window(self, config: dict[str, Any]) -> None:
        """Called when a window is opened while reviewing."""
        if config['stopOnLostFocus']:
            self.toggle_drain(enable=False)

    @must_be_enabled
    def show_question(self, config: dict[str, Any], card: Card) -> None:
        """Called when a question is shown."""
        self.toggle_drain(enable=True)
        if self.status['action'] == 'undo':
            self.deck_manager.undo()
        elif self.status['action'] == 'bury':
            self.deck_manager.action(config['behavBury'])
        elif self.status['action'] == 'suspend':
            self.deck_manager.action(config['behavSuspend'])
        elif self.status['action'] == 'delete':
            self.deck_manager.action(config['behavUndo'])
        elif self.status['reviewed']:
            self.deck_manager.answer(
                self.status['review_response'],
                self.status['card_type'],
            )
        self.status['reviewed'] = False
        self.status['action'] = None
        self.status['card_type'] = card.type

    @must_be_enabled
    def show_answer(self, config: dict[str, Any]) -> None:
        """Called when an answer is shown."""
        self.toggle_drain(not config['stopOnAnswer'])
        self.status['reviewed'] = True

    @must_be_enabled
    def toggle_drain(
        self,
        _config: dict[str, Any],
        enable: Union[bool, None] = None,
    ) -> None:
        """Toggles the life drain.

        Args:
            config: Global configuration dictionary.
            enable: Optional. Enables the drain if True.
        """
        is_active = self.deck_manager.timer.isActive()
        if is_active and enable is not True:
            self.deck_manager.timer.stop()
        elif not is_active and enable is not False:
            self.deck_manager.timer.start()
