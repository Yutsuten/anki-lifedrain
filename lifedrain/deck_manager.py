'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from anki.hooks import runHook

from .defaults import DEFAULTS
from .progress_bar import ProgressBar


class DeckManager(object):
    '''
    Manages different Life Drain configuration for each deck.
    '''
    _bar_info = {}
    _game_over = False
    _main_window = None
    _progress_bar = None

    def __init__(self, qt, mw):
        self._progress_bar = ProgressBar(qt, mw)
        self._main_window = mw

    def set_deck(self, deck_id):
        '''
        Sets the current deck.
        '''
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)

        self._progress_bar.set_max_value(
            self._bar_info[deck_id]['maxValue']
        )
        self._progress_bar.set_current_value(
            self._bar_info[deck_id]['currentValue']
        )

    def get_deck_conf(self, deck_id):
        '''
        Get the settings and state of a deck.
        '''
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)

        return self._bar_info[deck_id]

    def set_deck_conf(self, deck_id, conf):
        '''
        Updates deck's current state.
        '''
        current_value = conf['currentValue']
        if current_value > conf['maxLife']:
            current_value = conf['maxLife']

        self._bar_info[deck_id]['maxValue'] = conf['maxLife']
        self._bar_info[deck_id]['recoverValue'] = conf['recover']
        self._bar_info[deck_id]['enableDamageValue'] = conf['enableDamage']
        self._bar_info[deck_id]['damageValue'] = conf['damage']
        self._bar_info[deck_id]['currentValue'] = current_value

    def set_progress_bar_style(self, config):
        '''
        Updates the AnkiProgressBar instance.
        '''
        self._progress_bar.dock_at(config['position'])
        self._progress_bar.set_style(config['progressBarStyle'])

    def recover_life(self, increment=True, value=None, damage=False):
        '''
        Recover life of the currently active deck.
        '''
        deck_id = self._main_window.col.decks.current()['id']

        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and self._bar_info[deck_id]['enableDamageValue']:
                multiplier = -1
                value = self._bar_info[deck_id]['damageValue']
            else:
                value = self._bar_info[deck_id]['recoverValue']

        self._progress_bar.inc_current_value(multiplier * value)

        life = self._progress_bar.get_current_value()
        self._bar_info[deck_id]['currentValue'] = life
        if life == 0 and not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')
        elif life > 0:
            self._game_over = False

    def bar_visible(self, visible):
        '''
        Sets the visibility of the Progress Bar
        '''
        if visible:
            self._progress_bar.show()
        else:
            self._progress_bar.hide()

    def _add_deck(self, deck_id):
        '''
        Adds a deck to the manager.
        '''
        conf = self._main_window.col.decks.confForDid(deck_id)
        self._bar_info[deck_id] = {
            'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
            'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
            'recoverValue': conf.get('recover', DEFAULTS['recover']),
            'enableDamageValue': conf.get('enableDamage', DEFAULTS['enableDamage']),
            'damageValue': conf.get('damage', DEFAULTS['damage'])
        }
