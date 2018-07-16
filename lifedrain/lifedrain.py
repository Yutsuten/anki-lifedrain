'''
Anki Add-on: Life Drain
Add a bar that is reduced as time passes. Completing reviews recovers life.

**
Some of the code (progress bar) used here was originally done by Glutanimate,
from the Addon Progress Bar. So I copied the copyright from that Addon and
appended my name.
**

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
            (c) Yutsuten 2018 <https://github.com/Yutsuten>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
'''

from anki.hooks import addHook, wrap
from anki.sched import Scheduler
from anki.collection import _Collection
from aqt import qt, mw, forms, appVersion
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.deckconf import DeckConf
from aqt.dyndeckconf import DeckConf as FiltDeckConf
from aqt.preferences import Preferences
from aqt.editcurrent import EditCurrent


POSITION_OPTIONS = ['Top', 'Bottom']
STYLE_OPTIONS = [
    'Default', 'Cde', 'Cleanlooks', 'Fusion', 'Gtk', 'Macintosh',
    'Motif', 'Plastique', 'Windows', 'Windows Vista', 'Windows XP'
]
DEFAULTS = {
    'maxLife': 120,
    'recover': 5,
    'barPosition': POSITION_OPTIONS.index('Bottom'),
    'barHeight': 15,
    'barBgColor': '#f3f3f2',
    'barFgColor': '#489ef6',
    'barBorderRadius': 0,
    'barStyle': STYLE_OPTIONS.index('Default')
}


# Saving data inside a class to access it as lifeDrain.config
class LifeDrain(object):  # pylint: disable=too-few-public-methods
    '''
    Contains the state of the life drain.
    '''
    config = {}
    deckBarManager = None
    timer = None
    status = {
        'reviewed': False,
        'newCardState': False,
        'screen': None
    }
    shortcutKeys = None


# Variable with the state the life drain
# Pylint complains that it is a constant, so I disabled this check
lifeDrain = LifeDrain()  # pylint: disable=invalid-name


# Allowed this method to use global statement, as I don't see any other
# way to access my variables inside the methods extended from Anki.
# Adding new parameters to those methods is not possible, and cannot use
# classes because it adds a parameter 'self' to the methods
def getLifeDrain():
    '''
    Gets the state of the life drain.
    '''
    global lifeDrain  # pylint: disable=invalid-name,global-statement
    return lifeDrain


def globalSettingsLifeDrainTabUi(self, Preferences):
    '''
    Appends LifeDrain tab to Global Settings dialog.
    '''
    tabWidget = qt.QWidget()
    layout = qt.QGridLayout(tabWidget)
    layout.setColumnStretch(0, 3)
    layout.setColumnStretch(3, 1)
    layout.setColumnMinimumWidth(2, 50)
    row = 0

    title = qt.QLabel('<b>Life Drain Bar style</b>')
    layout.addWidget(title, row, 0, 1, 3)
    row += 1

    positionLabel = qt.QLabel('Position')
    self.positionList = qt.QComboBox(tabWidget)
    for position in POSITION_OPTIONS:
        self.positionList.addItem(position)
    layout.addWidget(positionLabel, row, 0)
    layout.addWidget(self.positionList, row, 1, 1, 2)
    row += 1

    heightLabel = qt.QLabel('Height')
    self.heightInput = qt.QSpinBox(tabWidget)
    self.heightInput.setRange(1, 40)
    layout.addWidget(heightLabel, row, 0)
    layout.addWidget(self.heightInput, row, 1, 1, 2)
    row += 1

    bgLabel = qt.QLabel('Background color')
    self.bgColorPreview = qt.QLabel('')
    bgSelectButton = qt.QPushButton('Select')
    self.bgColorDialog = qt.QColorDialog(bgSelectButton)
    bgSelectButton.pressed.connect(
        lambda: selectColorDialog(self.bgColorDialog, self.bgColorPreview)
    )
    layout.addWidget(bgLabel, row, 0)
    layout.addWidget(bgSelectButton, row, 1)
    layout.addWidget(self.bgColorPreview, row, 2)
    row += 1

    fgLabel = qt.QLabel('Foreground color')
    self.fgColorPreview = qt.QLabel('')
    fgSelectButton = qt.QPushButton('Select')
    self.fgColorDialog = qt.QColorDialog(fgSelectButton)
    fgSelectButton.pressed.connect(
        lambda: selectColorDialog(self.fgColorDialog, self.fgColorPreview)
    )
    layout.addWidget(fgLabel, row, 0)
    layout.addWidget(fgSelectButton, row, 1)
    layout.addWidget(self.fgColorPreview, row, 2)
    row += 1

    borderRadiusLabel = qt.QLabel('Border radius')
    self.borderRadiusInput = qt.QSpinBox(tabWidget)
    self.borderRadiusInput.setRange(0, 20)
    layout.addWidget(borderRadiusLabel, row, 0)
    layout.addWidget(self.borderRadiusInput, row, 1, 1, 2)
    row += 1

    styleLabel = qt.QLabel('Style*')
    self.styleList = qt.QComboBox(tabWidget)
    for customStyle in STYLE_OPTIONS:
        self.styleList.addItem(customStyle)
    layout.addWidget(styleLabel, row, 0)
    layout.addWidget(self.styleList, row, 1, 1, 2)
    row += 1

    descriptionLabel = qt.QLabel(
        ' * Please keep in mind that some styles may not work well in some '
        'platforms!'
    )
    descriptionLabel.setWordWrap(True)
    layout.addWidget(descriptionLabel, row, 0, 1, 4)
    row += 1

    spacer = qt.QSpacerItem(
        1, 1, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding
    )
    layout.addItem(spacer, row, 0)

    self.tabWidget.addTab(tabWidget, "Life Drain")


