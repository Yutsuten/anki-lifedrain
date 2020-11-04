"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .config import GlobalConf, DeckConf
from .deck_manager import DeckManager
from .decorators import must_be_enabled
from . import settings


class Lifedrain:
    """The main class of the Life Drain add-on.

    Implements some basic functions of the Life Drain. Also intermediates some
    complex functionalities implemented in another classes.

    Attributes:
        config: An instance of GlobalConf.
        deck_manager: An instance of DeckManager.
        status: A dictionary that keeps track the events on Anki.
    """

    config = None
    deck_manager = None
    status = {
        'special_action': False,  # Flag for bury, suspend, remove, leech
        'reviewed': False,
        'review_response': 0,
        'screen': None,
        'shortcuts': [],
    }

    _qt = None
    _mw = None
    _dconfig = None
    _timer = None

    def __init__(self, make_timer, mw, qt):
        """Initializes DeckManager and Settings, and add-on initial setup.

        Args:
            make_timer: A function that creates a timer.
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._qt = qt
        self._mw = mw
        self.config = GlobalConf(mw)
        self._dconfig = DeckConf(mw)

        self.deck_manager = DeckManager(mw, qt, self.config, self._dconfig)
        self._timer = make_timer(
            100, lambda: self.deck_manager.recover_life(False, 0.1), True)
        self._timer.stop()

    def global_settings(self):
        """Opens a dialog with the Global Settings."""
        drain_enabled = self._timer.isActive()
        self.toggle_drain(False)
        settings.global_settings(self._qt, self.config)
        self.clear_global_shortcuts()
        self.set_global_shortcuts()
        self.toggle_drain(drain_enabled)
        self.deck_manager.update()

    def deck_settings(self):
        """Opens a dialog with the Deck Settings."""
        drain_enabled = self._timer.isActive()
        self.toggle_drain(False)
        settings.deck_settings(self._qt, self._dconfig, self.deck_manager)
        self.toggle_drain(drain_enabled)
        self.deck_manager.update()

    def clear_global_shortcuts(self):
        """Clear the global shortcuts."""
        for shortcut in self.status['shortcuts']:
            self._qt.sip.delete(shortcut)
        self.status['shortcuts'] = []

    @must_be_enabled
    def set_global_shortcuts(self):
        """Sets the global shortcuts."""
        config = self.config.get()
        if not config['globalSettingsShortcut']:
            return

        shortcuts = [
            tuple([config['globalSettingsShortcut'], self.global_settings])
        ]
        self.status['shortcuts'] = self._mw.applyShortcuts(shortcuts)

    def review_shortcuts(self, shortcuts):
        """Generates the review screen shortcuts."""
        config = self.config.get()
        if config['pauseShortcut']:
            shortcuts.append(
                tuple([config['pauseShortcut'], self.toggle_drain])
            )
        if config['deckSettingsShortcut']:
            shortcuts.append(
                tuple([config['deckSettingsShortcut'], self.deck_settings])
            )

    def overview_shortcuts(self, shortcuts):
        """Generates the overview screen shortcuts."""
        config = self.config.get()
        if config['deckSettingsShortcut']:
            shortcuts.append(
                tuple([config['deckSettingsShortcut'], self.deck_settings])
            )
        if config['recoverShortcut']:
            def full_recover():
                self.deck_manager.recover_life(value=10000)

            shortcuts.append(
                tuple([config['recoverShortcut'], full_recover])
            )

    @must_be_enabled
    def toggle_drain(self, enable=None):
        """Toggles the life drain.

        Args:
            enable: Optional. Enables the drain if True.
        """
        if self._timer.isActive() and enable is not True:
            self._timer.stop()
        elif not self._timer.isActive() and enable is not False:
            self._timer.start()

    @must_be_enabled
    def screen_change(self, state):
        """Updates Life Drain when the screen changes.

        Args:
            state: The name of the current screen.
        """
        if state != 'review':
            self.toggle_drain(False)

        if self.status['reviewed'] and state in ['overview', 'review']:
            self.deck_manager.recover_life()

        self.status['reviewed'] = False
        self.status['screen'] = state

        if state == 'deckBrowser':
            self.deck_manager.bar_visible(False)
        else:
            self.deck_manager.update()
            self.deck_manager.bar_visible(True)

    @must_be_enabled
    def show_question(self):
        """Called when a question is shown."""
        self.toggle_drain(True)
        if self.status['reviewed']:
            if self.status['review_response'] == 1:
                self.deck_manager.recover_life(damage=True)
            else:
                self.deck_manager.recover_life()
        self.status['reviewed'] = False
        self.status['special_action'] = False

    @must_be_enabled
    def show_answer(self):
        """Called when an answer is shown."""
        conf = self.config.get()
        self.toggle_drain(not conf['stopOnAnswer'])
        self.status['reviewed'] = True

    @must_be_enabled
    def undo(self):
        """Called when an undo event happens on Anki. Not so accurate though."""
        on_review = self.status['screen'] == 'review'
        if on_review and not self.status['special_action']:
            self.status['reviewed'] = False
            self.deck_manager.recover_life(False)
        self.status['special_action'] = False
