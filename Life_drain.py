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
from aqt.qt import *
from aqt import mw, forms
from aqt.progress import ProgressManager
from aqt.reviewer import Reviewer
from aqt.deckconf import DeckConf
from aqt.preferences import Preferences

from aqt.utils import showInfo


## Bar design configuration ##

# Position: 'top' or 'bottom'

# CustomStyle:
# 'default' to use a simple bar
#
# Other options are also available:
# 'plastique', 'windowsxp', 'windows', 'windowsvista', 'motif', 'cde', 'cleanlooks'
# 'macintosh', 'gtk', 'fusion', 'windowsvista'
# Check more on http://doc.qt.io/qt-4.8/gallery.html

config = {
    'position': 'bottom',
    'progressBarStyle': {
        'height': 17,
        'backgroundColor': '#222222',
        'foregroundColor': '#666666',
        'borderRadius': 0,
        'customStyle': 'default'
    }
}

## End configuration ##


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
    self.positionList.addItem('Top')
    self.positionList.addItem('Bottom')
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
    self.styleList.addItem('Default')
    self.styleList.addItem('Cde')
    self.styleList.addItem('Cleanlooks')
    self.styleList.addItem('Fusion')
    self.styleList.addItem('Gtk')
    self.styleList.addItem('Macintosh')
    self.styleList.addItem('Motif')
    self.styleList.addItem('Plastique')
    self.styleList.addItem('Windows')
    self.styleList.addItem('Windows Vista')
    self.styleList.addItem('Windows XP')
    layout.addWidget(styleLabel, row, 0)
    layout.addWidget(self.styleList, row, 1, 1, 2)
    row += 1

    hideSeparatorStripLabel = QLabel('Hide separator**')
    self.hideSeparatorStripCheckBox = QCheckBox(tabWidget)
    layout.addWidget(hideSeparatorStripLabel, row, 0)
    layout.addWidget(self.hideSeparatorStripCheckBox, row, 1, 1, 2)
    row += 1

    descriptionLabel = QLabel('*  Please keep in mind that some styles may not work well with another configurations!')
    descriptionLabel.setWordWrap(True)
    layout.addWidget(descriptionLabel, row, 0, 1, 4)
    row += 1

    descriptionLabel2 = QLabel('** If while using other addons you find problems with the separator strip being hidden, uncheck this. Usually you will want this checked.')
    descriptionLabel2.setWordWrap(True)
    layout.addWidget(descriptionLabel2, row, 0, 1, 4)
    row += 1

    spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout.addItem(spacer, row, 0)

    self.tabWidget.addTab(tabWidget, "Life Drain")

def selectColorDialog(qColorDialog, previewLabel):
    if qColorDialog.exec_():
        previewLabel.setStyleSheet('QLabel { background-color: %s; }' % qColorDialog.currentColor().name())

def globalLoadConf(self, mw):
    conf = self.mw.col.conf
    self.form.positionList.setCurrentIndex(conf.get('barPosition', 1))
    self.form.heightInput.setValue(conf.get('barHeight', 17))

    self.form.bgColorDialog.setCurrentColor(QColor(conf.get('barBgColor', '#222222')))
    self.form.bgColorPreview.setStyleSheet('QLabel { background-color: %s; }' % self.form.bgColorDialog.currentColor().name())

    self.form.fgColorDialog.setCurrentColor(QColor(conf.get('barFgColor', '#666666')))
    self.form.fgColorPreview.setStyleSheet('QLabel { background-color: %s; }' % self.form.fgColorDialog.currentColor().name())

    self.form.borderRadiusInput.setValue(conf.get('barBorderRadius', 0))
    self.form.styleList.setCurrentIndex(conf.get('barStyle', 0))
    self.form.hideSeparatorStripCheckBox.setChecked(conf.get('hideSeparator', True))

def globalSaveConf(self):
    conf = self.mw.col.conf

forms.preferences.Ui_Preferences.setupUi = wrap(forms.preferences.Ui_Preferences.setupUi, globalSettingsLifeDrainTabUi, pos='after')
Preferences.__init__ = wrap(Preferences.__init__, globalLoadConf, pos='after')
Preferences.accept = wrap(Preferences.accept, globalSaveConf, pos='before')


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

def deckLoadConf(self):
    self.conf = self.mw.col.decks.confForDid(self.deck['id'])
    self.form.maxLifeInput.setValue(self.conf.get('maxLife', 120))
    self.form.recoverInput.setValue(self.conf.get('recover', 5))

