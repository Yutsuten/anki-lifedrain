'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .deck_manager import DeckManager
from .defaults import DEFAULTS
from .settings import Settings


class Lifedrain(object):
    '''
    Contains the state and functions of the life drain.
    '''
    status = {
        'disable': None,
        'card_new_state': False,
        'reviewed': False,
        'review_response': 0,
        'screen': None,
        'stop_on_answer': None
    }
    preferences_ui = None
    deck_settings_ui = None
    custom_deck_settings_ui = None

    _deck_manager = None
    _mw = None
    _settings = None
    _timer = None

    def __init__(self, make_timer, mw, qt):
        self._timer = make_timer(100, lambda: self.recover(False, 0.1), True)
        self._settings = Settings(qt)
        self._deck_manager = DeckManager(qt, mw)
        self._mw = mw

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

        self.status['disable'] = conf['disable']
        self.status['stop_on_answer'] = conf['stopOnAnswer']
        self.status['card_new_state'] = True

        if self.status['disable']:
            self._deck_manager.bar_visible(False)

    def deck_settings_load(self, settings):
        '''
        Loads Life Drain deck configurations into the Deck Settings dialog.
        '''
        self._settings.deck_settings_load(
            settings,
            self._deck_manager.get_deck_conf(settings.deck['id'])['currentValue']
        )
        self.toggle_drain(False)

    def deck_settings_save(self, settings):
        '''
        Saves LifeDrain deck configurations.
        '''
        deck_conf = self._settings.deck_settings_save(settings)
        self._deck_manager.set_deck_conf(settings.deck['id'], deck_conf)
        self.status['card_new_state'] = True

    def toggle_drain(self, enable=None):
        '''
        Toggle the timer to pause/unpause the drain.
        '''
        if self.status['disable']:
            return

        if self._timer.isActive() and enable is not True:
            self._timer.stop()
        elif not self._timer.isActive() and enable is not False:
            self._timer.start()

    def recover(self, *args, **kwargs):
        '''
        Recover life.
        '''
        self._deck_manager.recover(*args, **kwargs)

    def screen_change(self, state):
        '''
        When screen changes, update state of the lifedrain.
        '''
        self._update()
        if self.status['disable']:
            return

        if state != 'review':
            self.toggle_drain(False)

        if self.status['reviewed'] and state in ['overview', 'review']:
            self._deck_manager.recover()

        self.status['reviewed'] = False
        self.status['screen'] = state

        if state == 'deckBrowser':
            self._deck_manager.bar_visible(False)
        elif self._mw.col is not None:
            self._deck_manager.set_deck(self._mw.col.decks.current()['id'])
            self._deck_manager.bar_visible(True)

    def show_question(self):
        '''
        Called when a question is shown.
        '''
        if self.status['disable']:
            return

        self.toggle_drain(True)
        if self.status['reviewed']:
            if self.status['review_response'] == 1:
                self.recover(damage=True)
            else:
                self.recover()
        self.status['reviewed'] = False
        self.status['card_new_state'] = False

    def show_answer(self):
        '''
        Called when an answer is shown.
        '''
        if self.status['disable']:
            return

        self.toggle_drain(not self.status['stop_on_answer'])
        self.status['reviewed'] = True

    def undo(self):
        '''
        Deals with undoing.
        '''
        if self.status['disable']:
            return

        if self.status['screen'] == 'review' and not self.status['card_new_state']:
            self.status['reviewed'] = False
            self.recover(False)
        self.status['card_new_state'] = False

    def _update(self):
        if self._mw.col is None:
            return

        conf = self._mw.col.conf
        self._deck_manager.set_progress_bar_style({
            'position': conf.get('barPosition', DEFAULTS['barPosition']),
            'progressBarStyle': {
                'height': conf.get('barHeight', DEFAULTS['barHeight']),
                'backgroundColor': conf.get('barBgColor', DEFAULTS['barBgColor']),
                'foregroundColor': conf.get('barFgColor', DEFAULTS['barFgColor']),
                'borderRadius': conf.get('barBorderRadius', DEFAULTS['barBorderRadius']),
                'text': conf.get('barText', DEFAULTS['barText']),
                'textColor': conf.get('barTextColor', DEFAULTS['barTextColor']),
                'customStyle': conf.get('barStyle', DEFAULTS['barStyle'])
            }
        })
        self.status['disable'] = conf.get('disable', DEFAULTS['disable'])
        self.status['stop_on_answer'] = conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])
