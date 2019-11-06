'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from anki.hooks import addHook, wrap
from anki.sched import Scheduler
from anki.collection import _Collection
from aqt import mw, appVersion
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.editcurrent import EditCurrent

from .lifedrain import LifeDrain


def main():
    '''
    Lifedrain's main function.
    '''
    lifedrain = LifeDrain()

    # Dealing with key presses in Anki 2.0 and 2.1
    if appVersion.startswith('2.0'):
        def key_handler(self, evt, _old):
            '''
            Appends 'p' shortcut to pause the drain.
            '''
            key = evt.text()
            if key == 'p':
                lifedrain.toggle_drain()
            else:
                _old(self, evt)

        Reviewer._keyHandler = wrap(Reviewer._keyHandler, key_handler, 'around')

    elif appVersion.startswith('2.1'):
        def _add_shortcut(shortcuts):
            '''
            Appends 'p' shortcut to pause the drain.
            '''
            shortcuts.append(tuple(['p', lifedrain.toggle_drain]))

        addHook('reviewStateShortcuts', _add_shortcut)

    def show_question():
        '''
        Called when a question is shown.
        '''
        if not lifedrain.disable:
            activate_timer()
            if lifedrain.status['reviewed']:
                if lifedrain.status['reviewResponse'] == 1:
                    lifedrain._deck.recover(damage=True)
                else:
                    lifedrain._deck.recover()
            lifedrain.status['reviewed'] = False
            lifedrain.status['newCardState'] = False

    def show_answer():
        '''
        Called when an answer is shown.
        '''
        if not lifedrain.disable:
            if lifedrain.stop_on_answer:
                deactivate_timer()
            else:
                activate_timer()
            lifedrain.status['reviewed'] = True

    def undo():
        '''
        Deals with undoing.
        '''
        if not lifedrain.disable:
            if lifedrain.status['screen'] == 'review' and not lifedrain.status['newCardState']:
                lifedrain.status['reviewed'] = False
                lifedrain._deck.recover(False)
            lifedrain.status['newCardState'] = False

    def leech():
        '''
        Called when the card becomes a leech.
        '''
        lifedrain.status['newCardState'] = True

    def bury():
        '''
        Called when the card is buried.
        '''
        lifedrain.status['newCardState'] = True

    def suspend():
        '''
        Called when the card is suspended.
        '''
        lifedrain.status['newCardState'] = True

    def delete():
        '''
        Called when the card is deleted.
        '''
        lifedrain.status['newCardState'] = True

    def activate_timer():
        '''
        Activates the timer that reduces the bar.
        '''
        if not lifedrain.disable and lifedrain._timer is not None and not lifedrain._timer.isActive():
            lifedrain._timer.start()

    def deactivate_timer():
        '''
        Deactivates the timer that reduces the bar.
        '''
        if not lifedrain.disable and lifedrain._timer is not None and lifedrain._timer.isActive():
            lifedrain._timer.stop()

    def recover(increment=True, value=None, damage=False):
        '''
        Method ran when invoking 'LifeDrain.recover' hook.
        '''
        lifedrain._deck.recover(increment, value, damage)

    def answer_card(resp):
        '''
        Called when a card is answered
        '''
        lifedrain.status['reviewResponse'] = resp

    addHook('afterStateChange', lambda *args: lifedrain.screen_change(args[0]))
    addHook('showQuestion', show_question)
    addHook('showAnswer', show_answer)
    addHook('reset', undo)
    addHook('revertedCard', lambda cid: undo())
    addHook('leech', lambda *args: leech())
    addHook('LifeDrain.recover', recover)

    Scheduler.buryNote = wrap(Scheduler.buryNote, lambda *args: bury())
    Scheduler.buryCards = wrap(Scheduler.buryCards, lambda *args: bury())
    Scheduler.suspendCards = wrap(Scheduler.suspendCards, lambda *args: suspend())
    _Collection.remCards = wrap(_Collection.remCards, lambda *args: delete())
    EditCurrent.__init__ = wrap(EditCurrent.__init__,
                                lambda *args: lifedrain.status.update({'reviewed': False}))
    Reviewer._answerCard = wrap(Reviewer._answerCard, lambda *args: answer_card(args[1]), 'before')
