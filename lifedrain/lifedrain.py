"""
Anki Add-on: Life Drain
Add a bar that is reduced as time passes. Completing reviews recovers life.

**
Some of the code (progress bar) used here was originally done by Glutanimate, from the
Addon Progress Bar. So I copied the copyright from that Addon and appended my name.
**

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
            (c) Yutsuten 2018 <https://github.com/Yutsuten>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from anki.hooks import addHook, wrap
from anki.sched import Scheduler
from anki.collection import _Collection
from aqt.qt import *
from aqt import mw, forms, appVersion
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.deckconf import DeckConf
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


# Settings GUI
def globalSettingsLifeDrainTabUi(self, Preferences):
    tabWidget = QWidget()
    layout = QGridLayout(tabWidget)
    layout.setColumnStretch(0, 3)
    layout.setColumnStretch(3, 1)
    layout.setColumnMinimumWidth(2, 50)
    row = 0

    title = QLabel('<b>Life Drain Bar style</b>')
    layout.addWidget(title, row, 0, 1, 3)
    row += 1

    positionLabel = QLabel('Position')
    self.positionList = QComboBox(tabWidget)
    for position in POSITION_OPTIONS:
        self.positionList.addItem(position)
    layout.addWidget(positionLabel, row, 0)
    layout.addWidget(self.positionList, row, 1, 1, 2)
    row += 1

    heightLabel = QLabel('Height')
    self.heightInput = QSpinBox(tabWidget)
    self.heightInput.setRange(1, 40)
    layout.addWidget(heightLabel, row, 0)
    layout.addWidget(self.heightInput, row, 1, 1, 2)
    row += 1

    bgLabel = QLabel('Background color')
    self.bgColorPreview = QLabel('')
    bgSelectButton = QPushButton('Select')
    self.bgColorDialog = QColorDialog(bgSelectButton)
    bgSelectButton.pressed.connect(lambda: selectColorDialog(self.bgColorDialog, self.bgColorPreview))
    layout.addWidget(bgLabel, row, 0)
    layout.addWidget(bgSelectButton, row, 1)
    layout.addWidget(self.bgColorPreview, row, 2)
    row += 1

    fgLabel = QLabel('Foreground color')
    self.fgColorPreview = QLabel('')
    fgSelectButton = QPushButton('Select')
    self.fgColorDialog = QColorDialog(fgSelectButton)
    fgSelectButton.pressed.connect(lambda: selectColorDialog(self.fgColorDialog, self.fgColorPreview))
    layout.addWidget(fgLabel, row, 0)
    layout.addWidget(fgSelectButton, row, 1)
    layout.addWidget(self.fgColorPreview, row, 2)
    row += 1

    borderRadiusLabel = QLabel('Border radius')
    self.borderRadiusInput = QSpinBox(tabWidget)
    self.borderRadiusInput.setRange(0, 20)
    layout.addWidget(borderRadiusLabel, row, 0)
    layout.addWidget(self.borderRadiusInput, row, 1, 1, 2)
    row += 1

    styleLabel = QLabel('Style*')
    self.styleList = QComboBox(tabWidget)
    for customStyle in STYLE_OPTIONS:
        self.styleList.addItem(customStyle)
    layout.addWidget(styleLabel, row, 0)
    layout.addWidget(self.styleList, row, 1, 1, 2)
    row += 1

    descriptionLabel = QLabel('* Please keep in mind that some styles may not work well in some platforms!')
    descriptionLabel.setWordWrap(True)
    layout.addWidget(descriptionLabel, row, 0, 1, 4)
    row += 1

    spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout.addItem(spacer, row, 0)

    self.tabWidget.addTab(tabWidget, "Life Drain")

def selectColorDialog(qColorDialog, previewLabel):
    if qColorDialog.exec_():
        previewLabel.setStyleSheet('QLabel { background-color: %s; }' % qColorDialog.currentColor().name())

def globalLoadConf(self, mw):
    conf = self.mw.col.conf
    self.form.positionList.setCurrentIndex(conf.get('barPosition', DEFAULTS['barPosition']))
    self.form.heightInput.setValue(conf.get('barHeight', DEFAULTS['barHeight']))

    self.form.bgColorDialog.setCurrentColor(QColor(conf.get('barBgColor', DEFAULTS['barBgColor'])))
    self.form.bgColorPreview.setStyleSheet('QLabel { background-color: %s; }' % self.form.bgColorDialog.currentColor().name())

    self.form.fgColorDialog.setCurrentColor(QColor(conf.get('barFgColor', DEFAULTS['barFgColor'])))
    self.form.fgColorPreview.setStyleSheet('QLabel { background-color: %s; }' % self.form.fgColorDialog.currentColor().name())

    self.form.borderRadiusInput.setValue(conf.get('barBorderRadius', DEFAULTS['barBorderRadius']))
    self.form.styleList.setCurrentIndex(conf.get('barStyle', DEFAULTS['barStyle']))

def globalSaveConf(self):
    global deckBarManager, config
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
            'borderRadius': conf.get('barBorderRadius', DEFAULTS['barBorderRadius']),
            'customStyle': conf.get('barStyle', DEFAULTS['barStyle'])
        }
    }
    progressBar = AnkiProgressBar(config, deckBarManager.getBar().getCurrentValue())
    deckBarManager.updateAnkiProgressBar(progressBar)

forms.preferences.Ui_Preferences.setupUi = wrap(forms.preferences.Ui_Preferences.setupUi, globalSettingsLifeDrainTabUi)
Preferences.__init__ = wrap(Preferences.__init__, globalLoadConf)
Preferences.accept = wrap(Preferences.accept, globalSaveConf, 'before')


# Deck settings GUI
def deckSettingsLifeDrainTabUi(self, Dialog):
    tabWidget = QWidget()
    layout = QGridLayout(tabWidget)
    row = 0

    title = QLabel('<b>Life Drain Bar settings</b>')
    layout.addWidget(title, row, 0, 1, 3)
    row += 1

    descriptionLabel = QLabel('The <b>maximum life</b> is the time in seconds for the life bar go from full to empty.\n<b>Recover</b> is the time in seconds that is recovered after answering a card.')
    descriptionLabel.setWordWrap(True)
    layout.addWidget(descriptionLabel, row, 0, 1, 3)
    row += 1

    maxLifeLabel = QLabel('Maximum life')
    self.maxLifeInput = QSpinBox(tabWidget)
    self.maxLifeInput.setRange(1, 1000)
    layout.addWidget(maxLifeLabel, row, 0)
    layout.addWidget(self.maxLifeInput, row, 2)
    row += 1

    recoverLabel = QLabel('Recover')
    self.recoverInput = QSpinBox(tabWidget)
    self.recoverInput.setRange(1, 1000)
    layout.addWidget(recoverLabel, row, 0)
    layout.addWidget(self.recoverInput, row, 2)
    row += 1

    spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout.addItem(spacer, row, 0)

    self.tabWidget.addTab(tabWidget, "Life Drain")

def loadDeckConf(self):
    self.conf = self.mw.col.decks.confForDid(self.deck['id'])
    self.form.maxLifeInput.setValue(self.conf.get('maxLife', DEFAULTS['maxLife']))
    self.form.recoverInput.setValue(self.conf.get('recover', DEFAULTS['recover']))

def saveDeckConf(self):
    global deckBarManager
    self.conf['maxLife'] = self.form.maxLifeInput.value()
    self.conf['recover'] = self.form.recoverInput.value()
    deckBarManager.updateDeckConf(self.deck['id'], self.conf)

forms.dconf.Ui_Dialog.setupUi = wrap(forms.dconf.Ui_Dialog.setupUi, deckSettingsLifeDrainTabUi)
DeckConf.loadConf = wrap(DeckConf.loadConf, loadDeckConf)
DeckConf.saveConf = wrap(DeckConf.saveConf, saveDeckConf, 'before')


# Edit during review
def onEdit(*args):
    global status
    status['reviewed'] = False

EditCurrent.__init__ = wrap(EditCurrent.__init__, onEdit)


class AnkiProgressBar(object):
    _qProgressBar = None
    _maxValue = 1
    _currentValue = 1

    def __init__(self, config, maxValue):
        self._qProgressBar = QProgressBar()
        self.setMaxValue(maxValue)
        self.resetBar()
        self.setTextVisible(False)
        self.setStyle(config['progressBarStyle'])
        self._dockAt(config['position'])

    def show(self):
        self._qProgressBar.show()

    def hide(self):
        self._qProgressBar.hide()

    def resetBar(self):
        self._currentValue = self._maxValue
        self._validateUpdateCurrentValue()

    def setMaxValue(self, maxValue):
        self._maxValue = maxValue
        if (self._maxValue <= 0):
            self._maxValue = 1
        self._qProgressBar.setRange(0, self._maxValue)

    def setCurrentValue(self, currentValue):
        self._currentValue = currentValue
        self._validateUpdateCurrentValue()

    def incCurrentValue(self, increment):
        self._currentValue += increment
        self._validateUpdateCurrentValue()

    def getCurrentValue(self):
        return self._currentValue

    def setTextVisible(self, flag):
        self._qProgressBar.setTextVisible(flag)

    def setStyle(self, options):
        global STYLE_OPTIONS
        customStyle = STYLE_OPTIONS[options['customStyle']].replace(" ", "").lower()
        if (customStyle != 'default'):
            palette = QPalette()
            palette.setColor(QPalette.Base, QColor(options['backgroundColor']))
            palette.setColor(QPalette.Highlight, QColor(options['foregroundColor']))
            palette.setColor(QPalette.Button, QColor(options['backgroundColor']))
            palette.setColor(QPalette.Window, QColor(options['backgroundColor']))

            self._qProgressBar.setStyle(QStyleFactory.create(customStyle))
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
        if (self._currentValue > self._maxValue):
            self._currentValue = self._maxValue
        elif (self._currentValue < 0):
            self._currentValue = 0
        self._qProgressBar.setValue(self._currentValue)

    def _dockAt(self, place):
        global POSITION_OPTIONS
        place = POSITION_OPTIONS[place]

        if place not in POSITION_OPTIONS:
            place = DEFAULTS['barPosition']

        if (place == 'Top'):
            dockArea = Qt.TopDockWidgetArea
        elif (place == 'Bottom'):
            dockArea = Qt.BottomDockWidgetArea

        self._dock = QDockWidget()
        tWidget = QWidget()
        self._dock.setWidget(self._qProgressBar)
        self._dock.setTitleBarWidget(tWidget)

        existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]
        if (len(existing_widgets) == 0):
            mw.addDockWidget(dockArea, self._dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existing_widgets[0], self._dock, Qt.Vertical)
        mw.web.setFocus()

    def __del__(self):
        self._dock.close()


class DeckProgressBarManager(object):
    '''
    Allow using the same instance of AnkiProgressBar with different configuration and
    currentValue for each deck.
    '''
    _ankiProgressBar = None
    _barInfo = {}
    _currentDeck = None

    def __init__(self, ankiProgressBar):
        self._ankiProgressBar = ankiProgressBar

    def addDeck(self, deckId, conf):
        if str(deckId) not in self._barInfo:
            self._barInfo[str(deckId)] = {
                'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'recoverValue': conf.get('recover', DEFAULTS['recover'])
            }

    def setDeck(self, deckId):
        if self._currentDeck:
            self._barInfo[self._currentDeck]['currentValue'] = self._ankiProgressBar.getCurrentValue()
        if deckId:
            self._currentDeck = str(deckId)
            self._ankiProgressBar.setMaxValue(self._barInfo[self._currentDeck]['maxValue'])
            self._ankiProgressBar.setCurrentValue(self._barInfo[self._currentDeck]['currentValue'])
        else:
            self._currentDeck = None

    def updateDeckConf(self, deckId, conf):
        self._barInfo[str(deckId)]['maxValue'] = conf.get('maxLife', DEFAULTS['maxLife'])
        self._barInfo[str(deckId)]['recoverValue'] = conf.get('recover', DEFAULTS['recover'])

    def updateAnkiProgressBar(self, ankiProgressBar):
        del(self._ankiProgressBar)
        self._ankiProgressBar = ankiProgressBar

    def recover(self, increment=True):
        multiplier = 1
        if not increment:
            multiplier = -1
        self._ankiProgressBar.incCurrentValue(multiplier * self._barInfo[self._currentDeck]['recoverValue'])

    def getBar(self):
        return self._ankiProgressBar


# Remove separator strip
separatorStripCss = 'QMainWindow::separator { width: 0px; height: 0px; }'
try:
    import Night_Mode
    Night_Mode.nm_css_menu += separatorStripCss
    if (not Night_Mode.nm_state_on):
        mw.setStyleSheet(separatorStripCss)
except ImportError:
    mw.setStyleSheet(separatorStripCss)


config = {}
deckBarManager = None
timer = None
status = {
    'reviewed': False,
    'newCardState': False,
    'screen': None
}

def timerTrigger():
    global deckBarManager
    deckBarManager.getBar().incCurrentValue(-1)

def profileLoaded():
    global deckBarManager, config

    config = {
        'position': mw.col.conf.get('barPosition', DEFAULTS['barPosition']),
        'progressBarStyle': {
            'height': mw.col.conf.get('barHeight', DEFAULTS['barHeight']),
            'backgroundColor': mw.col.conf.get('barBgColor', DEFAULTS['barBgColor']),
            'foregroundColor': mw.col.conf.get('barFgColor', DEFAULTS['barFgColor']),
            'borderRadius': mw.col.conf.get('barBorderRadius', DEFAULTS['barBorderRadius']),
            'customStyle': mw.col.conf.get('barStyle', DEFAULTS['barStyle'])
        }
    }
    progressBar = AnkiProgressBar(config, DEFAULTS['maxLife'])
    progressBar.hide()
    deckBarManager = DeckProgressBarManager(progressBar)
    for deckId in mw.col.decks.allIds():
        deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))

def afterStateChange(state, oldState):
    global deckBarManager, config, timer, status

    if not timer:
        timer = ProgressManager(mw).timer(1000, timerTrigger, True)
    timer.stop()

    if (status['reviewed'] and state in ['overview', 'review']):
        deckBarManager.recover()
    status['reviewed'] = False
    status['screen'] = state

    if deckBarManager:
        if state == 'deckBrowser':
            deckBarManager.getBar().hide()
            deckBarManager.setDeck(None)
        else:
            deckBarManager.setDeck(mw.col.decks.current()['id'])
            deckBarManager.getBar().show()

    if state == 'review':
        timer.start()

def showQuestion():
    global deckBarManager, config, status
    activateTimer()
    if (status['reviewed']):
        deckBarManager.recover()

def showAnswer():
    global status
    activateTimer()
    status['reviewed'] = True

def undo():
    global deckBarManager, status
    if (status['screen'] == 'review' and not status['newCardState']):
        activateTimer()
        status['reviewed'] = False
        deckBarManager.recover(False)
    status['newCardState'] = False

def leech(card):
    global status
    status['newCardState'] = True

def bury(self, ids):
    global status
    status['newCardState'] = True

def suspend(self, ids):
    global status
    status['newCardState'] = True

def delete(self, ids, notes=True):
    global status
    status['newCardState'] = True

def activateTimer():
    global timer
    if not timer.isActive():
        timer.start()

def newDeck():
    for deckId in mw.col.decks.allIds():
        deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))

def toggleTimer():
    global timer
    if timer:
        if (timer.isActive()):
            timer.stop()
        else:
            timer.start()

# Dealing with key presses is different in Anki 2.0 and 2.1
# This if/elif block deals with the differences
if appVersion.startswith('2.0'):
    def keyHandler(self, evt, _old):
        key = unicode(evt.text())
        if key == 'p':
            toggleTimer()
        else:
            return _old(self, evt)

    Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, 'around')

elif appVersion.startswith('2.1'):
    def _shortcutKeys():
        global shortcutKeys
        return shortcutKeys

    shortcutKeys = mw.reviewer._shortcutKeys()
    shortcutKeys.append(tuple(['p', toggleTimer]))
    mw.reviewer._shortcutKeys = _shortcutKeys


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

