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


# Saving data inside a class to access it as lifedrain.config
class LifeDrain(object):  # pylint: disable=too-few-public-methods
    '''
    Contains the state of the life drain.
    '''
    config = {}
    deck_bar_manager = None
    timer = None
    status = {
        'reviewed': False,
        'newCardState': False,
        'screen': None,
        'reviewResponse': 0
    }
    stop_on_answer = False
    disable = None


# Variable with the state the life drain
# Pylint complains that it is a constant, so I disabled this check
lifedrain = LifeDrain()  # pylint: disable=invalid-name


# Allowed this method to use global statement, as I don't see any other
# way to access my variables inside the methods extended from Anki.
# Adding new parameters to those methods is not possible, and cannot use
# classes because it adds a parameter 'self' to the methods
def get_lifedrain():
    '''
    Gets the state of the life drain.
    '''
    global lifedrain  # pylint: disable=invalid-name,global-statement

    if mw.col is not None:
        # Create deck_bar_manager, should run only once
        if lifedrain.deck_bar_manager is None:
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
            progress_bar = AnkiProgressBar(config, DEFAULTS['maxLife'])
            progress_bar.hide()
            lifedrain.deck_bar_manager = DeckProgressBarManager(progress_bar)
            lifedrain.disable = mw.col.conf.get('disable', DEFAULTS['disable'])
            lifedrain.stop_on_answer = mw.col.conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])

        # Keep deck list always updated
        for deck_id in mw.col.decks.allIds():
            lifedrain.deck_bar_manager.add_deck(deck_id, mw.col.decks.confForDid(deck_id))

    return lifedrain


def gui_settings_setup_layout(widget):
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


def create_label(self, row, text, color=None):
    '''
    Creates a label that occupies the whole line and wraps if it is too big.
    '''
    label = qt.QLabel(text)
    label.setWordWrap(True)
    self.lifeDrainLayout.addWidget(label, row, 0, 1, 4)
    if color:
        label.setStyleSheet('color: {}'.format(color))


def create_combo_box(self, row, cb_name, label_text, options):
    '''
    Creates a combo box with the specified label and options.
    '''
    label = qt.QLabel(label_text)
    setattr(self, cb_name, qt.QComboBox(self.lifeDrainWidget))
    for option in options:
        getattr(self, cb_name).addItem(option)
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(getattr(self, cb_name), row, 2, 1, 2)


def create_check_box(self, row, cb_name, label_text):
    '''
    Creates a checkbox with the specified label.
    '''
    label = qt.QLabel(label_text)
    setattr(self, cb_name, qt.QCheckBox(self.lifeDrainWidget))
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(getattr(self, cb_name), row, 2, 1, 2)


def create_spin_box(self, row, sb_name, label_text, val_range):
    '''
    Creates a spin box with the specified label and range.
    '''
    label = qt.QLabel(label_text)
    setattr(self, sb_name, qt.QSpinBox(self.lifeDrainWidget))
    getattr(self, sb_name).setRange(val_range[0], val_range[1])
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(getattr(self, sb_name), row, 2, 1, 2)


def create_color_select(self, row, cs_name, label_text):
    '''
    Creates a color select with the specified label.
    '''
    label = qt.QLabel(label_text)
    select_button = qt.QPushButton('Select')
    cs_preview_name = '%sPreview' % cs_name
    cs_dialog_name = '%sDialog' % cs_name
    setattr(self, cs_preview_name, qt.QLabel(''))
    setattr(self, cs_dialog_name, qt.QColorDialog(select_button))
    getattr(self, cs_dialog_name).setOption(qt.QColorDialog.DontUseNativeDialog)
    select_button.pressed.connect(
        lambda: select_color_dialog(getattr(self, cs_dialog_name), getattr(self, cs_preview_name))
    )
    self.lifeDrainLayout.addWidget(label, row, 0)
    self.lifeDrainLayout.addWidget(select_button, row, 2)
    self.lifeDrainLayout.addWidget(getattr(self, cs_preview_name), row, 3)


