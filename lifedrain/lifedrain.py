'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from anki.hooks import wrap
from aqt import mw, forms
from aqt.deckconf import DeckConf
from aqt.dyndeckconf import DeckConf as FiltDeckConf
from aqt.preferences import Preferences

from .settings_ui import (
    preferences, preferences_load, deck_settings,
    custom_deck_settings
)
from .deck import Deck
from .defaults import DEFAULTS
from .progress_bar import ProgressBar


def get_lifedrain():
    '''
    Gets the state of the life drain.
    '''
    if mw.col is not None:
        # Create deck_bar_manager, should run only once
        if LIFEDRAIN.deck_bar_manager is None:
            config = {
                'position': mw.col.conf.get('barPosition', DEFAULTS['barPosition']),
                'progressBarStyle': {
                    'height': mw.col.conf.get('barHeight', DEFAULTS['barHeight']),
                    'backgroundColor': mw.col.conf.get(
                        'barBgColor', DEFAULTS['barBgColor']),
                    'foregroundColor': mw.col.conf.get(
                        'barFgColor', DEFAULTS['barFgColor']),
                    'borderRadius': mw.col.conf.get(
                        'barBorderRadius', DEFAULTS['barBorderRadius']),
                    'text': mw.col.conf.get('barText', DEFAULTS['barText']),
                    'textColor': mw.col.conf.get('barTextColor', DEFAULTS['barTextColor']),
                    'customStyle': mw.col.conf.get('barStyle', DEFAULTS['barStyle'])
                }
            }
            progress_bar = ProgressBar(config, DEFAULTS['maxLife'])
            progress_bar.hide()
            LIFEDRAIN.deck_bar_manager = Deck(progress_bar)
            LIFEDRAIN.disable = mw.col.conf.get('disable', DEFAULTS['disable'])
            LIFEDRAIN.stop_on_answer = mw.col.conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

        # Keep deck list always updated
        for deck_id in mw.col.decks.allIds():
            LIFEDRAIN.deck_bar_manager.add_deck(deck_id, mw.col.decks.confForDid(deck_id))

    return LIFEDRAIN


class LifeDrain(object):  # pylint: disable=useless-object-inheritance
    '''
    Contains the state of the life drain.
    '''
    config = {}
    deck_bar_manager = None
    timer = None
    status = {
        'reviewed': False,
        'newCardState': False,
        'screen': None,
        'reviewResponse': 0
    }
    stop_on_answer = False
    disable = None

    def __init__(self):
        # Separator strip
        mw.setStyleSheet('QMainWindow::separator { width: 0px; height: 0px; }')
        try:
            import Night_Mode
            Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
        except Exception:  # nosec  # pylint: disable=broad-except
            pass

        # Preferences
        forms.preferences.Ui_Preferences.setupUi = wrap(
            forms.preferences.Ui_Preferences.setupUi, preferences
        )
        Preferences.__init__ = wrap(Preferences.__init__, preferences_load)
        Preferences.accept = wrap(
            Preferences.accept, lambda *args: self.preferences_save(args[0]), 'before'
        )

        # Deck configuration
        forms.dconf.Ui_Dialog.setupUi = wrap(
            forms.dconf.Ui_Dialog.setupUi, deck_settings
        )
        DeckConf.loadConf = wrap(
            DeckConf.loadConf, lambda *args: self.deck_settings_load(args[0])
        )
        DeckConf.saveConf = wrap(
            DeckConf.saveConf, lambda *args: self.deck_settings_save(args[0]), 'before'
        )

        # Custom deck configuration
        forms.dyndconf.Ui_Dialog.setupUi = wrap(
            forms.dyndconf.Ui_Dialog.setupUi, custom_deck_settings
        )
        FiltDeckConf.loadConf = wrap(
            FiltDeckConf.loadConf, lambda *args: self.deck_settings_load(args[0])
        )
        FiltDeckConf.saveConf = wrap(
            FiltDeckConf.saveConf, lambda *args: self.deck_settings_save(args[0]), 'before'
        )

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
        self.deck_bar_manager.set_anki_progress_bar_style(config)
        self.disable = conf.get('disable', DEFAULTS['disable'])
        self.stop_on_answer = conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

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
            self.deck_bar_manager.get_deck_conf(settings.deck['id'])['currentValue']
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
        self.deck_bar_manager.set_deck_conf(settings.deck['id'], settings.conf)

    def visible(self, flag):
        pass

    def toggle_visible(self):
        pass

    def drain(self, flag):
        pass

    def toggle_drain(self):
        '''
        Toggle the timer to pause/unpause the drain.
        '''
        if not self.disable and self.timer is not None:
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start()

    def recover(self, *args, **kwargs):
        '''
        When a decisecond (0.1s) passes, this function is triggered.
        '''
        self.deck_bar_manager.recover(*args, **kwargs)

    def update_status(self, **kwargs):
        self.status.update(kwargs)
