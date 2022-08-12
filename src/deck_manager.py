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
        deck_id = self._get_deck_id()
        self._cur_deck_id = deck_id

        if deck_id not in self._bar_info:
            self._add_deck(deck_id)

        self._update_progress_bar_style()

        bar_info = self._bar_info[deck_id]
        self._progress_bar.set_max_value(bar_info['maxValue'])
        self._progress_bar.set_current_value(bar_info['currentValue'])
        history = bar_info['history']
        history[bar_info['currentReview']] = bar_info['currentValue']

    def get_current_life(self):
        """Get the current deck's current life."""
        deck_id = self._get_deck_id()
        self._cur_deck_id = deck_id
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)
        return self._bar_info[deck_id]['currentValue']

    def set_deck_conf(self, conf, update_life=True):
        """Updates a deck's current settings and state.

        Args:
            conf: A dictionary with the deck's configuration and state.
        """
        current_value = conf.get('currentValue', conf['maxLife'])
        if current_value > conf['maxLife']:
            current_value = conf['maxLife']
        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])

        deck_id = conf['id']
        self._bar_info[deck_id]['maxValue'] = conf['maxLife']
        self._bar_info[deck_id]['recoverValue'] = conf['recover']
        self._bar_info[deck_id]['damageValue'] = conf['damage']
        self._bar_info[deck_id]['damageNew'] = conf['damageNew']
        self._bar_info[deck_id]['damageLearning'] = conf['damageLearning']
        if update_life:
            self._bar_info[deck_id]['currentValue'] = current_value

    def recover_life(self, increment=True, value=None, damage=False,
                     card_type=None):
        """Recover life of the currently active deck.

        Args:
            increment: Optional. A flag that indicates increment or decrement.
            value: Optional. The value used to increment or decrement.
            damage: Optional. If this flag is ON, uses the default damage value.
        """
        bar_info = self._bar_info[self._cur_deck_id]

        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and bar_info['damageValue'] is not None:
                multiplier = -1
                value = self._calculate_damage(card_type)
            else:
                value = bar_info['recoverValue']

        self._progress_bar.inc_current_value(multiplier * value)

        life = self._progress_bar.get_current_value()
        bar_info['currentValue'] = life
        if life > 0:
            self._game_over = False
        elif not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')

    def answer(self, review_response, card_type):
        """Restores or drains life after an answer."""
        if review_response == 1:
            self.recover_life(damage=True, card_type=card_type)
        else:
            self.recover_life()
        self._next()

    def action(self, behavior_index):
        """Bury/suspend handling."""
        if behavior_index == 0:
            self.recover_life(False)
        elif behavior_index == 2:
            self.recover_life(True)
        self._next()

    def undo(self):
        """Restore the life to how it was in the previous card."""
        bar_info = self._bar_info[self._cur_deck_id]
        history = bar_info['history']
        if bar_info['currentReview'] == 0:
            return
        bar_info['currentReview'] -= 1
        bar_info['currentValue'] = history[bar_info['currentReview']]
        self._progress_bar.set_current_value(bar_info['currentValue'])

    def _next(self):
        """Remembers the current life and advances to the next card."""
        bar_info = self._bar_info[self._cur_deck_id]
        bar_info['currentReview'] += 1
        history = bar_info['history']
        if len(history) == bar_info['currentReview']:
            history.append(bar_info['currentValue'])
        else:
            history[bar_info['currentReview']] = bar_info['currentValue']

    def _get_deck_id(self):
        global_conf = self._global_conf.get()
        if global_conf['shareDrain']:
            return 'shared'
        conf = self._deck_conf.get()
        return conf['id']

    def _calculate_damage(self, card_type):
        """Calculate damage depending on card type.

        Args:
            card_type: 0 = New, 1 = Learning, 2 = Review.
        """
        bar_info = self._bar_info[self._cur_deck_id]
        damage = bar_info['damageValue']
        if card_type == 0 and bar_info['damageNew'] is not None:
            damage = bar_info['damageNew']
        elif card_type == 1 and bar_info['damageLearning'] is not None:
            damage = bar_info['damageLearning']
        return damage

    def _add_deck(self, deck_id):
        """Adds a deck to the list of decks that are being managed.

        Args:
            deck_id: The ID of the deck.
        """
        conf = self._global_conf.get()
        if not conf['shareDrain']:
            conf = self._deck_conf.get()
        self._bar_info[deck_id] = {
            'maxValue': conf['maxLife'],
            'currentValue': conf['maxLife'],
            'recoverValue': conf['recover'],
            'damageValue': conf['damage'],
            'damageNew': conf['damageNew'],
            'damageLearning': conf['damageLearning'],
            'history': [conf['maxLife']],
            'currentReview': 0,
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