def fill_remaining_space(self, row):
    '''
    Fills the remaining space, so what comes after this is in the bottom.
    '''
    spacer = qt.QSpacerItem(
        1, 1, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding
    )
    self.lifeDrainLayout.addItem(spacer, row, 0)


def global_settings_lifedrain_tab_ui(self, Preferences):
    '''
    Appends LifeDrain tab to Global Settings dialog.
    '''
    self.lifeDrainWidget = qt.QWidget()
    self.lifeDrainLayout = gui_settings_setup_layout(self.lifeDrainWidget)
    row = 0
    create_label(self, row, '<b>Bar behaviour</b>')
    row += 1
    create_check_box(self, row, 'stopOnAnswer', 'Stop drain on answer shown')
    row += 1
    create_check_box(self, row, 'disableAddon', 'Disable Life Drain (!)')
    row += 1
    create_label(self, row, '<b>Bar style</b>')
    row += 1
    create_combo_box(self, row, 'positionList', 'Position', POSITION_OPTIONS)
    row += 1
    create_spin_box(self, row, 'heightInput', 'Height', [1, 40])
    row += 1
    create_spin_box(self, row, 'borderRadiusInput', 'Border radius', [0, 20])
    row += 1
    create_combo_box(self, row, 'textList', 'Text', TEXT_OPTIONS)
    row += 1
    create_combo_box(self, row, 'styleList', 'Style', STYLE_OPTIONS)
    row += 1
    create_color_select(self, row, 'bgColor', 'Background color')
    row += 1
    create_color_select(self, row, 'fgColor', 'Foreground color')
    row += 1
    create_color_select(self, row, 'textColor', 'Text color')
    row += 1
    fill_remaining_space(self, row)
    self.tabWidget.addTab(self.lifeDrainWidget, 'Life Drain')


def select_color_dialog(qcolor_dialog, preview_label):
    '''
    Shows the select color dialog and updates the preview color in settings.
    '''
    if qcolor_dialog.exec_():
        preview_label.setStyleSheet(
            'QLabel { background-color: %s; }'
            % qcolor_dialog.currentColor().name()
        )


def global_load_conf(self, mw):
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


def global_save_conf(self):
    '''
    Saves LifeDrain global configurations.
    '''
    lifedrain = get_lifedrain()

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
    lifedrain.deck_bar_manager.set_anki_progress_bar_style(config)
    lifedrain.disable = conf.get('disable', DEFAULTS['disable'])
    lifedrain.stop_on_answer = conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer'])


def deck_settings_lifedrain_tab_ui(self, Dialog):
    '''
    Appends a new tab to deck settings dialog.
    '''
    self.lifeDrainWidget = qt.QWidget()
    self.lifeDrainLayout = gui_settings_setup_layout(self.lifeDrainWidget)
    row = 0
    create_label(
        self, row,
        'The <b>maximum life</b> is the time in seconds for the life bar go '
        'from full to empty.\n<b>Recover</b> is the time in seconds that is '
        'recovered after answering a card. <b>Damage</b> is the life lost '
        'when a card is answered with \'Again\'.'
    )
    row += 1
    create_spin_box(self, row, 'maxLifeInput', 'Maximum life', [1, 10000])
    row += 1
    create_spin_box(self, row, 'recoverInput', 'Recover', [0, 1000])
    row += 1
    create_check_box(self, row, 'enableDamageInput', 'Enable damage')
    row += 1
    create_spin_box(self, row, 'damageInput', 'Damage', [-1000, 1000])
    row += 1
    create_spin_box(self, row, 'currentValueInput', 'Current life', [0, 10000])
    row += 1
    fill_remaining_space(self, row)
    self.tabWidget.addTab(self.lifeDrainWidget, 'Life Drain')


def load_deck_conf(self):
    '''
    Loads LifeDrain deck configurations.
    '''
    lifedrain = get_lifedrain()

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
        lifedrain.deck_bar_manager.get_deck_conf(self.deck['id'])['currentValue']
    )


