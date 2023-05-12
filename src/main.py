# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from typing import Any, Callable, Optional

from anki import hooks
from anki.decks import DeckId
from aqt import gui_hooks, mw, qt
from aqt.overview import OverviewBottomBar
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.toolbar import BottomBar

from .lifedrain import Lifedrain


def main() -> None:
    """Initialize the Life Drain add-on."""
    if mw is None:
        raise RuntimeError

    make_timer = ProgressManager(mw).timer
    lifedrain = Lifedrain(make_timer, mw, qt)

    setup_shortcuts(lifedrain)
    setup_state_change(lifedrain)
    setup_deck_browser(lifedrain)
    setup_overview(lifedrain)
    setup_review(lifedrain)

    mw.addonManager.setConfigAction(__name__, lifedrain.global_settings)
    hooks.addHook('LifeDrain.recover', lifedrain.deck_manager.recover_life)


def setup_shortcuts(lifedrain: Lifedrain) -> None:
    """Configure the shortcuts provided by the add-on."""

    def global_shortcuts() -> None:
        lifedrain.clear_global_shortcuts()
        lifedrain.set_global_shortcuts()

    def state_shortcuts(state: str, shortcuts: list[tuple]) -> None:
        if state == 'review':
            lifedrain.review_shortcuts(shortcuts)
        elif state == 'overview':
            lifedrain.overview_shortcuts(shortcuts)

    gui_hooks.collection_did_load.append(lambda col: global_shortcuts())  # noqa: ARG
    gui_hooks.state_shortcuts_will_change.append(state_shortcuts)


def setup_state_change(lifedrain: Lifedrain) -> None:
    """Set hooks triggered when changing state."""
    gui_hooks.state_will_change.append(
        lambda *args: lifedrain.screen_change(args[0]))
    gui_hooks.state_did_reset.append(
        lambda *args: lifedrain.status.update({'reviewed': False}))  # noqa: ARG


def setup_deck_browser(lifedrain: Lifedrain) -> None:
    """Add an option to open deck settings from deck browser."""
    def options_menu(menu: Any, did: int) -> None:
        action = menu.addAction('Life Drain')
        menu.insertAction(menu.actions()[2], action)
        qt.qconnect(action.triggered, lambda b: action_deck_settings(DeckId(did)))  # noqa: ARG

    def action_deck_settings(did: DeckId) -> None:
        if mw is None:
            raise RuntimeError
        if mw.col is None:
            raise RuntimeError
        mw.col.decks.select(did)
        lifedrain.deck_settings()

    gui_hooks.deck_browser_will_show_options_menu.append(options_menu)


def setup_overview(lifedrain: Lifedrain) -> None:
    """Add a Life Drain button into the overview screen."""

    def button(text: str, link: str, shortcut_key: Optional[str]) -> str:
        attribute_list = [
            f'''title="Shortcut key: {shortcut_key}"''',
            f'onclick="pycmd(\'{link}\')"']
        attributes = ' '.join(attribute_list)
        return f'<button {attributes}>{text}</button>'

    def bottom_bar_draw(*args, **kwargs) -> None:
        if isinstance(kwargs['web_context'], OverviewBottomBar):

            def update_buf(buf: str) -> str:
                buttons = [button('Life Drain', 'lifedrain', 'L'),
                           button('Recover', 'recover', 'None')]
                return '{}\n{}'.format(buf, '\n'.join(buttons))

            def link_handler(url: str) -> Any:
                if url == 'lifedrain':
                    lifedrain.deck_settings()
                elif url == 'recover':
                    lifedrain.deck_manager.recover_life(value=10000)
                return default_link_handler(url=url)

            default_link_handler = kwargs['link_handler']

            new_kwargs = dict(kwargs)
            new_kwargs['buf'] = update_buf(kwargs['buf'])
            new_kwargs['link_handler'] = link_handler
            return default_bottom_bar_draw(*args, **new_kwargs)

        return default_bottom_bar_draw(*args, **kwargs)

    default_bottom_bar_draw = BottomBar.draw
    BottomBar.draw = bottom_bar_draw


def setup_review(lifedrain: Lifedrain) -> None:
    """Set hooks triggered while reviewing."""
    gui_hooks.reviewer_did_show_question.append(lifedrain.show_question)
    gui_hooks.reviewer_did_show_answer.append(
        lambda card: lifedrain.show_answer())  # noqa: ARG
    gui_hooks.reviewer_did_answer_card.append(
        lambda *args: lifedrain.status.update({'review_response': args[2]}))
    gui_hooks.review_did_undo.append(
        lambda card_id: lifedrain.status.update({'action': 'undo'}))  # noqa: ARG
    gui_hooks.state_did_undo.append(
        lambda out: lifedrain.status.update({'action': 'undo'}))  # noqa: ARG

    gui_hooks.browser_will_show.append(
        lambda browser: lifedrain.opened_window())  # noqa: ARG
    gui_hooks.editor_did_init.append(
        lambda editor: lifedrain.opened_window())  # noqa: ARG
    gui_hooks.deck_options_did_load.append(
        lambda deck_options: lifedrain.opened_window())  # noqa: ARG
    gui_hooks.filtered_deck_dialog_did_load_deck.append(
        lambda *args: lifedrain.opened_window())  # noqa: ARG

    # Action on cards
    hooks.notes_will_be_deleted.append(
        lambda *args: lifedrain.status.update({'action': 'delete'}))  # noqa: ARG

    def reviewer_wrap(old_method: Callable, action: str) -> Callable:
        def new_method(reviewer, *args):  # noqa: ARG
            old_method(reviewer)
            lifedrain.status.update({'action': action})
        return new_method

    Reviewer.suspend_current_note = reviewer_wrap(
        Reviewer.suspend_current_note,
        'suspend',
    )
    Reviewer.suspend_current_card = reviewer_wrap(
        Reviewer.suspend_current_card,
        'suspend',
    )
    Reviewer.bury_current_note = reviewer_wrap(
        Reviewer.bury_current_note,
        'bury',
    )
    Reviewer.bury_current_card = reviewer_wrap(
        Reviewer.bury_current_card,
        'bury',
    )
