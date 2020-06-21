"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from anki.hooks import runHook

from .progress_bar import ProgressBar


class DeckManager:
    """Manages Life Drain status and configuration for each deck.

    Users may configure each deck with different settings, and the current
    status of the life bar (e.g. current life) will likely differ for each deck.

    Attributes:
        bar_visible: Function that toggles the Progress Bar visibility.
    """

    bar_visible = None

    _bar_info = {}
    _conf = None
    _global_conf = None
    _deck_conf = None
    _game_over = False
    _progress_bar = None
    _cur_deck_id = None

    def __init__(self, mw, qt, global_conf, deck_conf):
        """Initializes a Progress Bar, and keeps Anki's main window reference.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._progress_bar = ProgressBar(mw, qt)
        self._global_conf = global_conf
        self._deck_conf = deck_conf
        self.bar_visible = self._progress_bar.set_visible

    def update(self):
        """Updates the current deck's life bar."""
        conf = self._deck_conf.get()
        self._cur_deck_id = conf['id']

        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])

        self._update_progress_bar_style()

        bar_info = self._bar_info[conf['id']]
        self._progress_bar.set_max_value(bar_info['maxValue'])
        self._progress_bar.set_current_value(bar_info['currentValue'])

    def get_current_life(self):
        """Get the current deck's current life."""
        conf = self._deck_conf.get()
        self._cur_deck_id = conf['id']
        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])
        return self._bar_info[conf['id']]['currentValue']

    def set_deck_conf(self, conf):
        """Updates a deck's current settings and state.

        Args:
            deck_id: The ID of the deck.
            conf: A dictionary with the deck's configuration and state.
        """
        current_value = conf['currentValue']
        if current_value > conf['maxLife']:
            current_value = conf['maxLife']
        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])

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
        conf = self._global_conf.get()
        self._progress_bar.dock_at(conf['barPosition'])
        progress_bar_style = {
            'height': conf['barHeight'],
            'fgColor': conf['barFgColor'],
            'borderRadius': conf['barBorderRadius'],
            'text': conf['barText'],
            'textColor': conf['barTextColor'],
            'customStyle': conf['barStyle']}
        if conf['enableBgColor']:
            progress_bar_style['bgColor'] = conf['barBgColor']
        self._progress_bar.set_style(progress_bar_style)
