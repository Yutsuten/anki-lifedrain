"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from anki.hooks import runHook

from .defaults import DEFAULTS
from .progress_bar import ProgressBar


class DeckManager(object):
    """Manages Life Drain status and configuration for each deck.

    Users may configure each deck with different settings, and the current
    status of the life bar (e.g. current life) will likely differ for each deck.

    Attributes:
        bar_visible: Function that toggles the Progress Bar visibility.
    """

    bar_visible = None

    _bar_info = {}
    _conf = None
    _deck_conf = None
    _game_over = False
    _main_window = None
    _progress_bar = None
    _cur_deck_id = None

    def __init__(self, mw, qt, deck_conf):
        """Initializes a Progress Bar, and keeps Anki's main window reference.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._progress_bar = ProgressBar(mw, qt)
        self._main_window = mw
        self._deck_conf = deck_conf
        self.bar_visible = self._progress_bar.set_visible

    def set_deck(self, deck_id):
        """Sets a deck as the currently active.

        Args:
            deck_id: The ID of the deck.
        """
        self._update_progress_bar_style()
        self._cur_deck_id = deck_id

        if deck_id not in self._bar_info:
            self._add_deck(deck_id)

        self._progress_bar.set_max_value(self._bar_info[deck_id]['maxValue'])
        self._progress_bar.set_current_value(
            self._bar_info[deck_id]['currentValue'])

    def get_deck_conf(self, deck_id):
        """Get the settings and state of a deck.

        Args:
            deck_id: The ID of the deck.
        """
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)
        return self._bar_info[deck_id]

    def set_deck_conf(self, conf):
        """Updates a deck's current settings and state.

        Args:
            deck_id: The ID of the deck.
            conf: A dictionary with the deck's configuration and state.
        """
        current_value = conf['currentValue']
        if current_value > conf['maxLife']:
            current_value = conf['maxLife']

        deck_id = conf['id']
        self._bar_info[deck_id]['maxValue'] = conf['maxLife']
        self._bar_info[deck_id]['recoverValue'] = conf['recover']
        self._bar_info[deck_id]['damageValue'] = conf['damage']
        self._bar_info[deck_id]['currentValue'] = current_value

    def recover_life(self, increment=True, value=None, damage=False):
        """Recover life of the currently active deck.

        Args:
            increment: Optional. A flag that indicates increment or decrement.
            value: Optional. The value used to increment or decrement.
            damage: Optional. If this flag is ON, uses the default damage value.
        """
        deck_id = self._cur_deck_id

        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and self._bar_info[deck_id]['damageValue'] is not None:
                multiplier = -1
                value = self._bar_info[deck_id]['damageValue']
            else:
                value = self._bar_info[deck_id]['recoverValue']

        self._progress_bar.inc_current_value(multiplier * value)

        life = self._progress_bar.get_current_value()
        self._bar_info[deck_id]['currentValue'] = life
        if life > 0:
            self._game_over = False
        elif not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')

    def _add_deck(self, deck_id):
        """Adds a deck to the list of decks that are being managed.

        Args:
            deck_id: The ID of the deck.
        """
        conf = self._deck_conf.get()
        self._bar_info[deck_id] = {
            'maxValue': conf['maxLife'],
            'currentValue': conf['maxLife'],
            'recoverValue': conf['recover'],
            'damageValue': conf['damage']
        }

    def _update_progress_bar_style(self):
        """Synchronizes the Progress Bar styling with the Global Settings."""
        self._conf = self._main_window.col.conf
        self._progress_bar.dock_at(self._get_conf('barPosition'))
        progress_bar_style = {
            'height': self._get_conf('barHeight'),
            'foregroundColor': self._get_conf('barFgColor'),
            'borderRadius': self._get_conf('barBorderRadius'),
            'text': self._get_conf('barText'),
            'textColor': self._get_conf('barTextColor'),
            'customStyle': self._get_conf('barStyle')
        }
        self._progress_bar.set_style(progress_bar_style)

    def _get_conf(self, key):
        """Gets the value of a configuration."""
        return self._conf.get(key, DEFAULTS[key])
