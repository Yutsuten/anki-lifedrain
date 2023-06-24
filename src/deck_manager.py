# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from typing import Any, Literal, Optional, Union

from anki.consts import CardType
from anki.hooks import runHook
from aqt.main import AnkiQt

from .database import DeckConf, GlobalConf
from .defaults import BEHAVIORS
from .progress_bar import ProgressBar


class DeckManager:
    """Manages Life Drain status and configuration for each deck.

    Users may configure each deck with different settings, and the current
    status of the life bar (e.g. current life) will likely differ for each deck.
    """

    _bar_info = {}
    _game_over = False
    _cur_deck_id = None

    def __init__(self, mw: AnkiQt, qt: Any, global_conf: GlobalConf, deck_conf: DeckConf):
        """Initializes a Progress Bar, and keeps Anki's main window reference.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
            global_conf: An instance of GlobalConf.
            deck_conf: An instance of DeckConf.
        """
        self._progress_bar = ProgressBar(mw, qt)
        self._global_conf = global_conf
        self._deck_conf = deck_conf
        self.bar_visible = self._progress_bar.set_visible

    def update(self) -> None:
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

    def get_current_life(self) -> Union[int, float]:
        """Get the current deck's current life."""
        deck_id = self._get_deck_id()
        self._cur_deck_id = deck_id
        if deck_id not in self._bar_info:
            self._add_deck(deck_id)
        return self._bar_info[deck_id]['currentValue']

    def set_deck_conf(self, conf: dict, *, update_life: bool) -> None:
        """Updates a deck's current settings and state.

        Args:
            conf: A dictionary with the deck's configuration and state.
            update_life: Update the current life?
        """
        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])

        deck_id = conf['id']
        self._bar_info[deck_id]['maxValue'] = conf['maxLife']
        self._bar_info[deck_id]['recoverValue'] = conf['recover']
        self._bar_info[deck_id]['damageValue'] = conf['damage']
        self._bar_info[deck_id]['damageNew'] = conf['damageNew']
        self._bar_info[deck_id]['damageLearning'] = conf['damageLearning']

        if update_life:
            current_value = conf.get('currentValue', conf['maxLife'])
            if current_value > conf['maxLife']:
                current_value = conf['maxLife']
            self._bar_info[deck_id]['currentValue'] = current_value

    def drain(self) -> None:
        """Life loss due to drain."""
        self._update_life(-0.1)

    def heal(self, value:Optional[Union[int, float]]=None, *, increment:bool=True) -> None:
        """Partially heal life of the currently active deck.

        Args:
            increment: Optional. A flag that indicates increment or decrement.
            value: Optional. The value used to increment or decrement.
        """
        multiplier = 1 if increment else -1
        if value is None:
            value = int(self._bar_info[self._cur_deck_id]['recoverValue'])
        self._update_life(multiplier * value)

    def recover(self) -> None:
        """Resets the life bar of the currently active deck to the initial value."""
        conf = self._global_conf.get()
        start_empty = conf['startEmpty']
        if not conf['shareDrain']:
            conf = self._deck_conf.get()

        life = 0 if start_empty else conf['maxLife']
        self._bar_info[self._cur_deck_id]['currentValue'] = life
        self._progress_bar.set_current_value(life)
        self._game_over = start_empty

    def damage(self, card_type: CardType) -> None:
        """Apply damage.

        Args:
            card_type: Optional. Applies different damage depending on card type.
        """
        bar_info = self._bar_info[self._cur_deck_id]
        damage = bar_info['damageValue']
        if card_type == 0 and bar_info['damageNew'] is not None:
            damage = bar_info['damageNew']
        elif card_type == 1 and bar_info['damageLearning'] is not None:
            damage = bar_info['damageLearning']
        self._update_life(-1 * damage)

    def answer(self, review_response: Literal[1, 2, 3, 4], card_type: CardType) -> None:
        """Restores or drains life after an answer."""
        if review_response == 1 and self._bar_info[self._cur_deck_id]['damageValue'] is not None:
            self.damage(card_type=card_type)
        else:
            self.heal()
        self._next()

    def action(self, behavior_index: Literal[0, 1, 2]) -> None:
        """Bury/suspend handling."""
        if behavior_index == BEHAVIORS.index('Drain life'):
            self.heal(increment=False)
        elif behavior_index == BEHAVIORS.index('Recover life'):
            self.heal(increment=True)
        self._next()

    def undo(self) -> None:
        """Restore the life to how it was in the previous card."""
        bar_info = self._bar_info[self._cur_deck_id]
        history = bar_info['history']
        if bar_info['currentReview'] == 0:
            return
        bar_info['currentReview'] -= 1
        bar_info['currentValue'] = history[bar_info['currentReview']]
        self._progress_bar.set_current_value(bar_info['currentValue'])

    def _update_life(self, difference: Union[int, float]) -> None:
        """Apply recover/damage/drain.

        Args:
            difference: The amount to increase or decrease.
        """
        self._progress_bar.inc_current_value(difference)
        life = self._progress_bar.get_current_value()
        self._bar_info[self._cur_deck_id]['currentValue'] = life
        if life > 0:
            self._game_over = False
        elif not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')

    def _next(self) -> None:
        """Remembers the current life and advances to the next card."""
        bar_info = self._bar_info[self._cur_deck_id]
        bar_info['currentReview'] += 1
        history = bar_info['history']
        if len(history) == bar_info['currentReview']:
            history.append(bar_info['currentValue'])
        else:
            history[bar_info['currentReview']] = bar_info['currentValue']

    def _get_deck_id(self) -> str:
        global_conf = self._global_conf.get()
        if global_conf['shareDrain']:
            return 'shared'
        conf = self._deck_conf.get()
        return conf['id']

    def _add_deck(self, deck_id:str) -> None:
        """Adds a deck to the list of decks that are being managed.

        Args:
            deck_id: The ID of the deck.
        """
        conf = self._global_conf.get()
        start_empty = conf['startEmpty']
        if not conf['shareDrain']:
            conf = self._deck_conf.get()

        self._bar_info[deck_id] = {
            'maxValue': conf['maxLife'],
            'recoverValue': conf['recover'],
            'damageValue': conf['damage'],
            'damageNew': conf['damageNew'],
            'damageLearning': conf['damageLearning'],
            'history': [conf['maxLife']],
            'currentReview': 0,
        }
        self._bar_info[deck_id]['currentValue'] = 0 if start_empty else conf['maxLife']
        self._game_over = start_empty

    def _update_progress_bar_style(self) -> None:
        """Synchronizes the Progress Bar styling with the Global Settings."""
        conf = self._global_conf.get()
        self._progress_bar.dock_at(conf['barPosition'])
        progress_bar_style = {
            'height': conf['barHeight'],
            'fgColor': conf['barFgColor'],
            'thresholdWarn': conf['barThresholdWarn'],
            'fgColorWarn': conf['barFgColorWarn'],
            'thresholdDanger': conf['barThresholdDanger'],
            'fgColorDanger': conf['barFgColorDanger'],
            'borderRadius': conf['barBorderRadius'],
            'text': conf['barText'],
            'textColor': conf['barTextColor'],
            'customStyle': conf['barStyle']}
        if conf['enableBgColor']:
            progress_bar_style['bgColor'] = conf['barBgColor']
        self._progress_bar.set_style(progress_bar_style)
