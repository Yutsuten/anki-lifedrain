"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from .deck_manager import DeckManager
from .decorators import must_be_enabled
from .defaults import DEFAULTS
from .settings import Settings


class Lifedrain(object):
    """The main class of the Life Drain add-on.

    Implements some basic functions of the Life Drain. Also intermediates some
    complex functionalities implemented in another classes.

    Attributes:
        deck_manager: An instance of DeckManager.
        main_window: A reference to the Anki's main window.
        status: A dictionary that keeps track of the state of the events on Anki.
        preferences_ui: Function that generates the Global Settings dialog.
        deck_settings_ui: Function that generates the Deck Settings dialog.
        custom_deck_settings_ui: Function that generates the Filtered Deck Settings dialog.
    """

    deck_manager = None
    main_window = None
    status = {
        'card_new_state': False,
        'reviewed': False,
        'review_response': 0,
        'screen': None,
    }
    preferences_ui = None
    deck_settings_ui = None
    custom_deck_settings_ui = None

    _settings = None
    _timer = None

    def __init__(self, make_timer, mw, qt):
        """Initializes a DeckManager and Settings instances, and add-on initial setup.

        Args:
            make_timer: A function that creates a timer.
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self.deck_manager = DeckManager(mw, qt)
        self.main_window = mw
        self._settings = Settings(qt)
        self._timer = make_timer(100, lambda: self.deck_manager.recover_life(False, 0.1), True)
        self._timer.stop()

        self.preferences_ui = self._settings.preferences_ui
        self.deck_settings_ui = self._settings.deck_settings_ui
        self.custom_deck_settings_ui = self._settings.custom_deck_settings_ui

        # Configure separator strip
        mw.setStyleSheet('QMainWindow::separator { width: 0px; height: 0px; }')
        try:
            import Night_Mode
            Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
        except Exception:  # nosec  # pylint: disable=broad-except
            pass

    def preferences_load(self, pref):
        """Loads Life Drain global settings into the Global Settings dialog.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        self._settings.preferences_load(pref)
        self.toggle_drain(False)

    def preferences_save(self, pref):
        """Saves Life Drain global settings.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        conf = self._settings.preferences_save(pref)

        self.status['card_new_state'] = True
        self.status['reviewed'] = False

        if conf['disable'] is True:
            self.deck_manager.bar_visible(False)

    def deck_settings_load(self, settings):
        """Loads Life Drain deck settings into the Deck Settings dialog.

        Args:
            settings: The instance of the Deck Settings dialog.
        """
        self._settings.deck_settings_load(
            settings,
            self.deck_manager.get_deck_conf(settings.deck['id'])['currentValue']
        )
        self.toggle_drain(False)

    def deck_settings_save(self, settings):
        """Saves Life Drain deck settings.

        Args:
            settings: The instance of the Deck Settings dialog.
        """
        deck_conf = self._settings.deck_settings_save(settings)
        self.deck_manager.set_deck_conf(settings.deck['id'], deck_conf)
        self.status['card_new_state'] = True
        self.status['reviewed'] = False

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
            self.deck_manager.set_deck(self.main_window.col.decks.current()['id'])
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
        self.status['card_new_state'] = False

    @must_be_enabled
    def show_answer(self):
        """Called when an answer is shown."""
        conf = self.main_window.col.conf
        self.toggle_drain(not conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer']))
        self.status['reviewed'] = True

    @must_be_enabled
    def undo(self):
        """Called when an undo event happens on Anki. Not so accurate though."""
        if self.status['screen'] == 'review' and not self.status['card_new_state']:
            self.status['reviewed'] = False
            self.deck_manager.recover_life(False)
        self.status['card_new_state'] = False