def save_deck_conf(self):
    '''
    Saves LifeDrain deck configurations.
    '''
    lifedrain = get_lifedrain()

    self.conf['maxLife'] = self.form.maxLifeInput.value()
    self.conf['recover'] = self.form.recoverInput.value()
    self.conf['currentValue'] = self.form.currentValueInput.value()
    self.conf['enableDamage'] = self.form.enableDamageInput.isChecked()
    self.conf['damage'] = self.form.damageInput.value()
    lifedrain.deck_bar_manager.set_deck_conf(self.deck['id'], self.conf)


def custom_study_lifedrain_ui(self, Dialog):
    '''
    Adds LifeDrain configurations to custom study dialog.
    '''
    self.lifeDrainWidget = qt.QGroupBox('Life Drain')
    self.lifeDrainLayout = gui_settings_setup_layout(self.lifeDrainWidget)
    row = 0
    create_spin_box(self, row, 'maxLifeInput', 'Maximum life', [1, 10000])
    row += 1
    create_spin_box(self, row, 'recoverInput', 'Recover', [0, 1000])
    row += 1
    create_check_box(self, row, 'enableDamageInput', 'Enable damage')
    row += 1
    create_spin_box(self, row, 'damageInput', 'Damage', [-1000, 1000])
    row += 1
    create_spin_box(self, row, 'currentValueInput', 'Current life', [0, 10000])
    row += 1
    index = 2 if appVersion.startswith('2.0') else 3
    self.verticalLayout.insertWidget(index, self.lifeDrainWidget)


forms.preferences.Ui_Preferences.setupUi = wrap(
    forms.preferences.Ui_Preferences.setupUi, global_settings_lifedrain_tab_ui
)
Preferences.__init__ = wrap(Preferences.__init__, global_load_conf)
Preferences.accept = wrap(Preferences.accept, global_save_conf, 'before')


forms.dconf.Ui_Dialog.setupUi = wrap(
    forms.dconf.Ui_Dialog.setupUi, deck_settings_lifedrain_tab_ui
)
DeckConf.loadConf = wrap(DeckConf.loadConf, load_deck_conf)
DeckConf.saveConf = wrap(DeckConf.saveConf, save_deck_conf, 'before')


forms.dyndconf.Ui_Dialog.setupUi = wrap(
    forms.dyndconf.Ui_Dialog.setupUi, custom_study_lifedrain_ui
)
FiltDeckConf.loadConf = wrap(FiltDeckConf.loadConf, load_deck_conf)
FiltDeckConf.saveConf = wrap(FiltDeckConf.saveConf, save_deck_conf, 'before')


