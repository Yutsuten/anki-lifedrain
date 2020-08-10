"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from aqt import forms, mw, qt, gui_hooks
from aqt.overview import OverviewBottomBar
from aqt.preferences import Preferences
from aqt.progress import ProgressManager
from aqt.toolbar import BottomBar

from anki import hooks
from anki.lang import _
from anki.sched import Scheduler

from .lifedrain import Lifedrain


def main():
    """Initializes the Life Drain add-on."""
    make_timer = ProgressManager(mw).timer
    lifedrain = Lifedrain(make_timer, mw, qt)

    setup_user_interface(lifedrain)
    setup_shortcuts(lifedrain)
    setup_state_change(lifedrain)
    setup_deck_browser(lifedrain)
    setup_overview(lifedrain)
    setup_review(lifedrain)

    mw.addonManager.setConfigAction(__name__, lifedrain.global_settings)
    hooks.addHook('LifeDrain.recover', lifedrain.deck_manager.recover_life)


def setup_user_interface(lifedrain):
    """Generates the User Interfaces for configurating the add-on.

    Generates the Preferences (Global Settings) User Interface. It also adds the
    triggers for loading and saving each setting.
    """
    # Global Settings
    forms.preferences.Ui_Preferences.setupUi = hooks.wrap(
        forms.preferences.Ui_Preferences.setupUi,
        lambda *args: lifedrain.preferences_ui(args[0]))
    Preferences.__init__ = hooks.wrap(
        Preferences.__init__,
        lambda *args: lifedrain.preferences_load(args[0]))
    Preferences.accept = hooks.wrap(
        Preferences.accept, lambda *args: lifedrain.preferences_save(args[0]),
        'before')


def setup_shortcuts(lifedrain):
    """Configures the shortcuts provided by the add-on."""

    # Global shortcuts
    mw.applyShortcuts([tuple(['Ctrl+l', lifedrain.global_settings])])

    # State shortcuts
    def state_shortcuts(state, shortcuts):
        if state == 'review':
            shortcuts.append(tuple(['p', lifedrain.toggle_drain]))
            shortcuts.append(tuple(['l', lifedrain.deck_settings]))
        elif state == 'overview':
            shortcuts.append(tuple(['l', lifedrain.deck_settings]))

    gui_hooks.state_shortcuts_will_change.append(state_shortcuts)


def setup_state_change(lifedrain):
    """Setup hooks triggered when changing state."""
    gui_hooks.state_will_change.append(
        lambda *args: lifedrain.screen_change(args[0]))
    gui_hooks.state_did_reset.append(
        lambda *args: lifedrain.status.update({'reviewed': False}))


def setup_deck_browser(lifedrain):
    """Adds an option to open deck settings from deck browser."""

    def options_menu(menu, did):
        action = menu.addAction('Life Drain')
        menu.insertAction(menu.actions()[2], action)
        qt.qconnect(action.triggered, lambda b: action_deck_settings(did))

    def action_deck_settings(did):
        mw.col.decks.select(did)
        lifedrain.deck_settings()

    gui_hooks.deck_browser_will_show_options_menu.append(options_menu)


def setup_overview(lifedrain):
    """Adds a Life Drain button into the overview screen."""

    def button(text, link, shortcut_key=None):
        attribute_list = [
            'title="{}"'.format(_('Shortcut key: %s') % shortcut_key),
            'onclick="pycmd(\'{}\')"'.format(link)]
        attributes = ' '.join(attribute_list)
        return '<button {}>{}</button>'.format(attributes, text)

    def bottom_bar_draw(*args, **kwargs):
        if isinstance(kwargs['web_context'], OverviewBottomBar):

            def update_buf(buf):
                buttons = [button('Life Drain', 'lifedrain', 'L'),
                           button('Recover', 'recover', 'None')]
                return '{}\n{}'.format(buf, '\n'.join(buttons))

            def link_handler(url):
                if url == 'lifedrain':
                    lifedrain.deck_settings()
                elif url == 'recover':
                    lifedrain.deck_manager.recover_life(value=10000)
                default_link_handler(url=url)

            default_link_handler = kwargs['link_handler']

            new_kwargs = dict(kwargs)
            new_kwargs['buf'] = update_buf(kwargs['buf'])
            new_kwargs['link_handler'] = link_handler
            return default_bottom_bar_draw(*args, **new_kwargs)

        return default_bottom_bar_draw(*args, **kwargs)

    default_bottom_bar_draw = BottomBar.draw
    BottomBar.draw = bottom_bar_draw


def setup_review(lifedrain):
    """Setup hooks triggered while reviewing."""
    gui_hooks.reviewer_did_show_question.append(
        lambda card: lifedrain.show_question())
    gui_hooks.reviewer_did_show_answer.append(
        lambda card: lifedrain.show_answer())
    gui_hooks.reviewer_did_answer_card.append(
        lambda *args: lifedrain.status.update({'review_response': args[2]}))
    gui_hooks.review_did_undo.append(lambda card_id: lifedrain.undo())

    # Action on cards
    hooks.card_did_leech.append(
        lambda *args: lifedrain.status.update({'special_action': True}))
    hooks.notes_will_be_deleted.append(
        lambda *args: lifedrain.status.update({'special_action': True}))
    Scheduler.buryCards = hooks.wrap(
        Scheduler.buryCards,
        lambda *args: lifedrain.status.update({'special_action': True}))
    Scheduler.suspendCards = hooks.wrap(
        Scheduler.suspendCards,
        lambda *args: lifedrain.status.update({'special_action': True}))