def selectColorDialog(qColorDialog, previewLabel):
    '''
    Shows the select color dialog and updates the preview color in settings.
    '''
    if qColorDialog.exec_():
        previewLabel.setStyleSheet(
            'QLabel { background-color: %s; }'
            % qColorDialog.currentColor().name()
        )


def globalLoadConf(self, mw):
    '''
    Loads LifeDrain global configurations.
    '''
    conf = self.mw.col.conf
    self.form.positionList.setCurrentIndex(
        conf.get('barPosition', DEFAULTS['barPosition'])
    )
    self.form.heightInput.setValue(
        conf.get('barHeight', DEFAULTS['barHeight'])
    )

    self.form.bgColorDialog.setCurrentColor(
        qt.QColor(conf.get('barBgColor', DEFAULTS['barBgColor']))
    )
    self.form.bgColorPreview.setStyleSheet(
        'QLabel { background-color: %s; }'
        % self.form.bgColorDialog.currentColor().name()
    )

    self.form.fgColorDialog.setCurrentColor(
        qt.QColor(conf.get('barFgColor', DEFAULTS['barFgColor']))
    )
    self.form.fgColorPreview.setStyleSheet(
        'QLabel { background-color: %s; }'
        % self.form.fgColorDialog.currentColor().name()
    )

    self.form.borderRadiusInput.setValue(
        conf.get('barBorderRadius', DEFAULTS['barBorderRadius'])
    )
    self.form.styleList.setCurrentIndex(
        conf.get('barStyle', DEFAULTS['barStyle'])
    )


def globalSaveConf(self):
    '''
    Saves LifeDrain global configurations.
    '''
    lifeDrain = getLifeDrain()

    conf = self.mw.col.conf
    conf['barPosition'] = self.form.positionList.currentIndex()
    conf['barHeight'] = self.form.heightInput.value()
    conf['barBgColor'] = self.form.bgColorDialog.currentColor().name()
    conf['barFgColor'] = self.form.fgColorDialog.currentColor().name()
    conf['barBorderRadius'] = self.form.borderRadiusInput.value()
    conf['barStyle'] = self.form.styleList.currentIndex()

    # Create new instance of the bar with new configurations
    config = {
        'position': conf.get('barPosition', DEFAULTS['barPosition']),
        'progressBarStyle': {
            'height': conf.get('barHeight', DEFAULTS['barHeight']),
            'backgroundColor': conf.get('barBgColor', DEFAULTS['barBgColor']),
            'foregroundColor': conf.get('barFgColor', DEFAULTS['barFgColor']),
            'borderRadius': conf.get(
                'barBorderRadius', DEFAULTS['barBorderRadius']),
            'customStyle': conf.get('barStyle', DEFAULTS['barStyle'])
        }
    }
    progressBar = AnkiProgressBar(
        config, lifeDrain.deckBarManager.getBar().getCurrentValue()
    )
    lifeDrain.deckBarManager.updateAnkiProgressBar(progressBar)


