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

from anki.hooks import addHook, runHook, wrap
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
TEXT_FORMAT = [
    {'text': 'None'},
    {'text': 'current/total (XX%)', 'format': '%v/%m (%p%)'},
    {'text': 'current/total', 'format': '%v/%m'},
    {'text': 'current', 'format': '%v'},
    {'text': 'XX%', 'format': '%p%'},
    {'text': 'mm:ss', 'format': 'mm:ss'}
]
TEXT_OPTIONS = []
for text_format in TEXT_FORMAT:
    TEXT_OPTIONS.append(text_format['text'])

DEFAULTS = {
    'maxLife': 120,
    'recover': 5,
    'barPosition': POSITION_OPTIONS.index('Bottom'),
    'barHeight': 15,
    'barBgColor': '#f3f3f2',
    'barFgColor': '#489ef6',
    'barBorderRadius': 0,
    'barText': 0,
    'barTextColor': '#000',
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

    # Create deckBarManager, should run only once
    if lifeDrain.deckBarManager is None:
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
                'text': mw.col.conf.get('barText', DEFAULTS['barText']),
                'textColor': mw.col.conf.get('barTextColor', DEFAULTS['barTextColor']),
                'customStyle': mw.col.conf.get('barStyle', DEFAULTS['barStyle'])
            }
        }
        progressBar = AnkiProgressBar(config, DEFAULTS['maxLife'])
        progressBar.hide()
        lifeDrain.deckBarManager = DeckProgressBarManager(progressBar)

    if mw.col is not None:
        # Keep deck list always updated
        for deckId in mw.col.decks.allIds():
            lifeDrain.deckBarManager.addDeck(deckId, mw.col.decks.confForDid(deckId))

    return lifeDrain


def guiSettingsSetupLayout(widget):
    '''
    Sets up the layout used for the menus used in Life Drain.
    '''
    layout = qt.QGridLayout(widget)
    layout.setColumnStretch(0, 2)
    layout.setColumnStretch(1, 4)
    layout.setColumnStretch(2, 3)
    layout.setColumnStretch(3, 2)
    layout.setColumnMinimumWidth(2, 50)
    return layout


def createLabel(self, row, text):
    '''
    Creates a label that occupies the whole line and wraps if it is too big.
    '''
    label = qt.QLabel(text)
    label.setWordWrap(True)
    self.lifeDrainLayout.addWidget(label, row, 0, 1, 4)


def createComboBox(self, row, cbName, labelText, options):
    '''
    Creates a combo box with the specified label and options.
    '''
    label = qt.QLabel(labelText)
    setattr(self, cbName, qt.QComboBox(self.lifeDrainWidget))
    for option in options:
        getattr(self, cbName).addItem(option)
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(getattr(self, cbName), row, 2, 1, 2)


def createSpinBox(self, row, sbName, labelText, valRange):
    '''
    Creates a spin box with the specified label and range.
    '''
    label = qt.QLabel(labelText)
    setattr(self, sbName, qt.QSpinBox(self.lifeDrainWidget))
    getattr(self, sbName).setRange(valRange[0], valRange[1])
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(getattr(self, sbName), row, 2, 1, 2)


def createColorSelect(self, row, csName, labelText):
    '''
    Creates a color select with the specified label.
    '''
    label = qt.QLabel(labelText)
    selectButton = qt.QPushButton('Select')
    csPreviewName = '%sPreview' % csName
    csDialogName = '%sDialog' % csName
    setattr(self, csPreviewName, qt.QLabel(''))
    setattr(self, csDialogName, qt.QColorDialog(selectButton))
    selectButton.pressed.connect(
        lambda: selectColorDialog(getattr(self, csDialogName), getattr(self, csPreviewName))
    )
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(selectButton, row, 2)
    self.lifeDrainLayout.addWidget(getattr(self, csPreviewName), row, 3)


def fillRemainingSpace(self, row):
    '''
    Fills the remaining space, so what comes after this is in the bottom.
    '''
    spacer = qt.QSpacerItem(
        1, 1, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding
    )
    self.lifeDrainLayout.addItem(spacer, row, 0)