def deckSaveConf(self):
    global deckBarManager
    self.conf['maxLife'] = self.form.maxLifeInput.value()
    self.conf['recover'] = self.form.recoverInput.value()
    deckBarManager.updateDeckConf(self.deck['id'], self.conf)

forms.dconf.Ui_Dialog.setupUi = wrap(forms.dconf.Ui_Dialog.setupUi, deckSettingsLifeDrainTabUi, pos='after')
DeckConf.loadConf = wrap(DeckConf.loadConf, deckLoadConf)
DeckConf.saveConf = wrap(DeckConf.saveConf, deckSaveConf, pos='before')


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
        if (options['customStyle'] != 'default'):
            palette = QPalette()
            palette.setColor(QPalette.Base, QColor(options['backgroundColor']))
            palette.setColor(QPalette.Highlight, QColor(options['foregroundColor']))
            palette.setColor(QPalette.Button, QColor(options['backgroundColor']))
            palette.setColor(QPalette.Window, QColor(options['backgroundColor']))

            self._qProgressBar.setStyle(QStyleFactory.create(options['customStyle']))
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
        '''
        - Valid place values: top, bottom
        Default to bottom
        '''
        if (place not in ['top', 'bottom']):
            place = 'bottom'

        if (place == 'top'):
            dockArea = Qt.TopDockWidgetArea
        elif (place == 'bottom'):
            dockArea = Qt.BottomDockWidgetArea

        dock = QDockWidget()
        tWidget = QWidget()
        dock.setWidget(self._qProgressBar)
        dock.setTitleBarWidget(tWidget)

        existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]
        if (len(existing_widgets) == 0):
            mw.addDockWidget(dockArea, dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existing_widgets[0], dock, Qt.Vertical)
        mw.web.setFocus()


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
        self._barInfo[str(deckId)] = {
            'maxValue': conf.get('maxLife', 120),
            'currentValue': conf.get('maxLife', 120),
            'recoverValue': conf.get('recover', 5)
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
        self._barInfo[str(deckId)]['maxValue'] = conf.get('maxLife', 120)
        self._barInfo[str(deckId)]['recoverValue'] = conf.get('recover', 5)

    def recover(self, increment=True):
        multiplier = 1
        if not increment:
            multiplier = -1
        self._ankiProgressBar.incCurrentValue(multiplier * self._barInfo[self._currentDeck]['recoverValue'])

    def getBar(self):
        return self._ankiProgressBar


# Remove separator strip
separatorStripCss = '''
    QMainWindow::separator {
        width: 0px;
        height: 0px;
    }
'''
try:
    import Night_Mode
    Night_Mode.nm_css_menu += separatorStripCss
    if (not Night_Mode.nm_state_on):
        mw.setStyleSheet(separatorStripCss)
except ImportError:
    mw.setStyleSheet(separatorStripCss)


deckBarManager = None
timer = None
status = {
    'reviewed': False,
    'screen': None
}

def timerTrigger():
    global deckBarManager
    deckBarManager.getBar().incCurrentValue(-1)

def profileLoaded():
    global deckBarManager, config
    progressBar = AnkiProgressBar(config, 120)
    deckBarManager = DeckProgressBarManager(progressBar)
    for deckId in mw.col.decks.allIds():
        deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))
    progressBar.hide()

def afterStateChange(state, oldState):
    global deckBarManager, config, timer, status

    if not timer:
        timer = ProgressManager(mw).timer(1000, timerTrigger, True)
    timer.stop()

    if (status['reviewed'] and state in ['overview', 'review']):
        deckBarManager.recover()
    status['reviewed'] = False
    status['screen'] = state

    if state in ['overview', 'review']:
        deckBarManager.setDeck(mw.col.decks.current()['id'])
        deckBarManager.getBar().show()
    elif deckBarManager:
        deckBarManager.getBar().hide()
        deckBarManager.setDeck(None)

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

def reset():
    global deckBarManager, config, status
    status['reviewed'] = False
    if (status['screen'] == 'review'):
        activateTimer()
        deckBarManager.recover(False)

def activateTimer():
    global timer
    if not timer.isActive():
        timer.start()

def keyHandler(self, evt, _old):
    '''
    Add the P shortcut for pausing/unpausing the drain.
    '''
    global timer
    key = unicode(evt.text())
    if key == 'p' and timer:
        if (timer.isActive()):
            timer.stop()
        else:
            timer.start()
    else:
        return _old(self, evt)

Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, 'around')


addHook('profileLoaded', profileLoaded)
addHook('afterStateChange', afterStateChange)
addHook('showQuestion', showQuestion)
addHook('showAnswer', showAnswer)
addHook('reset', reset)