class DeckProgressBarManager(object):
    '''
    Allow using the same instance of AnkiProgressBar with different
    configuration and current_value for each deck.
    '''
    _anki_progressbar = None
    _barInfo = {}
    _current_deck = None
    _game_over = False

    def __init__(self, ankiProgressBar):
        self._anki_progressbar = ankiProgressBar

    def add_deck(self, deck_id, conf):
        '''
        Adds a deck to the manager.
        '''
        if str(deck_id) not in self._barInfo:
            self._barInfo[str(deck_id)] = {
                'maxValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'currentValue': conf.get('maxLife', DEFAULTS['maxLife']),
                'recoverValue': conf.get('recover', DEFAULTS['recover']),
                'enableDamageValue': conf.get('enableDamage', DEFAULTS['enableDamage']),
                'damageValue': conf.get('damage', DEFAULTS['damage'])
            }

    def set_deck(self, deck_id):
        '''
        Sets the current deck.
        '''
        if deck_id:
            self._current_deck = str(deck_id)
            self._anki_progressbar.set_max_value(
                self._barInfo[self._current_deck]['maxValue']
            )
            self._anki_progressbar.set_current_value(
                self._barInfo[self._current_deck]['currentValue']
            )
        else:
            self._current_deck = None

    def get_deck_conf(self, deck_id):
        '''
        Get the settings and state of a deck.
        '''
        return self._barInfo[str(deck_id)]

    def set_deck_conf(self, deck_id, conf):
        '''
        Updates deck's current state.
        '''
        max_life = conf.get('maxLife', DEFAULTS['maxLife'])
        recover = conf.get('recover', DEFAULTS['recover'])
        enable_damage = conf.get('enableDamage', DEFAULTS['enableDamage'])
        damage = conf.get('damage', DEFAULTS['damage'])
        current_value = conf.get('currentValue', DEFAULTS['maxLife'])
        if current_value > max_life:
            current_value = max_life

        self._barInfo[str(deck_id)]['maxValue'] = max_life
        self._barInfo[str(deck_id)]['recoverValue'] = recover
        self._barInfo[str(deck_id)]['enableDamageValue'] = enable_damage
        self._barInfo[str(deck_id)]['damageValue'] = damage
        self._barInfo[str(deck_id)]['currentValue'] = current_value

    def set_anki_progress_bar_style(self, config=None):
        '''
        Updates the AnkiProgressBar instance.
        '''
        pb_style = {
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
                self._anki_progressbar.dock_at(config['position'])
            if 'progressBarStyle' in config:
                pb_style.update(config['progressBarStyle'])

        self._anki_progressbar.set_style(pb_style)
        if self._current_deck is not None:
            self.recover(value=0)

    def recover(self, increment=True, value=None, damage=False):
        '''
        Abstraction for recovering life, increments the bar if increment is True (default).
        '''
        multiplier = 1
        if not increment:
            multiplier = -1
        if value is None:
            if damage and self._barInfo[self._current_deck]['enableDamageValue']:
                multiplier = -1
                value = self._barInfo[self._current_deck]['damageValue']
            else:
                value = self._barInfo[self._current_deck]['recoverValue']

        self._anki_progressbar.inc_current_value(multiplier * value)

        life = self._anki_progressbar.get_current_value()
        self._barInfo[self._current_deck]['currentValue'] = life
        if life == 0 and not self._game_over:
            self._game_over = True
            runHook('LifeDrain.gameOver')
        elif life > 0:
            self._game_over = False

    def bar_visible(self, visible):
        '''
        Sets the visibility of the Progress Bar
        '''
        if visible:
            self._anki_progressbar.show()
        else:
            self._anki_progressbar.hide()


# Night Mode integration begin
try:
    import Night_Mode
    Night_Mode.nm_css_menu += 'QMainWindow::separator { width: 0px; height: 0px; }'
except Exception:  # nosec  # pylint: disable=broad-except
    pass
# Night Mode integration end


def on_edit(*args):
    '''
    Updates reviewed status to False when user goes to edit mode.
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['reviewed'] = False


def timer_trigger():
    '''
    When a decisecond (0.1s) passes, this function is triggered.
    '''
    lifedrain = get_lifedrain()
    lifedrain.deck_bar_manager.recover(False, 0.1)


def after_state_change(state, oldState):
    '''
    Called when user alternates between deckBrowser, overview, review screens.
    It updates some variables and shows/hides the bar.
    '''
    lifedrain = get_lifedrain()

    if not lifedrain.disable:  # Enabled
        if not lifedrain.timer:
            lifedrain.timer = ProgressManager(mw).timer(100, timer_trigger, True)
        lifedrain.timer.stop()

        if lifedrain.status['reviewed'] and state in ['overview', 'review']:
            lifedrain.deck_bar_manager.recover()
        lifedrain.status['reviewed'] = False
        lifedrain.status['screen'] = state

        if state == 'deckBrowser':
            lifedrain.deck_bar_manager.bar_visible(False)
            lifedrain.deck_bar_manager.set_deck(None)
        else:
            if mw.col is not None:
                lifedrain.deck_bar_manager.set_deck(mw.col.decks.current()['id'])
            lifedrain.deck_bar_manager.bar_visible(True)

        if state == 'review':
            lifedrain.timer.start()

    else:  # Disabled
        lifedrain.deck_bar_manager.bar_visible(False)
        if lifedrain.timer is not None:
            lifedrain.timer.stop()


def show_question():
    '''
    Called when a question is shown.
    '''
    lifedrain = get_lifedrain()

    if not lifedrain.disable:
        activate_timer()
        if lifedrain.status['reviewed']:
            if lifedrain.status['reviewResponse'] == 1:
                lifedrain.deck_bar_manager.recover(damage=True)
            else:
                lifedrain.deck_bar_manager.recover()
        lifedrain.status['reviewed'] = False
        lifedrain.status['newCardState'] = False


def show_answer():
    '''
    Called when an answer is shown.
    '''
    lifedrain = get_lifedrain()

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
    lifedrain = get_lifedrain()

    if not lifedrain.disable:
        if lifedrain.status['screen'] == 'review' and not lifedrain.status['newCardState']:
            lifedrain.status['reviewed'] = False
            lifedrain.deck_bar_manager.recover(False)
        lifedrain.status['newCardState'] = False


def leech(card):
    '''
    Called when the card becomes a leech.
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['newCardState'] = True


def bury(self, ids):
    '''
    Called when the card is buried.
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['newCardState'] = True


def suspend(self, ids):
    '''
    Called when the card is suspended.
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['newCardState'] = True


def delete(self, ids, notes=True):
    '''
    Called when the card is deleted.
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['newCardState'] = True


def activate_timer():
    '''
    Activates the timer that reduces the bar.
    '''
    lifedrain = get_lifedrain()
    if not lifedrain.disable and lifedrain.timer is not None and not lifedrain.timer.isActive():
        lifedrain.timer.start()


def deactivate_timer():
    '''
    Deactivates the timer that reduces the bar.
    '''
    lifedrain = get_lifedrain()
    if not lifedrain.disable and lifedrain.timer is not None and lifedrain.timer.isActive():
        lifedrain.timer.stop()


def toggle_timer():
    '''
    Toggle the timer to pause/unpause the drain.
    '''
    lifedrain = get_lifedrain()
    if not lifedrain.disable and lifedrain.timer is not None:
        if lifedrain.timer.isActive():
            lifedrain.timer.stop()
        else:
            lifedrain.timer.start()


def recover(increment=True, value=None, damage=False):
    '''
    Method ran when invoking 'LifeDrain.recover' hook.
    '''
    lifedrain = get_lifedrain()
    lifedrain.deck_bar_manager.recover(increment, value, damage)


def answer_card(self, resp):
    '''
    Called when a card is answered
    '''
    lifedrain = get_lifedrain()
    lifedrain.status['reviewResponse'] = resp


# Dealing with key presses is different in Anki 2.0 and 2.1
# This if/elif block deals with the differences
if appVersion.startswith('2.0'):
    def key_handler(self, evt, _old):
        '''
        Appends 'p' shortcut to pause the drain.
        '''
        key = evt.text()
        if key == 'p':
            toggle_timer()
        else:
            _old(self, evt)

    Reviewer._keyHandler = wrap(Reviewer._keyHandler, key_handler, 'around')

elif appVersion.startswith('2.1'):
    def _add_shortcut(shortcuts):
        '''
        Appends 'p' shortcut to pause the drain.
        '''
        shortcuts.append(tuple(['p', toggle_timer]))

    addHook('reviewStateShortcuts', _add_shortcut)


addHook('afterStateChange', after_state_change)
addHook('showQuestion', show_question)
addHook('showAnswer', show_answer)
addHook('reset', undo)
addHook('revertedCard', lambda cid: undo())
addHook('leech', leech)
addHook('LifeDrain.recover', recover)

Scheduler.buryNote = wrap(Scheduler.buryNote, bury)
Scheduler.buryCards = wrap(Scheduler.buryCards, bury)
Scheduler.suspendCards = wrap(Scheduler.suspendCards, suspend)
_Collection.remCards = wrap(_Collection.remCards, delete)
EditCurrent.__init__ = wrap(EditCurrent.__init__, on_edit)
Reviewer._answerCard = wrap(Reviewer._answerCard, answer_card, "before")