def deckSettingsLifeDrainTabUi(self, Dialog):
    '''
    Appends a new tab to deck settings dialog.
    '''
    tabWidget = qt.QWidget()
    layout = qt.QGridLayout(tabWidget)
    row = 0

    descriptionLabel = qt.QLabel(
        'The <b>maximum life</b> is the time in seconds for the life bar go '
        'from full to empty.\n<b>Recover</b> is the time in seconds that is '
        'recovered after answering a card.'
    )
    descriptionLabel.setWordWrap(True)
    layout.addWidget(descriptionLabel, row, 0, 1, 3)
    row += 1

    maxLifeLabel = qt.QLabel('Maximum life')
    self.maxLifeInput = qt.QSpinBox(tabWidget)
    self.maxLifeInput.setRange(1, 1000)
    layout.addWidget(maxLifeLabel, row, 0)
    layout.addWidget(self.maxLifeInput, row, 2)
    row += 1

    recoverLabel = qt.QLabel('Recover')
    self.recoverInput = qt.QSpinBox(tabWidget)
    self.recoverInput.setRange(1, 1000)
    layout.addWidget(recoverLabel, row, 0)
    layout.addWidget(self.recoverInput, row, 2)
    row += 1

    spacer = qt.QSpacerItem(
        1, 1, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding
    )
    layout.addItem(spacer, row, 0)

    self.tabWidget.addTab(tabWidget, "Life Drain")


def loadDeckConf(self):
    '''
    Loads LifeDrain deck configurations.
    '''
    self.conf = self.mw.col.decks.confForDid(self.deck['id'])
    self.form.maxLifeInput.setValue(
        self.conf.get('maxLife', DEFAULTS['maxLife'])
    )
    self.form.recoverInput.setValue(
        self.conf.get('recover', DEFAULTS['recover'])
    )


def saveDeckConf(self):
    '''
    Saves LifeDrain deck configurations.
    '''
    lifeDrain = getLifeDrain()

    self.conf['maxLife'] = self.form.maxLifeInput.value()
    self.conf['recover'] = self.form.recoverInput.value()
    lifeDrain.deckBarManager.updateDeckConf(self.deck['id'], self.conf)


def customStudyLifeDrainUi(self, Dialog):
    '''
    Adds LifeDrain configurations to custom study dialog.
    '''
    row = 0

    lifeDrainGroupBox = qt.QGroupBox('Life Drain')
    layout = qt.QGridLayout(lifeDrainGroupBox)
    row = 0

    maxLifeLabel = qt.QLabel('Maximum life')
    self.maxLifeInput = qt.QSpinBox(lifeDrainGroupBox)
    self.maxLifeInput.setRange(1, 1000)
    layout.addWidget(maxLifeLabel, row, 0, 1, 2)
    layout.addWidget(self.maxLifeInput, row, 2)
    row += 1

    recoverLabel = qt.QLabel('Recover')
    self.recoverInput = qt.QSpinBox(lifeDrainGroupBox)
    self.recoverInput.setRange(1, 1000)
    layout.addWidget(recoverLabel, row, 0, 1, 2)
    layout.addWidget(self.recoverInput, row, 2)
    row += 1

    index = 2 if appVersion.startswith('2.0') else 3
    self.verticalLayout.insertWidget(index, lifeDrainGroupBox)


forms.preferences.Ui_Preferences.setupUi = wrap(
    forms.preferences.Ui_Preferences.setupUi, globalSettingsLifeDrainTabUi
)
Preferences.__init__ = wrap(Preferences.__init__, globalLoadConf)
Preferences.accept = wrap(Preferences.accept, globalSaveConf, 'before')


forms.dconf.Ui_Dialog.setupUi = wrap(
    forms.dconf.Ui_Dialog.setupUi, deckSettingsLifeDrainTabUi
)
DeckConf.loadConf = wrap(DeckConf.loadConf, loadDeckConf)
DeckConf.saveConf = wrap(DeckConf.saveConf, saveDeckConf, 'before')


forms.dyndconf.Ui_Dialog.setupUi = wrap(
    forms.dyndconf.Ui_Dialog.setupUi, customStudyLifeDrainUi
)
FiltDeckConf.loadConf = wrap(FiltDeckConf.loadConf, loadDeckConf)
FiltDeckConf.saveConf = wrap(FiltDeckConf.saveConf, saveDeckConf, 'before')


