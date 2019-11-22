'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .deck import Deck
from .defaults import DEFAULTS
from .progress_bar import ProgressBar


class LifeDrain(object):
    '''
    Contains the state of the life drain.
    '''
    status = {
        'reviewed': False,
        'newCardState': False,
        'screen': None,
        'reviewResponse': 0
    }

    _deck = None
    _disable = None
    _mw = None
    _stop_on_answer = False
    _timer = None

    def __init__(self, make_timer, mw):
        self._timer = make_timer(100, lambda: self.recover(False, 0.1), True)
        self._mw = mw

        # Configure separator strip
        mw.setStyleSheet('QMainWindow::separator { width: 0px; height: 0px; }')
        try:
            import Night_Mode
            Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
        except Exception:  # nosec  # pylint: disable=broad-except
            pass

    def preferences_save(self, settings):
        '''
        Saves LifeDrain global configurations.
        '''
        conf = settings.mw.col.conf
        conf['barPosition'] = settings.form.positionList.currentIndex()
        conf['barHeight'] = settings.form.heightInput.value()
        conf['barBgColor'] = settings.form.bgColorDialog.currentColor().name()
        conf['barFgColor'] = settings.form.fgColorDialog.currentColor().name()
        conf['barBorderRadius'] = settings.form.borderRadiusInput.value()
        conf['barText'] = settings.form.textList.currentIndex()
        conf['barTextColor'] = settings.form.textColorDialog.currentColor().name()
        conf['barStyle'] = settings.form.styleList.currentIndex()
        conf['stopOnAnswer'] = settings.form.stopOnAnswer.isChecked()
        conf['disable'] = settings.form.disableAddon.isChecked()

        # Create new instance of the bar with new configurations
        config = {
            'position': conf.get('barPosition', DEFAULTS['barPosition']),
            'progressBarStyle': {
                'height': conf.get('barHeight', DEFAULTS['barHeight']),
                'backgroundColor': conf.get('barBgColor', DEFAULTS['barBgColor']),
                'foregroundColor': conf.get('barFgColor', DEFAULTS['barFgColor']),
                'borderRadius': conf.get(
                    'barBorderRadius', DEFAULTS['barBorderRadius']),
                'text': conf.get('barText', DEFAULTS['barText']),
                'textColor': conf.get('barTextColor', DEFAULTS['barTextColor']),
                'customStyle': conf.get('barStyle', DEFAULTS['barStyle'])
            }
        }
        self._deck.set_anki_progress_bar_style(config)
        self._disable = conf.get('disable', DEFAULTS['disable'])
        self._stop_on_answer = conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

    def deck_settings_load(self, settings):
        '''
        Loads LifeDrain deck configurations.
        '''
        settings.conf = settings.mw.col.decks.confForDid(settings.deck['id'])
        settings.form.maxLifeInput.setValue(
            settings.conf.get('maxLife', DEFAULTS['maxLife'])
        )
        settings.form.recoverInput.setValue(
            settings.conf.get('recover', DEFAULTS['recover'])
        )
        settings.form.enableDamageInput.setChecked(
            settings.conf.get('enableDamage', DEFAULTS['enableDamage'])
        )
        settings.form.damageInput.setValue(
            settings.conf.get('damage', DEFAULTS['damage'])
        )
        settings.form.currentValueInput.setValue(
            self._deck.get_deck_conf(settings.deck['id'])['currentValue']
        )

    def deck_settings_save(self, settings):
        '''
        Saves LifeDrain deck configurations.
        '''
        settings.conf['maxLife'] = settings.form.maxLifeInput.value()
        settings.conf['recover'] = settings.form.recoverInput.value()
        settings.conf['currentValue'] = settings.form.currentValueInput.value()
        settings.conf['enableDamage'] = settings.form.enableDamageInput.isChecked()
        settings.conf['damage'] = settings.form.damageInput.value()
        self._deck.set_deck_conf(settings.deck['id'], settings.conf)

    def toggle_drain(self, enable=None):
        '''
        Toggle the timer to pause/unpause the drain.
        '''
        if not self._disable:
            if self._timer.isActive() and enable is not True:
                self._timer.stop()
            elif not self._timer.isActive() and enable is not False:
                self._timer.start()

    def recover(self, *args, **kwargs):
        '''
        Recover life.
        '''
        self._deck.recover(*args, **kwargs)

    def screen_change(self, state):
        '''
        When screen changes, update state of the lifedrain.
        '''
        self._update()

        if not self._disable:
            self._timer.stop()

            if self.status['reviewed'] and state in ['overview', 'review']:
                self._deck.recover()
            self.status['reviewed'] = False
            self.status['screen'] = state

            if state == 'deckBrowser':
                self._deck.bar_visible(False)
                self._deck.set_deck(None)
            else:
                if self._mw.col is not None:
                    self._deck.set_deck(self._mw.col.decks.current()['id'])
                self._deck.bar_visible(True)

            if state == 'review':
                self._timer.start()

        else:
            self._deck.bar_visible(False)
            self._timer.stop()

    def show_question(self):
        '''
        Called when a question is shown.
        '''
        if not self._disable:
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
        if not self._disable:
            if self._stop_on_answer:
                self.toggle_drain(False)
            else:
                self.toggle_drain(True)
            self.status['reviewed'] = True

    def undo(self):
        '''
        Deals with undoing.
        '''
        if not self._disable:
            if self.status['screen'] == 'review' and not self.status['newCardState']:
                self.status['reviewed'] = False
                self.recover(False)
            self.status['newCardState'] = False

    def _update(self):
        if self._mw.col is None:
            return

        # Create deck manager, should run only once
        if self._deck is None:
            config = {
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
            }
            progress_bar = ProgressBar(config, DEFAULTS['maxLife'])
            progress_bar.hide()
            self._deck = Deck(progress_bar)
            self._disable = self._mw.col.conf.get('disable', DEFAULTS['disable'])
            self._stop_on_answer = self._mw.col.conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

        # Keep deck list always updated
        for deck_id in self._mw.col.decks.allIds():
            self._deck.add_deck(deck_id, self._mw.col.decks.confForDid(deck_id))