def globalSettingsLifeDrainTabUi(self, Preferences):
    '''
    Appends LifeDrain tab to Global Settings dialog.
    '''
    self.lifeDrainWidget = qt.QWidget()
    self.lifeDrainLayout = guiSettingsSetupLayout(self.lifeDrainWidget)
    row = 0
    createLabel(self, row, '<b>Life Drain Bar style</b>')
    row += 1
    createComboBox(self, row, 'positionList', 'Position', POSITION_OPTIONS)
    row += 1
    createSpinBox(self, row, 'heightInput', 'Height', [1, 40])
    row += 1
    createColorSelect(self, row, 'bgColor', 'Background color')
    row += 1
    createColorSelect(self, row, 'fgColor', 'Foreground color')
    row += 1
    createSpinBox(self, row, 'borderRadiusInput', 'Border radius', [0, 20])
    row += 1
    createComboBox(self, row, 'textList', 'Text', TEXT_OPTIONS)
    row += 1
    createColorSelect(self, row, 'textColor', 'Text color')
    row += 1
    createComboBox(self, row, 'styleList', 'Style*', STYLE_OPTIONS)
    row += 1
    createLabel(
        self, row,
        ' * Please keep in mind that some styles may not work well in some platforms!'
    )
    row += 1
    fillRemainingSpace(self, row)
    self.tabWidget.addTab(self.lifeDrainWidget, 'Life Drain')


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

    self.form.textList.setCurrentIndex(
        conf.get('barText', DEFAULTS['barText'])
    )

    self.form.textColorDialog.setCurrentColor(
        qt.QColor(conf.get('barTextColor', DEFAULTS['barTextColor']))
    )
    self.form.textColorPreview.setStyleSheet(
        'QLabel { background-color: %s; }'
        % self.form.textColorDialog.currentColor().name()
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
    conf['barText'] = self.form.textList.currentIndex()
    conf['barTextColor'] = self.form.textColorDialog.currentColor().name()
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
            'text': conf.get('barText', DEFAULTS['barText']),
            'textColor': conf.get('barTextColor', DEFAULTS['barTextColor']),
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
    self.lifeDrainWidget = qt.QWidget()
    self.lifeDrainLayout = guiSettingsSetupLayout(self.lifeDrainWidget)
    row = 0
    createLabel(
        self, row,
        'The <b>maximum life</b> is the time in seconds for the life bar go '
        'from full to empty.\n<b>Recover</b> is the time in seconds that is '
        'recovered after answering a card.'
    )
    row += 1
    createSpinBox(self, row, 'maxLifeInput', 'Maximum life', [1, 10000])
    row += 1
    createSpinBox(self, row, 'recoverInput', 'Recover', [0, 1000])
    row += 1
    createSpinBox(self, row, 'currentValueInput', 'Current life', [0, 10000])
    row += 1
    fillRemainingSpace(self, row)
    self.tabWidget.addTab(self.lifeDrainWidget, 'Life Drain')


def loadDeckConf(self):
    '''
    Loads LifeDrain deck configurations.
    '''
    lifeDrain = getLifeDrain()

    self.conf = self.mw.col.decks.confForDid(self.deck['id'])
    self.form.maxLifeInput.setValue(
        self.conf.get('maxLife', DEFAULTS['maxLife'])
    )
    self.form.recoverInput.setValue(
        self.conf.get('recover', DEFAULTS['recover'])
    )
    self.form.currentValueInput.setValue(
        lifeDrain.deckBarManager.getDeckConf(self.deck['id'])['currentValue']
    )


def saveDeckConf(self):
    '''
    Saves LifeDrain deck configurations.
    '''
    lifeDrain = getLifeDrain()

    self.conf['maxLife'] = self.form.maxLifeInput.value()
    self.conf['recover'] = self.form.recoverInput.value()
    self.conf['currentValue'] = self.form.currentValueInput.value()
    lifeDrain.deckBarManager.updateDeckConf(self.deck['id'], self.conf)


def customStudyLifeDrainUi(self, Dialog):
    '''
    Adds LifeDrain configurations to custom study dialog.
    '''
    self.lifeDrainWidget = qt.QGroupBox('Life Drain')
    self.lifeDrainLayout = guiSettingsSetupLayout(self.lifeDrainWidget)
    row = 0
    createSpinBox(self, row, 'maxLifeInput', 'Maximum life', [1, 10000])
    row += 1
    createSpinBox(self, row, 'recoverInput', 'Recover', [0, 1000])
    row += 1
    createSpinBox(self, row, 'currentValueInput', 'Current life', [0, 10000])
    row += 1
    index = 2 if appVersion.startswith('2.0') else 3
    self.verticalLayout.insertWidget(index, self.lifeDrainWidget)


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
    _textFormat = ''

    def __init__(self, config, maxValue):
        self._qProgressBar = qt.QProgressBar()
        self.setMaxValue(maxValue)
        self.resetBar()
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
        if self._textFormat == 'mm:ss':
            self._updateTimerText()

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
        if self._textFormat == 'mm:ss':
            self._updateTimerText()

    def incCurrentValue(self, increment):
        '''
        Increments the current value of the bar.
        Negative values will decrement.
        '''
        self._currentValue += increment
        self._validateUpdateCurrentValue()
        if self._textFormat == 'mm:ss':
            self._updateTimerText()

    def getCurrentValue(self):
        '''
        Gets the current value of the bar.
        '''
        return self._currentValue

    def setStyle(self, options):
        '''
        Sets the style of the bar.
        '''
        self._qProgressBar.setTextVisible(options['text'] != 0)  # 0 is the index of None
        textFormat = TEXT_FORMAT[options['text']]
        if 'format' in textFormat:
            self._textFormat = textFormat['format']
            self._qProgressBar.setFormat(textFormat['format'])

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
                    color: %s;
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
                    options['textColor'],
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

    def _updateTimerText(self):
        minutes = int(self._currentValue / 60)
        seconds = int(self._currentValue % 60)
        self._qProgressBar.setFormat('{0:01d}:{1:02d}'.format(minutes, seconds))

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
    _gameOver = False

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

    def getDeckConf(self, deckId):
        '''
        Get the settings and state of a deck.
        '''
        return self._barInfo[str(deckId)]

    def updateDeckConf(self, deckId, conf):
        '''
        Updates deck's current state.
        '''
        maxLife = conf.get('maxLife', DEFAULTS['maxLife'])
        recover = conf.get('recover', DEFAULTS['recover'])
        currentValue = conf.get('currentValue', DEFAULTS['maxLife'])
        if currentValue > maxLife:
            currentValue = maxLife

        self._barInfo[str(deckId)]['maxValue'] = maxLife
        self._barInfo[str(deckId)]['recoverValue'] = recover
        self._barInfo[str(deckId)]['currentValue'] = currentValue

    def updateAnkiProgressBar(self, ankiProgressBar):
        '''
        Updates the AnkiProgressBar instance.
        '''
        del self._ankiProgressBar
        self._ankiProgressBar = ankiProgressBar

    def recover(self, increment=True, value=None):
        '''
        Abstraction for recovering life, increments the bar if increment is True (default).
        '''
        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            value = self._barInfo[self._currentDeck]['recoverValue']

        self._ankiProgressBar.incCurrentValue(multiplier * value)

        life = self._ankiProgressBar.getCurrentValue()
        self._barInfo[self._currentDeck]['currentValue'] = life
        if life == 0 and not self._gameOver:
            self._gameOver = True
            runHook('LifeDrain.gameOver')
        elif life > 0:
            self._gameOver = False

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
    lifeDrain.deckBarManager.recover(False, 1)


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

    if state == 'deckBrowser':
        lifeDrain.deckBarManager.getBar().hide()
        lifeDrain.deckBarManager.setDeck(None)
    else:
        if mw.col is not None:
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
    def _addShortcut(shortcuts):
        '''
        Appends 'p' shortcut to pause the drain.
        '''
        shortcuts.append(tuple(['p', toggleTimer]))

    addHook('reviewStateShortcuts', _addShortcut)


addHook('afterStateChange', afterStateChange)
addHook('showQuestion', showQuestion)
addHook('showAnswer', showAnswer)
addHook('reset', undo)
addHook('leech', leech)

Scheduler.buryNote = wrap(Scheduler.buryNote, bury)
Scheduler.buryCards = wrap(Scheduler.buryCards, bury)
Scheduler.suspendCards = wrap(Scheduler.suspendCards, suspend)
_Collection.remCards = wrap(_Collection.remCards, delete)
EditCurrent.__init__ = wrap(EditCurrent.__init__, onEdit)
