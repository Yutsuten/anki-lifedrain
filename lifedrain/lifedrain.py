'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .deck_manager import DeckManager
from .defaults import DEFAULTS
from .progress_bar import ProgressBar
from .settings import Settings


class Lifedrain(object):
    '''
    Contains the state and functions of the life drain.
    '''
    status = {
        'reviewed': False,
        'newCardState': False,
        'screen': None,
        'reviewResponse': 0
    }

    _deck_manager = None
    _disable = None
    _mw = None
    _qt = None
    _settings = None
    _stop_on_answer = False
    _timer = None

    def __init__(self, make_timer, mw, qt):
        self._timer = make_timer(100, lambda: self.recover(False, 0.1), True)
        self._settings = Settings(qt)
        self._deck_manager = DeckManager(qt, mw)
        self._mw = mw
        self._qt = qt

        # Configure separator strip
        mw.setStyleSheet('QMainWindow::separator { width: 0px; height: 0px; }')
        try:
            import Night_Mode
            Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
        except Exception:  # nosec  # pylint: disable=broad-except
            pass

    def preferences_ui(self, form):
        '''
        Loads the User Interface for the Life Drain tab in the preferences.
        '''
        self._settings.preferences_ui(form)

    def deck_settings_ui(self, form):
        '''
        Loads the User Interface for the Life Drain tab in the Deck Settings (options).
        '''
        self._settings.deck_settings_ui(form)

    def custom_deck_settings_ui(self, form, is_anki21):
        '''
        Lods the User Interface for the Life Drain form in the Custom Deck Settings
        (aka Filtered Deck Settings)
        '''
        self._settings.custom_deck_settings_ui(form, is_anki21)

    def preferences_load(self, pref):
        '''
        Loads Life Drain global configurations into the Preferences UI.
        '''
        self._settings.preferences_load(pref)

    def preferences_save(self, pref):
        '''
        Saves Life Drain global configurations.
        '''
        conf = self._settings.preferences_save(pref)

        self._deck_manager.set_progress_bar_style({
            'position': conf['barPosition'],
            'progressBarStyle': {
                'height': conf['barHeight'],
                'backgroundColor': conf['barBgColor'],
                'foregroundColor': conf['barFgColor'],
                'borderRadius': conf['barBorderRadius'],
                'text': conf['barText'],
                'textColor': conf['barTextColor'],
                'customStyle': conf['barStyle']
            }
        })
        self._disable = conf['disable']
        self._stop_on_answer = conf['stopOnAnswer']

    def deck_settings_load(self, settings):
        '''
        Loads LifeDrain deck configurations into the Settings UI.
        '''
        self._settings.deck_settings_load(
            settings,
            self._deck_manager.get_deck_conf(settings.deck['id'])['currentValue']
        )

    def deck_settings_save(self, settings):
        '''
        Saves LifeDrain deck configurations.
        '''
        deck_conf = self._settings.deck_settings_save(settings)
        self._deck_manager.set_deck_conf(settings.deck['id'], deck_conf)

    def toggle_drain(self, enable=None):
        '''
        Toggle the timer to pause/unpause the drain.
        '''
        if self._disable:
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
        self._timer.stop()

        if self._disable:
            self._deck_manager.bar_visible(False)
        else:
            self.status['reviewed'] = False
            self.status['screen'] = state

            if self.status['reviewed'] and state in ['overview', 'review']:
                self._deck_manager.recover()

            if state == 'deckBrowser':
                self._deck_manager.bar_visible(False)
                self._deck_manager.set_deck(None)
            else:
                if self._mw.col is not None:
                    self._deck_manager.set_deck(self._mw.col.decks.current()['id'])
                self._deck_manager.bar_visible(True)

            if state == 'review':
                self._timer.start()

    def show_question(self):
        '''
        Called when a question is shown.
        '''
        if self._disable:
            return

        self.toggle_drain(True)
        if self.status['reviewed']:
            if self.status['reviewResponse'] == 1:
                self.recover(damage=True)
            else:
                self.recover()
        self.status['reviewed'] = False
        self.status['newCardState'] = False

    def show_answer(self):
        '''
        Called when an answer is shown.
        '''
        if self._disable:
            return

        if self._stop_on_answer:
            self.toggle_drain(False)
        else:
            self.toggle_drain(True)
        self.status['reviewed'] = True

    def undo(self):
        '''
        Deals with undoing.
        '''
        if self._disable:
            return

        if self.status['screen'] == 'review' and not self.status['newCardState']:
            self.status['reviewed'] = False
            self.recover(False)
        self.status['newCardState'] = False

    def _update(self):
        if self._mw.col is None:
            return

        self._deck_manager.set_progress_bar_style({
            'position': self._mw.col.conf.get('barPosition', DEFAULTS['barPosition']),
            'progressBarStyle': {
                'height': self._mw.col.conf.get('barHeight', DEFAULTS['barHeight']),
                'backgroundColor': self._mw.col.conf.get(
                    'barBgColor', DEFAULTS['barBgColor']),
                'foregroundColor': self._mw.col.conf.get(
                    'barFgColor', DEFAULTS['barFgColor']),
                'borderRadius': self._mw.col.conf.get(
                    'barBorderRadius', DEFAULTS['barBorderRadius']),
                'text': self._mw.col.conf.get('barText', DEFAULTS['barText']),
                'textColor': self._mw.col.conf.get('barTextColor', DEFAULTS['barTextColor']),
                'customStyle': self._mw.col.conf.get('barStyle', DEFAULTS['barStyle'])
            }
        })
        self._disable = self._mw.col.conf.get('disable', DEFAULTS['disable'])
        self._stop_on_answer = self._mw.col.conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

        # Keep deck list always updated
        for deck_id in self._mw.col.decks.allIds():
            self._deck_manager.add_deck(deck_id, self._mw.col.decks.confForDid(deck_id))
