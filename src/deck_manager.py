# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from anki.hooks import runHook
from aqt.progress import ProgressManager

from .decorators import must_have_active_deck
from .defaults import BEHAVIORS
from .progress_bar import ProgressBar

if TYPE_CHECKING:
    from anki.consts import CardType
    from aqt.main import AnkiQt, MainWindowState

    from .database import DeckConf, GlobalConf


class DeckManager:
    """Manages Life Drain status and configuration for each deck.

    Users may configure each deck with different settings, and the current
    status of the life bar (e.g. current life) will likely differ for each deck.
    """

    def __init__(self, mw: AnkiQt, qt: Any, global_conf: GlobalConf, deck_conf: DeckConf):
        """Initializes a Progress Bar, and keeps Anki's main window reference.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
            global_conf: An instance of GlobalConf.
            deck_conf: An instance of DeckConf.
        """
        self.recovering: bool = False
        self.timer = ProgressManager(mw).timer(100, self.life_timer, repeat=True, parent=mw)
        self.timer.stop()
        self._progress_bar = ProgressBar(mw, qt)
        self._global_conf = global_conf
        self._deck_conf = deck_conf
        self._bar_info: dict[str, dict[str, Any]] = {}
        self._game_over: bool = False
        self._cur_deck_id: Optional[str] = None

    def update(self, state: MainWindowState) -> None:
        """Updates the current deck's life bar."""
        if state == 'deckBrowser':
            self._cur_deck_id = None
            self._progress_bar.set_visible(visible=False)
        else:
            self._cur_deck_id = self._get_cur_deck_id()
            if self._cur_deck_id not in self._bar_info:
                self._add_deck(self._cur_deck_id)
            bar_info = self._bar_info[self._cur_deck_id]
            bar_info['history'][bar_info['currentReview']] = bar_info['currentValue']
            self._update_progress_bar_style()
            self._progress_bar.set_max_value(bar_info['maxValue'])
            self._progress_bar.set_current_value(bar_info['currentValue'])
            self._progress_bar.set_visible(visible=bar_info['enable'])

    def hide_life_bar(self) -> None:
        """Set life bar visibility to False."""
        self._progress_bar.set_visible(visible=False)

    def get_current_life(self) -> Union[int, float]:
        """Get the current deck's current life."""
        self._cur_deck_id = self._get_cur_deck_id()
        if self._cur_deck_id not in self._bar_info:
            self._add_deck(self._cur_deck_id)
        return self._bar_info[self._cur_deck_id]['currentValue']

    def set_deck_conf(self, conf: dict[str, Any], *, update_life: bool) -> None:
        """Updates a deck's current settings and state.

        Args:
            conf: The deck's configuration and state.
            update_life: Update the current life?
        """
        if conf['id'] not in self._bar_info:
            self._add_deck(conf['id'])

        bar_info = self._bar_info[conf['id']]
        bar_info['enable'] = conf['enable']
        bar_info['maxValue'] = conf['maxLife']
        bar_info['recoverValue'] = conf['recover']
        bar_info['fullRecoverSpeed'] = conf['fullRecoverSpeed']
        bar_info['damageValue'] = conf['damage']
        bar_info['damageNew'] = conf['damageNew']
        bar_info['damageLearning'] = conf['damageLearning']

        if update_life:
            current_value = conf.get('currentValue', conf['maxLife'])
            if current_value > conf['maxLife']:
                current_value = conf['maxLife']
            bar_info['currentValue'] = current_value

    @must_have_active_deck
    def life_timer(self, bar_info: dict[str, Any]) -> None:
        """Life loss due to drain, or life gained due to recover."""
        if self.recovering:
            if bar_info['fullRecoverSpeed'] == 0:
                self.recover()
            else:
                self._update_life(bar_info, bar_info['fullRecoverSpeed'] / 10)
        else:
            self._update_life(bar_info, -0.1)  # Drain

        if bar_info['currentValue'] in [0, bar_info['maxValue']]:
            self.timer.stop()

    @must_have_active_deck
    def heal(self, bar_info: dict[str, Any], value:Optional[Union[int, float]]=None, *,
             increment:bool=True) -> None:
        """Partially heal life of the currently active deck.

        Args:
            bar_info: The currently active deck's life bar information.
            value: Optional. The value used to increment or decrement.
            increment: Optional. A flag that indicates increment or decrement.
        """
        multiplier = 1 if increment else -1
        if value is None:
            value = int(bar_info['recoverValue'])
        self._update_life(bar_info, multiplier * value)

    @must_have_active_deck
    def recover(self, bar_info: dict[str, Any]) -> None:
        """Resets the life bar of the currently active deck to the initial value.

        Args:
            bar_info: The currently active deck's life bar information.
        """
        conf = self._global_conf.get()
        start_empty = conf['startEmpty']
        if not conf['shareDrain']:
            conf = self._deck_conf.get()

        life = 0 if start_empty else conf['maxLife']
        bar_info['currentValue'] = life
        self._progress_bar.set_current_value(life)
        self._game_over = start_empty

    @must_have_active_deck
    def damage(self, bar_info: dict[str, Any], card_type: CardType) -> None:
        """Apply damage.

        Args:
            bar_info: The currently active deck's life bar information.
            card_type: Applies different damage depending on card type.
        """
        damage = bar_info['damageValue']
        if card_type == 0:
            damage = bar_info['damageNew']
        elif card_type == 1:
            damage = bar_info['damageLearning']
        self._update_life(bar_info, -1 * damage)

    @must_have_active_deck
    def answer(self, bar_info: dict[str, Any], review_response: Literal[1, 2, 3, 4],
               card_type: CardType) -> None:
        """Restores or drains life after an answer.

        Args:
            bar_info: The currently active deck's life bar information.
            review_response: The response given by the user.
            card_type: The card type of the answered card.
        """
        if review_response == 1 and bar_info['damageValue'] is not None:
            self.damage(card_type=card_type)
        else:
            self.heal()
        self._next(bar_info)

    @must_have_active_deck
    def action(self, bar_info: dict[str, Any], behavior_index: Literal[0, 1, 2]) -> None:
        """Bury/suspend handling."""
        if behavior_index == BEHAVIORS.index('Drain life'):
            self.heal(increment=False)
        elif behavior_index == BEHAVIORS.index('Recover life'):
            self.heal(increment=True)
        self._next(bar_info)

    @must_have_active_deck
    def undo(self, bar_info: dict[str, Any]) -> None:
        """Restore the life to how it was in the previous card.

        Args:
            bar_info: The currently active deck's life bar information.
        """
        history = bar_info['history']
        if bar_info['currentReview'] == 0:
            return
        bar_info['currentReview'] -= 1
        bar_info['currentValue'] = history[bar_info['currentReview']]
        self._progress_bar.set_current_value(bar_info['currentValue'])

    def _update_life(self, bar_info: dict[str, Any], difference: float) -> None:
        """Apply recover/damage/drain.

        Args:
            bar_info: The currently active deck's life bar information.
            difference: The amount to increase or decrease.
        """
        self._progress_bar.inc_current_value(difference)
        life = self._progress_bar.get_current_value()
        bar_info['currentValue'] = life
        if life > 0:
            self._game_over = False
        elif not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')

    def _next(self, bar_info: dict[str, Any]) -> None:
        """Remembers the current life and advances to the next card.

        Args:
            bar_info: The currently active deck's life bar information.
        """
        bar_info['currentReview'] += 1
        history = bar_info['history']
        if len(history) == bar_info['currentReview']:
            history.append(bar_info['currentValue'])
        else:
            history[bar_info['currentReview']] = bar_info['currentValue']

    def _get_cur_deck_id(self) -> str:
        """Gets the currently selected deck id."""
        return 'shared' if self._global_conf.get()['shareDrain'] else self._deck_conf.get()['id']

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
            'enable': conf['enable'],
            'maxValue': conf['maxLife'],
            'recoverValue': conf['recover'],
            'fullRecoverSpeed': conf['fullRecoverSpeed'],
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
            'customStyle': conf['barStyle'],
            'invert': conf['invert'],
        }
        if conf['enableBgColor']:
            progress_bar_style['bgColor'] = conf['barBgColor']
        self._progress_bar.set_style(progress_bar_style)
