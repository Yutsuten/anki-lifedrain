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
            (c) Al Beano 2019 <https://github.com/whiteisthenewblack>
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

from .anki_progress_bar import AnkiProgressBar
from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_OPTIONS, DEFAULTS


# Hide separator strip
mw.setStyleSheet('QMainWindow::separator { width: 0px; height: 0px; }')


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
        'screen': None,
        'reviewResponse': 0
    }
    stopOnAnswer = False
    disable = None


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

    if mw.col is not None:
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
            lifeDrain.disable = mw.col.conf.get('disable', DEFAULTS['disable'])
            lifeDrain.stopOnAnswer = mw.col.conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

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


def createLabel(self, row, text, color=None):
    '''
    Creates a label that occupies the whole line and wraps if it is too big.
    '''
    label = qt.QLabel(text)
    label.setWordWrap(True)
    self.lifeDrainLayout.addWidget(label, row, 0, 1, 4)
    if color:
        label.setStyleSheet('color: {}'.format(color))


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


def createCheckBox(self, row, cbName, labelText):
    '''
    Creates a checkbox with the specified label.
    '''
    label = qt.QLabel(labelText)
    setattr(self, cbName, qt.QCheckBox(self.lifeDrainWidget))
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
    getattr(self, csDialogName).setOption(qt.QColorDialog.DontUseNativeDialog)
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
    createLabel(self, row, '<b>Bar behaviour</b>')
    row += 1
    createCheckBox(self, row, 'stopOnAnswer', 'Stop drain on answer shown')
    row += 1
    createCheckBox(self, row, 'disableAddon', 'Disable Life Drain (!)')
    row += 1
    createLabel(self, row, '<b>Bar style</b>')
    row += 1
    createComboBox(self, row, 'positionList', 'Position', POSITION_OPTIONS)
    row += 1
    createSpinBox(self, row, 'heightInput', 'Height', [1, 40])
    row += 1
    createSpinBox(self, row, 'borderRadiusInput', 'Border radius', [0, 20])
    row += 1
    createComboBox(self, row, 'textList', 'Text', TEXT_OPTIONS)
    row += 1
    createComboBox(self, row, 'styleList', 'Style', STYLE_OPTIONS)
    row += 1
    createColorSelect(self, row, 'bgColor', 'Background color')
    row += 1
    createColorSelect(self, row, 'fgColor', 'Foreground color')
    row += 1
    createColorSelect(self, row, 'textColor', 'Text color')
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

    self.form.stopOnAnswer.setChecked(
        conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer']))

    self.form.disableAddon.setChecked(
        conf.get('disable', DEFAULTS['disable'])
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
    conf['stopOnAnswer'] = self.form.stopOnAnswer.isChecked()
    conf['disable'] = self.form.disableAddon.isChecked()

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
    lifeDrain.deckBarManager.setAnkiProgressBarStyle(config)
    lifeDrain.disable = conf.get('disable', DEFAULTS['disable'])
    lifeDrain.stopOnAnswer = conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])


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
        'recovered after answering a card. <b>Damage</b> is the life lost '
        'when a card is answered with \'Again\'.'
    )
    row += 1
    createSpinBox(self, row, 'maxLifeInput', 'Maximum life', [1, 10000])
    row += 1
    createSpinBox(self, row, 'recoverInput', 'Recover', [0, 1000])
    row += 1
    createCheckBox(self, row, 'enableDamageInput', 'Enable damage')
    row += 1
    createSpinBox(self, row, 'damageInput', 'Damage', [-1000, 1000])
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
    self.form.enableDamageInput.setChecked(
        self.conf.get('enableDamage', DEFAULTS['enableDamage'])
    )
    self.form.damageInput.setValue(
        self.conf.get('damage', DEFAULTS['damage'])
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
    self.conf['enableDamage'] = self.form.enableDamageInput.isChecked()
    self.conf['damage'] = self.form.damageInput.value()
    lifeDrain.deckBarManager.setDeckConf(self.deck['id'], self.conf)


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
    createCheckBox(self, row, 'enableDamageInput', 'Enable damage')
    row += 1
    createSpinBox(self, row, 'damageInput', 'Damage', [-1000, 1000])
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
                'recoverValue': conf.get('recover', DEFAULTS['recover']),
                'enableDamageValue': conf.get('enableDamage', DEFAULTS['enableDamage']),
                'damageValue': conf.get('damage', DEFAULTS['damage'])
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

    def setDeckConf(self, deckId, conf):
        '''
        Updates deck's current state.
        '''
        maxLife = conf.get('maxLife', DEFAULTS['maxLife'])
        recover = conf.get('recover', DEFAULTS['recover'])
        enableDamage = conf.get('enableDamage', DEFAULTS['enableDamage'])
        damage = conf.get('damage', DEFAULTS['damage'])
        currentValue = conf.get('currentValue', DEFAULTS['maxLife'])
        if currentValue > maxLife:
            currentValue = maxLife

        self._barInfo[str(deckId)]['maxValue'] = maxLife
        self._barInfo[str(deckId)]['recoverValue'] = recover
        self._barInfo[str(deckId)]['enableDamageValue'] = enableDamage
        self._barInfo[str(deckId)]['damageValue'] = damage
        self._barInfo[str(deckId)]['currentValue'] = currentValue

    def setAnkiProgressBarStyle(self, config=None):
        '''
        Updates the AnkiProgressBar instance.
        '''
        pbStyle = {
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

        if config is not None:
            if 'position' in config:
                self._ankiProgressBar.dockAt(config['position'])
            if 'progressBarStyle' in config:
                pbStyle.update(config['progressBarStyle'])

        self._ankiProgressBar.setStyle(pbStyle)
        if self._currentDeck is not None:
            self.recover(value=0)

    def recover(self, increment=True, value=None, damage=False):
        '''
        Abstraction for recovering life, increments the bar if increment is True (default).
        '''
        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and self._barInfo[self._currentDeck]['enableDamageValue']:
                multiplier = -1
                value = self._barInfo[self._currentDeck]['damageValue']
            else:
                value = self._barInfo[self._currentDeck]['recoverValue']

        self._ankiProgressBar.incCurrentValue(multiplier * value)

        life = self._ankiProgressBar.getCurrentValue()
        self._barInfo[self._currentDeck]['currentValue'] = life
        if life == 0 and not self._gameOver:
            self._gameOver = True
            runHook('LifeDrain.gameOver')
        elif life > 0:
            self._gameOver = False

    def barVisible(self, visible):
        '''
        Sets the visibility of the Progress Bar
        '''
        if visible:
            self._ankiProgressBar.show()
        else:
            self._ankiProgressBar.hide()


# Night Mode integration begin
try:
    import Night_Mode
    Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
except Exception:  # nosec  # pylint: disable=broad-except
    pass
# Night Mode integration end


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

    if not lifeDrain.disable:  # Enabled
        if not lifeDrain.timer:
            lifeDrain.timer = ProgressManager(mw).timer(100, timerTrigger, True)
        lifeDrain.timer.stop()

        if lifeDrain.status['reviewed'] and state in ['overview', 'review']:
            lifeDrain.deckBarManager.recover()
        lifeDrain.status['reviewed'] = False
        lifeDrain.status['screen'] = state

        if state == 'deckBrowser':
            lifeDrain.deckBarManager.barVisible(False)
            lifeDrain.deckBarManager.setDeck(None)
        else:
            if mw.col is not None:
                lifeDrain.deckBarManager.setDeck(mw.col.decks.current()['id'])
            lifeDrain.deckBarManager.barVisible(True)

        if state == 'review':
            lifeDrain.timer.start()

    else:  # Disabled
        lifeDrain.deckBarManager.barVisible(False)
        if lifeDrain.timer is not None:
            lifeDrain.timer.stop()


def showQuestion():
    '''
    Called when a question is shown.
    '''
    lifeDrain = getLifeDrain()

    if not lifeDrain.disable:
        activateTimer()
        if lifeDrain.status['reviewed']:
            if lifeDrain.status['reviewResponse'] == 1:
                lifeDrain.deckBarManager.recover(damage=True)
            else:
                lifeDrain.deckBarManager.recover()
        lifeDrain.status['reviewed'] = False
        lifeDrain.status['newCardState'] = False


def showAnswer():
    '''
    Called when an answer is shown.
    '''
    lifeDrain = getLifeDrain()

    if not lifeDrain.disable:
        if lifeDrain.stopOnAnswer:
            deactivateTimer()
        else:
            activateTimer()
        lifeDrain.status['reviewed'] = True


def undo():
    '''
    Deals with undoing.
    '''
    lifeDrain = getLifeDrain()

    if not lifeDrain.disable:
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
    if not lifeDrain.disable and lifeDrain.timer is not None and not lifeDrain.timer.isActive():
        lifeDrain.timer.start()


def deactivateTimer():
    '''
    Deactivates the timer that reduces the bar.
    '''
    lifeDrain = getLifeDrain()
    if not lifeDrain.disable and lifeDrain.timer is not None and lifeDrain.timer.isActive():
        lifeDrain.timer.stop()


def toggleTimer():
    '''
    Toggle the timer to pause/unpause the drain.
    '''
    lifeDrain = getLifeDrain()
    if not lifeDrain.disable and lifeDrain.timer is not None:
        if lifeDrain.timer.isActive():
            lifeDrain.timer.stop()
        else:
            lifeDrain.timer.start()


def recover(increment=True, value=None, damage=False):
    '''
    Method ran when invoking 'LifeDrain.recover' hook.
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.deckBarManager.recover(increment, value, damage)


def answerCard(self, resp):
    '''
    Called when a card is answered
    '''
    lifeDrain = getLifeDrain()
    lifeDrain.status['reviewResponse'] = resp


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
addHook('revertedCard', lambda cid: undo())
addHook('leech', leech)
addHook('LifeDrain.recover', recover)

Scheduler.buryNote = wrap(Scheduler.buryNote, bury)
Scheduler.buryCards = wrap(Scheduler.buryCards, bury)
Scheduler.suspendCards = wrap(Scheduler.suspendCards, suspend)
_Collection.remCards = wrap(_Collection.remCards, delete)
EditCurrent.__init__ = wrap(EditCurrent.__init__, onEdit)
Reviewer._answerCard = wrap(Reviewer._answerCard, answerCard, "before")
