"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from anki.hooks import runHook

from .defaults import DEFAULTS
from .progress_bar import ProgressBar


class DeckManager(object):
    """Manages Life Drain status and configuration for each deck.

    Users may configure each deck with different settings, and the current status of
    the life bar (e.g. current life) will likely differ for each deck.

    Attributes:
        bar_visible: Function that toggles the Progress Bar visibility.
    """

    bar_visible = None

    _bar_info = {}
    _game_over = False
    _main_window = None
    _progress_bar = None

    def __init__(self, mw, qt):
        """Initializes a Progress Bar, and keeps Anki's main window reference.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._progress_bar = ProgressBar(mw, qt)
        self._main_window = mw
        self.bar_visible = self._progress_bar.set_visible

    def set_deck(self, deck_id):
        """Sets a deck as the currently active.

        Args:
            deck_id: The ID of the deck.
        """
        self._update_progress_bar_style()
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)

        self._progress_bar.set_max_value(self._bar_info[deck_id]['maxValue'])
        self._progress_bar.set_current_value(self._bar_info[deck_id]['currentValue'])

    def get_deck_conf(self, deck_id):
        """Get the settings and state of a deck.

        Args:
            deck_id: The ID of the deck.
        """
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)
        return self._bar_info[deck_id]

    def set_deck_conf(self, deck_id, conf):
        """Updates a deck's current settings and state.

        Args:
            deck_id: The ID of the deck.
            conf: A dictionary with the deck's configuration and state.
        """
        current_value = conf['currentValue']
        if current_value > conf['maxLife']:
            current_value = conf['maxLife']

        self._bar_info[deck_id]['maxValue'] = conf['maxLife']
        self._bar_info[deck_id]['recoverValue'] = conf['recover']
        self._bar_info[deck_id]['enableDamageValue'] = conf['enableDamage']
        self._bar_info[deck_id]['damageValue'] = conf['damage']
        self._bar_info[deck_id]['currentValue'] = current_value

    def recover_life(self, increment=True, value=None, damage=False):
        """Recover life of the currently active deck.

        Args:
            increment: Optional. A flag that indicates if life will be increased or decreased.
            value: Optional. The value used to increment or decrement.
            damage: Optional. If this flag is ON, uses the default damage value to remove life.
        """
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
        conf = self._main_window.col.decks.confForDid(deck_id)
        self._bar_info[deck_id] = {
            'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
            'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
            'recoverValue': conf.get('recover', DEFAULTS['recover']),
            'enableDamageValue': conf.get('enableDamage', DEFAULTS['enableDamage']),
            'damageValue': conf.get('damage', DEFAULTS['damage'])
        }

    def _update_progress_bar_style(self):
        """Synchronizes the Progress Bar styling with the Global Settings."""
        conf = self._main_window.col.conf
        self._progress_bar.dock_at(conf.get('barPosition', DEFAULTS['barPosition']))
        self._progress_bar.set_style({
            'height': conf.get('barHeight', DEFAULTS['barHeight']),
            'backgroundColor': conf.get('barBgColor', DEFAULTS['barBgColor']),
            'foregroundColor': conf.get('barFgColor', DEFAULTS['barFgColor']),
            'borderRadius': conf.get('barBorderRadius', DEFAULTS['barBorderRadius']),
            'text': conf.get('barText', DEFAULTS['barText']),
            'textColor': conf.get('barTextColor', DEFAULTS['barTextColor']),
            'customStyle': conf.get('barStyle', DEFAULTS['barStyle'])
        })
