# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from typing import Any, Callable

from anki import hooks
from anki.decks import DeckId
from aqt import gui_hooks, mw, qt

from .defaults import DEFAULTS
from .exceptions import GetCollectionError, GetMainWindowError
from .lifedrain import Lifedrain


def main() -> None:
    """Initialize the Life Drain add-on."""
    if mw is None:
        raise GetMainWindowError

    lifedrain = Lifedrain(mw, qt)

    setup_shortcuts(lifedrain)
    setup_state_change(lifedrain)
    setup_deck_browser(lifedrain)
    setup_overview(lifedrain)
    setup_review(lifedrain)

    mw.addonManager.setConfigAction(__name__, lifedrain.global_settings)


def setup_shortcuts(lifedrain: Lifedrain) -> None:
    """Configure the shortcuts provided by the add-on."""

    def state_shortcuts(state: str, shortcuts: list[tuple]) -> None:
        if state == 'review':
            lifedrain.review_shortcuts(shortcuts)
        elif state == 'overview':
            lifedrain.overview_shortcuts(shortcuts)

    gui_hooks.collection_did_load.append(lambda col: lifedrain.update_global_shortcuts())  # noqa: ARG005
    gui_hooks.state_shortcuts_will_change.append(state_shortcuts)


def setup_state_change(lifedrain: Lifedrain) -> None:
    """Set hooks triggered when changing state."""
    gui_hooks.state_will_change.append(lambda *args: lifedrain.screen_change(args[0]))


def setup_deck_browser(lifedrain: Lifedrain) -> None:
    """Add an option to open deck settings from deck browser."""
    def options_menu(menu: Any, did: int) -> None:
        action = menu.addAction('Life Drain')
        menu.insertAction(menu.actions()[2], action)
        qt.qconnect(
            action.triggered,
            lambda b: action_deck_settings(DeckId(did)),  # noqa: ARG005
        )

    def action_deck_settings(did: DeckId) -> None:
        if mw is None:
            raise GetMainWindowError
        if mw.col is None:
            raise GetCollectionError
        mw.col.decks.select(did)
        lifedrain.deck_settings()

    gui_hooks.deck_browser_will_show_options_menu.append(options_menu)


def setup_overview(lifedrain: Lifedrain) -> None:
    """Add a Life Drain button into the overview screen."""

    def bottom_bar_draw(link_handler: Callable[..., bool], links: list[list]) -> Callable:
        links.append([DEFAULTS['deckSettingsShortcut'], 'lifedrain', 'Life Drain'])
        links.append(['None', 'recover', 'Recover'])

        def custom_link_handler(url: str) -> bool:
            if url == 'lifedrain':
                lifedrain.deck_settings()
            elif url == 'recover':
                lifedrain.deck_manager.recovering = True
                lifedrain.toggle_drain()
            return link_handler(url=url)

        return custom_link_handler

    gui_hooks.overview_will_render_bottom.append(bottom_bar_draw)


def setup_review(lifedrain: Lifedrain) -> None:
    """Set hooks triggered while reviewing."""
    gui_hooks.reviewer_did_show_question.append(lifedrain.show_question)
    gui_hooks.reviewer_did_show_answer.append(
        lambda card: lifedrain.show_answer())  # noqa: ARG005
    gui_hooks.reviewer_did_answer_card.append(
        lambda *args: lifedrain.status.update({'review_response': args[2]}))
    if hasattr(gui_hooks, 'review_did_undo'):
        gui_hooks.review_did_undo.append(
            lambda card_id: lifedrain.status.update({'action': 'undo'}))  # noqa: ARG005
    gui_hooks.state_did_undo.append(
        lambda out: lifedrain.status.update({'action': 'undo'}))  # noqa: ARG005

    gui_hooks.browser_will_show.append(
        lambda browser: lifedrain.opened_window())  # noqa: ARG005
    gui_hooks.editor_did_init.append(
        lambda editor: lifedrain.opened_window())  # noqa: ARG005
    gui_hooks.deck_options_did_load.append(
        lambda deck_options: lifedrain.opened_window())  # noqa: ARG005
    gui_hooks.filtered_deck_dialog_did_load_deck.append(
        lambda *args: lifedrain.opened_window())  # noqa: ARG005

    # Action on cards
    hooks.notes_will_be_deleted.append(
        lambda *args: lifedrain.status.update({'action': 'delete'}))  # noqa: ARG005
    gui_hooks.reviewer_will_suspend_note.append(
        lambda *args: lifedrain.status.update({'action': 'suspend'}))  # noqa: ARG005
    gui_hooks.reviewer_will_suspend_card.append(
        lambda *args: lifedrain.status.update({'action': 'suspend'}))  # noqa: ARG005
    gui_hooks.reviewer_will_bury_note.append(
        lambda *args: lifedrain.status.update({'action': 'bury'}))  # noqa: ARG005
    gui_hooks.reviewer_will_bury_card.append(
        lambda *args: lifedrain.status.update({'action': 'bury'}))  # noqa: ARG005
