"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .config import GlobalConf, DeckConf
from .deck_manager import DeckManager
from .decorators import must_be_enabled
from .settings import GlobalSettings, DeckSettings


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
    }

    _global_settings = None
    _deck_settings = None
    _timer = None

    def __init__(self, make_timer, mw, qt):
        """Initializes DeckManager and Settings, and add-on initial setup.

        Args:
            make_timer: A function that creates a timer.
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self.config = GlobalConf(mw)
        deck_config = DeckConf(mw)

        self.deck_manager = DeckManager(mw, qt, self.config, deck_config)
        self._global_settings = GlobalSettings(qt, self.config)
        self._deck_settings = DeckSettings(qt, deck_config)
        self._timer = make_timer(
            100, lambda: self.deck_manager.recover_life(False, 0.1), True)
        self._timer.stop()

    def global_settings(self):
        """Opens a dialog with the Global Settings."""
        drain_enabled = self._timer.isActive()
        self.toggle_drain(False)
        self._global_settings.open()
        self.toggle_drain(drain_enabled)
        self.deck_manager.update()

    def deck_settings(self):
        """Opens a dialog with the Deck Settings."""
        life = self.deck_manager.get_current_life()
        set_deck_conf = self.deck_manager.set_deck_conf

        drain_enabled = self._timer.isActive()
        self.toggle_drain(False)
        self._deck_settings.open(life, set_deck_conf)
        self.toggle_drain(drain_enabled)
        self.deck_manager.update()

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
