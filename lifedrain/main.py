'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from anki.hooks import addHook, wrap
from anki.sched import Scheduler
from anki.collection import _Collection
from aqt import appVersion
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
        Reviewer._keyHandler = wrap(  # pylint: disable=protected-access
            Reviewer._keyHandler,  # pylint: disable=protected-access
            lambda self, evt, _old:
            lifedrain.toggle_drain() if evt.text() == 'p' else _old(self, evt),
            'around'
        )
    elif appVersion.startswith('2.1'):
        addHook(
            'reviewStateShortcuts',
            lambda shortcuts: shortcuts.append(tuple(['p', lifedrain.toggle_drain]))
        )

    addHook('afterStateChange', lambda *args: lifedrain.screen_change(args[0]))
    addHook('showQuestion', lifedrain.show_question)
    addHook('showAnswer', lifedrain.show_answer)
    addHook('reset', lifedrain.undo)
    addHook('revertedCard', lambda cid: lifedrain.undo())
    addHook('leech', lambda *args: lifedrain.status.update({'newCardState': True}))
    addHook('LifeDrain.recover', lifedrain.recover)

    Scheduler.buryNote = wrap(
        Scheduler.buryNote,
        lambda *args: lifedrain.status.update({'newCardState': True})
    )
    Scheduler.buryCards = wrap(
        Scheduler.buryCards,
        lambda *args: lifedrain.status.update({'newCardState': True})
    )
    Scheduler.suspendCards = wrap(
        Scheduler.suspendCards,
        lambda *args: lifedrain.status.update({'newCardState': True})
    )
    _Collection.remCards = wrap(
        _Collection.remCards,
        lambda *args: lifedrain.status.update({'newCardState': True})
    )
    EditCurrent.__init__ = wrap(
        EditCurrent.__init__,
        lambda *args: lifedrain.status.update({'reviewed': False})
    )
    Reviewer._answerCard = wrap(  # pylint: disable=protected-access
        Reviewer._answerCard,  # pylint: disable=protected-access
        lambda *args: lifedrain.status.update({'reviewResponse': args[1]}),
        'before'
    )