class AnkiProgressBar(object):
    '''
    Creates and manages a Progress Bar in Anki.
    '''
    _qProgressBar = None
    _maxValue = 1
    _currentValue = 1

    def __init__(self, config, maxValue):
        self._qProgressBar = qt.QProgressBar()
        self.setMaxValue(maxValue)
        self.resetBar()
        self.setTextVisible(False)
        self.setStyle(config['progressBarStyle'])
        self._dockAt(config['position'])

    def show(self):
        '''
        Shows the progress bar.
        '''
        self._qProgressBar.show()

    def hide(self):
        '''
        Hides the progress bar.
        '''
        self._qProgressBar.hide()

    def resetBar(self):
        '''
        Resets bar, setting current value to maximum.
        '''
        self._currentValue = self._maxValue
        self._validateUpdateCurrentValue()

    def setMaxValue(self, maxValue):
        '''
        Sets the maximum value for the bar.
        '''
        self._maxValue = maxValue
        if self._maxValue <= 0:
            self._maxValue = 1
        self._qProgressBar.setRange(0, self._maxValue)

    def setCurrentValue(self, currentValue):
        '''
        Sets the current value for the bar.
        '''
        self._currentValue = currentValue
        self._validateUpdateCurrentValue()

    def incCurrentValue(self, increment):
        '''
        Increments the current value of the bar.
        Negative values will decrement.
        '''
        self._currentValue += increment
        self._validateUpdateCurrentValue()

    def getCurrentValue(self):
        '''
        Gets the current value of the bar.
        '''
        return self._currentValue

    def setTextVisible(self, flag):
        '''
        Sets the visibility of the text on bar.
        '''
        self._qProgressBar.setTextVisible(flag)

    def setStyle(self, options):
        '''
        Sets the style of the bar.
        '''
        customStyle = STYLE_OPTIONS[options['customStyle']] \
            .replace(' ', '').lower()
        if customStyle != 'default':
            palette = qt.QPalette()
            palette.setColor(
                qt.QPalette.Base, qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                qt.QPalette.Highlight, qt.QColor(options['foregroundColor'])
            )
            palette.setColor(
                qt.QPalette.Button, qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                qt.QPalette.Window, qt.QColor(options['backgroundColor'])
            )

            self._qProgressBar.setStyle(qt.QStyleFactory.create(customStyle))
            self._qProgressBar.setPalette(palette)
            self._qProgressBar.setStyleSheet(
                '''
                QProgressBar {
                    max-height: %spx;
                }
                '''
                % (
                    options['height'],
                )
            )
        else:
            self._qProgressBar.setStyleSheet(
                '''
                QProgressBar {
                    text-align:center;
                    background-color: %s;
                    border-radius: %dpx;
                    max-height: %spx;
                }
                QProgressBar::chunk {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                '''
                % (
                    options['backgroundColor'],
                    options['borderRadius'],
                    options['height'],
                    options['foregroundColor'],
                    options['borderRadius']
                )
            )

    def _validateUpdateCurrentValue(self):
        '''
        When updating current value, makes sure that the value is [0; max].
        '''
        if self._currentValue > self._maxValue:
            self._currentValue = self._maxValue
        elif self._currentValue < 0:
            self._currentValue = 0
        self._qProgressBar.setValue(self._currentValue)

    def _dockAt(self, place):
        '''
        Docks the bar at the specified place in the Anki window.
        '''
        place = POSITION_OPTIONS[place]

        if place not in POSITION_OPTIONS:
            place = DEFAULTS['barPosition']

        if place == 'Top':
            dockArea = qt.Qt.TopDockWidgetArea
        elif place == 'Bottom':
            dockArea = qt.Qt.BottomDockWidgetArea

        self._dock = qt.QDockWidget()
        tWidget = qt.QWidget()
        self._dock.setWidget(self._qProgressBar)
        self._dock.setTitleBarWidget(tWidget)

        existingWidgets = [
            widget for widget in mw.findChildren(qt.QDockWidget)
            if mw.dockWidgetArea(widget) == dockArea
        ]
        if not existingWidgets:
            mw.addDockWidget(dockArea, self._dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existingWidgets[0], self._dock, qt.Qt.Vertical)
        mw.web.setFocus()

    def __del__(self):
        self._dock.close()


