'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .deck_manager import DeckManager
from .decorators import must_be_enabled
from .defaults import DEFAULTS
from .settings import Settings


class Lifedrain(object):
    '''
    Contains the state and functions of the life drain.
    '''
    deck_manager = None
    mw = None
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
        self.deck_manager = DeckManager(qt, mw)
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
        '''
        Loads Life Drain global configurations into the Global Settings dialog.
        '''
        self._settings.preferences_load(pref)
        self.toggle_drain(False)

    def preferences_save(self, pref):
        '''
        Saves Life Drain global configurations.
        '''
        conf = self._settings.preferences_save(pref)

        self.status['card_new_state'] = True
        self.status['reviewed'] = False

        if conf['disable'] is True:
            self.deck_manager.bar_visible(False)

    def deck_settings_load(self, settings):
        '''
        Loads Life Drain deck configurations into the Deck Settings dialog.
        '''
        self._settings.deck_settings_load(
            settings,
            self.deck_manager.get_deck_conf(settings.deck['id'])['currentValue']
        )
        self.toggle_drain(False)

    def deck_settings_save(self, settings):
        '''
        Saves LifeDrain deck configurations.
        '''
        deck_conf = self._settings.deck_settings_save(settings)
        self.deck_manager.set_deck_conf(settings.deck['id'], deck_conf)
        self.status['card_new_state'] = True
        self.status['reviewed'] = False

    @must_be_enabled
    def toggle_drain(self, enable=None):
        '''
        Toggle the timer to pause/unpause the drain.
        '''
        if self._timer.isActive() and enable is not True:
            self._timer.stop()
        elif not self._timer.isActive() and enable is not False:
            self._timer.start()

    @must_be_enabled
    def screen_change(self, state):
        '''
        When screen changes, update state of the lifedrain.
        '''
        if state != 'review':
            self.toggle_drain(False)

        if self.status['reviewed'] and state in ['overview', 'review']:
            self.deck_manager.recover_life()

        self.status['reviewed'] = False
        self.status['screen'] = state

        if state == 'deckBrowser':
            self.deck_manager.bar_visible(False)
        elif self.main_window.col is not None:
            self.deck_manager.set_deck(self.main_window.col.decks.current()['id'])
            self.deck_manager.bar_visible(True)

    @must_be_enabled
    def show_question(self):
        '''
        Called when a question is shown.
        '''
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
        '''
        Called when an answer is shown.
        '''
        conf = self.main_window.col.conf
        self.toggle_drain(not conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer']))
        self.status['reviewed'] = True

    @must_be_enabled
    def undo(self):
        '''
        Deals with undoing.
        '''
        if self.status['screen'] == 'review' and not self.status['card_new_state']:
            self.status['reviewed'] = False
            self.deck_manager.recover_life(False)
        self.status['card_new_state'] = False
