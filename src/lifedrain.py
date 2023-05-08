# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from typing import Any, Callable, Optional

from anki.cards import Card
from aqt.main import AnkiQt, MainWindowState

from . import settings
from .database import DeckConf, GlobalConf
from .deck_manager import DeckManager
from .decorators import must_be_enabled


class Lifedrain:
    """The main class of the Life Drain add-on.

    Implements some basic functions of the Life Drain. Also intermediates some
    complex functionalities implemented in another classes.

    Attributes:
        config: An instance of GlobalConf.
        deck_manager: An instance of DeckManager.
        status: A dictionary that keeps track the events on Anki.
    """

    config: Optional[GlobalConf] = None
    deck_config: Optional[DeckConf] = None
    deck_manager: Optional[DeckManager] = None
    status = {
        'action': None,  # Flag for bury, suspend, delete
        'reviewed': False,
        'review_response': 0,
        'screen': None,
        'shortcuts': [],
        'card_type': None,
    }

    _qt: Any = None
    _mw: Optional[AnkiQt] = None
    _timer: Optional[Callable] = None

    def __init__(self, make_timer: Callable, mw: AnkiQt, qt: Any):
        """Initializes DeckManager and Settings, and add-on initial setup.

        Args:
            make_timer: A function that creates a timer.
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._qt = qt
        self._mw = mw
        self.config = GlobalConf(mw)
        self.deck_config = DeckConf(mw)
        deck_manager = DeckManager(mw, qt, self.config, self.deck_config)

        self.deck_manager = deck_manager
        self._timer = make_timer(
            100,
            lambda: deck_manager.recover_life(increment=False, value=0.1),
            repeat=True,
            parent=mw,
        )
        self._timer.stop()

    def global_settings(self) -> None:
        """Opens a dialog with the Global Settings."""
        if self._timer is None:
            raise RuntimeError
        if self.config is None:
            raise RuntimeError
        if self.deck_manager is None:
            raise RuntimeError
        if self.deck_manager.bar_visible is None:
            raise RuntimeError

        drain_enabled = self._timer.isActive()
        self.toggle_drain(enable=False)
        settings.global_settings(
            self._qt, self._mw, self.config, self.deck_manager)
        config = self.config.get()
        if config['enable']:
            self.clear_global_shortcuts()
            self.set_global_shortcuts()
            self.toggle_drain(drain_enabled)
            if self.status['screen'] == 'deckBrowser':
                self.deck_manager.bar_visible(visible=False)
            else:
                self.deck_manager.update()
                self.deck_manager.bar_visible(visible=True)
        else:
            self.clear_global_shortcuts()
            self.deck_manager.bar_visible(visible=False)

    def deck_settings(self) -> None:
        """Opens a dialog with the Deck Settings."""
        if self._timer is None:
            raise RuntimeError
        if self.deck_manager is None:
            raise RuntimeError

        drain_enabled = self._timer.isActive()
        self.toggle_drain(enable=False)
        settings.deck_settings(
            self._qt,
            self._mw,
            self.deck_config,
            self.config,
            self.deck_manager,
        )
        self.toggle_drain(drain_enabled)
        self.deck_manager.update()

    def clear_global_shortcuts(self) -> None:
        """Clear the global shortcuts."""
        if self._qt is None:
            raise RuntimeError

        for shortcut in self.status['shortcuts']:
            self._qt.sip.delete(shortcut)
        self.status['shortcuts'] = []

    @must_be_enabled
    def set_global_shortcuts(self, config: dict[str, Any]) -> None:
        """Sets the global shortcuts."""
        if not config['globalSettingsShortcut']:
            return
        if self._mw is None:
            raise RuntimeError

        shortcuts = [
            (config['globalSettingsShortcut'], self.global_settings),
        ]
        self.status['shortcuts'] = self._mw.applyShortcuts(shortcuts)

    @must_be_enabled
    def review_shortcuts(self, config: dict[str, Any], shortcuts: list[tuple]) -> None:
        """Generates the review screen shortcuts."""
        if config['pauseShortcut']:
            shortcuts.append(
                (config['pauseShortcut'], self.toggle_drain),
            )
        if config['deckSettingsShortcut']:
            shortcuts.append(
                (config['deckSettingsShortcut'], self.deck_settings),
            )

    @must_be_enabled
    def overview_shortcuts(self, config: dict[str, Any], shortcuts: list[tuple]) -> None:
        """Generates the overview screen shortcuts."""
        if config['deckSettingsShortcut']:
            shortcuts.append(
                (config['deckSettingsShortcut'], self.deck_settings),
            )
        if config['recoverShortcut']:
            def full_recover() -> None:
                if self.deck_manager is None:
                    raise RuntimeError
                self.deck_manager.recover_life(value=10000)

            shortcuts.append(
                (config['recoverShortcut'], full_recover),
            )

    @must_be_enabled
    def toggle_drain(self, config: dict[str, Any], enable=None) -> None:  # noqa: ARG
        """Toggles the life drain.

        Args:
            enable: Optional. Enables the drain if True.
        """
        if self._timer is None:
            raise RuntimeError

        if self._timer.isActive() and enable is not True:
            self._timer.stop()
        elif not self._timer.isActive() and enable is not False:
            self._timer.start()

    def screen_change(self, state: MainWindowState) -> None:
        """Updates Life Drain when the screen changes.

        Args:
            state: The name of the current screen.
        """
        if state not in ['deckBrowser', 'overview', 'review']:
            return

        if self.config is None:
            raise RuntimeError
        if self.deck_config is None:
            raise RuntimeError
        if self.deck_manager is None:
            raise RuntimeError
        if self.deck_manager.bar_visible is None:
            raise RuntimeError

        self.status['screen'] = state
        config = self.config.get()
        self.deck_config.get()
        if not config['enable']:
            return

        if state != 'review':
            self.toggle_drain(enable=False)
            self.status['prev_card'] = None

        if self.status['reviewed'] and state in ['overview', 'review']:
            self.deck_manager.answer(
                self.status['review_response'],
                self.status['card_type'],
            )
            self.status['reviewed'] = False

        if state == 'deckBrowser':
            self.deck_manager.bar_visible(visible=False)
        else:
            self.deck_manager.update()
            self.deck_manager.bar_visible(visible=True)

    @must_be_enabled
    def opened_window(self, config: dict[str, Any]) -> None:
        """Called when a window is opened while reviewing."""
        if config['stopOnLostFocus']:
            self.toggle_drain(enable=False)

    @must_be_enabled
    def show_question(self, config: dict[str, Any], card: Card) -> None:
        """Called when a question is shown."""
        if self.deck_manager is None:
            raise RuntimeError

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