class DeckProgressBarManager(object):
    '''
    Allow using the same instance of AnkiProgressBar with different
    configuration and currentValue for each deck.
    '''
    _ankiProgressBar = None
    _barInfo = {}
    _currentDeck = None

    def __init__(self, ankiProgressBar):
        self._ankiProgressBar = ankiProgressBar

    def addDeck(self, deckId, conf):
        '''
        Adds a deck to the manager.
        '''
        if str(deckId) not in self._barInfo:
            self._barInfo[str(deckId)] = {
                'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'recoverValue': conf.get('recover', DEFAULTS['recover'])
            }

    def setDeck(self, deckId):
        '''
        Sets the current deck.
        '''
        if self._currentDeck:
            self._barInfo[self._currentDeck]['currentValue'] = \
                self._ankiProgressBar.getCurrentValue()
        if deckId:
            self._currentDeck = str(deckId)
            self._ankiProgressBar.setMaxValue(
                self._barInfo[self._currentDeck]['maxValue']
            )
            self._ankiProgressBar.setCurrentValue(
                self._barInfo[self._currentDeck]['currentValue']
            )
        else:
            self._currentDeck = None

    def updateDeckConf(self, deckId, conf):
        '''
        Updates deck's current state.
        '''
        self._barInfo[str(deckId)]['maxValue'] = \
            conf.get('maxLife', DEFAULTS['maxLife'])
        self._barInfo[str(deckId)]['recoverValue'] = \
            conf.get('recover', DEFAULTS['recover'])

    def updateAnkiProgressBar(self, ankiProgressBar):
        '''
        Updates the AnkiProgressBar instance.
        '''
        del self._ankiProgressBar
        self._ankiProgressBar = ankiProgressBar

    def recover(self, increment=True):
        '''
        Abstraction for recovering life, increments the bar if increment is True (default).
        '''
        multiplier = 1
        if not increment:
            multiplier = -1
        self._ankiProgressBar.incCurrentValue(
            multiplier * self._barInfo[self._currentDeck]['recoverValue']
        )

    def getBar(self):
        '''
        Gets AnkiProgressBar instance.
        '''
        return self._ankiProgressBar


# Remove separator strip
SEPARATOR_STRIP_CSS = 'QMainWindow::separator { width: 0px; height: 0px; }'
try:
    import Night_Mode
    Night_Mode.nm_css_menu += SEPARATOR_STRIP_CSS
    if not Night_Mode.nm_state_on:
        mw.setStyleSheet(SEPARATOR_STRIP_CSS)
except ImportError:
    mw.setStyleSheet(SEPARATOR_STRIP_CSS)


def onEdit(*args):
    '''
    Updates reviewed status to False when user goes to edit mode.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['reviewed'] = False


def timerTrigger():
    '''
    When a second passed, this function is triggered.
    It decrements the bar by 1 unit.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.deckBarManager.getBar().incCurrentValue(-1)


def profileLoaded():
    '''
    Called when an Anki profile is loaded.
    Sets up some variables for the LifeDrain bar.
    '''
    lifeDrain = getLifeDrain()

    config = {
        'position': mw.col.conf.get('barPosition', DEFAULTS['barPosition']),
        'progressBarStyle': {
            'height': mw.col.conf.get('barHeight', DEFAULTS['barHeight']),
            'backgroundColor': mw.col.conf.get(
                'barBgColor', DEFAULTS['barBgColor']),
            'foregroundColor': mw.col.conf.get(
                'barFgColor', DEFAULTS['barFgColor']),
            'borderRadius': mw.col.conf.get(
                'barBorderRadius', DEFAULTS['barBorderRadius']),
            'customStyle': mw.col.conf.get('barStyle', DEFAULTS['barStyle'])
        }
    }
    progressBar = AnkiProgressBar(config, DEFAULTS['maxLife'])
    progressBar.hide()
    lifeDrain.deckBarManager = DeckProgressBarManager(progressBar)
    for deckId in mw.col.decks.allIds():
        lifeDrain.deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))


def afterStateChange(state, oldState):
    '''
    Called when user alternates between deckBrowser, overview, review screens.
    It updates some variables and shows/hides the bar.
    '''
    lifeDrain = getLifeDrain()

    if not lifeDrain.timer:
        lifeDrain.timer = ProgressManager(mw).timer(1000, timerTrigger, True)
    lifeDrain.timer.stop()

    if lifeDrain.status['reviewed'] and state in ['overview', 'review']:
        lifeDrain.deckBarManager.recover()
    lifeDrain.status['reviewed'] = False
    lifeDrain.status['screen'] = state

    if lifeDrain.deckBarManager:
        if state == 'deckBrowser':
            lifeDrain.deckBarManager.getBar().hide()
            lifeDrain.deckBarManager.setDeck(None)
        else:
            lifeDrain.deckBarManager.setDeck(mw.col.decks.current()['id'])
            lifeDrain.deckBarManager.getBar().show()

    if state == 'review':
        lifeDrain.timer.start()


def showQuestion():
    '''
    Called when a question is shown.
    '''
    lifeDrain = getLifeDrain()
    activateTimer()
    if lifeDrain.status['reviewed']:
        lifeDrain.deckBarManager.recover()
    lifeDrain.status['reviewed'] = False
    lifeDrain.status['newCardState'] = False


def showAnswer():
    '''
    Called when an answer is shown.
    '''
    lifeDrain = getLifeDrain()
    activateTimer()
    lifeDrain.status['reviewed'] = True


def undo():
    '''
    Deals with undoing.
    '''
    lifeDrain = getLifeDrain()
    if lifeDrain.status['screen'] == 'review' and not lifeDrain.status['newCardState']:
        lifeDrain.status['reviewed'] = False
        lifeDrain.deckBarManager.recover(False)
    lifeDrain.status['newCardState'] = False


def leech(card):
    '''
    Called when the card becomes a leech.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['newCardState'] = True


def bury(self, ids):
    '''
    Called when the card is buried.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['newCardState'] = True


def suspend(self, ids):
    '''
    Called when the card is suspended.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['newCardState'] = True


def delete(self, ids, notes=True):
    '''
    Called when the card is deleted.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['newCardState'] = True


def activateTimer():
    '''
    Activates the timer that reduces the bar.
    '''
    lifeDrain = getLifeDrain()
    if not lifeDrain.timer.isActive():
        lifeDrain.timer.start()


def newDeck():
    '''
    Called when a new deck is created.
    Updates the list of decks the manager knows.
    '''
    lifeDrain = getLifeDrain()
    for deckId in mw.col.decks.allIds():
        lifeDrain.deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))


def toggleTimer():
    '''
    Toggle the timer to pause/unpause the drain.
    '''
    lifeDrain = getLifeDrain()
    if lifeDrain.timer:
        if lifeDrain.timer.isActive():
            lifeDrain.timer.stop()
        else:
            lifeDrain.timer.start()


# Dealing with key presses is different in Anki 2.0 and 2.1
# This if/elif block deals with the differences
if appVersion.startswith('2.0'):
    def keyHandler(self, evt, _old):
        '''
        Appends 'p' shortcut to pause the drain.
        '''
        key = evt.text()
        if key == 'p':
            toggleTimer()
        else:
            _old(self, evt)

    Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, 'around')

elif appVersion.startswith('2.1'):
    def customShortcutKeys():
        '''
        Appends 'p' shortcut to pause the drain.
        '''
        lifeDrain = getLifeDrain()
        return lifeDrain.shortcutKeys

    lifeDrain = getLifeDrain()  # pylint: disable=invalid-name
    lifeDrain.shortcutKeys = mw.reviewer._shortcutKeys()
    lifeDrain.shortcutKeys.append(tuple(['p', toggleTimer]))
    mw.reviewer._shortcutKeys = customShortcutKeys


addHook('profileLoaded', profileLoaded)
addHook('afterStateChange', afterStateChange)
addHook('showQuestion', showQuestion)
addHook('showAnswer', showAnswer)
addHook('reset', undo)
addHook('leech', leech)
addHook('newDeck', newDeck)

Scheduler.buryNote = wrap(Scheduler.buryNote, bury)
Scheduler.buryCards = wrap(Scheduler.buryCards, bury)
Scheduler.suspendCards = wrap(Scheduler.suspendCards, suspend)
_Collection.remCards = wrap(_Collection.remCards, delete)
EditCurrent.__init__ = wrap(EditCurrent.__init__, onEdit)
