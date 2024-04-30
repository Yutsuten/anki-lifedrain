# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

from operator import itemgetter
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from .defaults import BEHAVIORS, DEFAULTS, POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT
from .version import VERSION

if TYPE_CHECKING:
    from aqt.main import AnkiQt

    from .database import DeckConf, GlobalConf
    from .deck_manager import DeckManager


class Form:
    """Generates a form.

    The form is consisted of a (fixed) layout and widget elements, may be used
    on places like dialogs and tabs.
    """

    def __init__(self, qt: Any, widget: Any=None):
        self._qt = qt
        self._row = 0
        self.widget = widget if widget is not None else qt.QWidget()
        self._layout = qt.QGridLayout(self.widget)

    def label(self, text: str, color: Optional[str]=None) -> None:
        """Creates a label in the current row of the form.

        Args:
            text: The text to be shown by the label.
            color: Optional. The color of the text in hex format.
        """
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        if color:
            label.setStyleSheet(f'color: {color}')

        self._layout.addWidget(label, self._row, 0, 1, 4)
        self._row += 1

    def text_field(self, tf_name: str, label_text:str, placeholder: Optional[str]=None,
                   tooltip: Optional[str]=None) -> None:
        """Creates a text field in the current row of the form.

        Args:
            tf_name: The name of the text field. Not visible by the user.
            label_text: A text that describes what is the text field for.
            placeholder: A sample input or tip
            tooltip: The tooltip to be shown.
        """
        label = self._qt.QLabel(label_text)
        text_field = self._qt.QLineEdit(self.widget)
        text_field.setMaxLength(15)
        if placeholder is not None:
            text_field.setPlaceholderText(placeholder)
        if tooltip is not None:
            label.setToolTip(tooltip)
            text_field.setToolTip(tooltip)

        text_field.get_value = text_field.text
        text_field.set_value = text_field.setText

        setattr(self.widget, tf_name, text_field)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(text_field, self._row, 2, 1, 2)
        self._row += 1

    def combo_box(self, cb_name: str, label_text: str, options: Union[Iterator[str], list[str]],
                  tooltip: Optional[str]=None) -> None:
        """Creates a combo box in the current row of the form.

        Args:
            cb_name: The name of the combo box. Not visible by the user.
            label_text: A text that describes what is the combo box for.
            options: A list of options.
            tooltip: The tooltip to be shown.
        """
        label = self._qt.QLabel(label_text)
        combo_box = self._qt.QComboBox(self.widget)
        for option in options:
            combo_box.addItem(option)
        if tooltip is not None:
            label.setToolTip(tooltip)
            combo_box.setToolTip(tooltip)

        combo_box.get_value = combo_box.currentIndex
        combo_box.set_value = combo_box.setCurrentIndex

        setattr(self.widget, cb_name, combo_box)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(combo_box, self._row, 2, 1, 2)
        self._row += 1

    def check_box(self, cb_name: str, label_text: str, tooltip: Optional[str]=None) -> None:
        """Creates a check box in the current row of the form.

        Args:
            cb_name: The name of the check box. Not visible by the user.
            label_text: A text that describes what is the check box for.
            tooltip: The tooltip to be shown.
        """
        check_box = self._qt.QCheckBox(label_text, self.widget)
        if tooltip is not None:
            check_box.setToolTip(tooltip)

        check_box.get_value = check_box.isChecked
        check_box.set_value = check_box.setChecked

        setattr(self.widget, cb_name, check_box)
        self._layout.addWidget(check_box, self._row, 0, 1, 4)
        self._row += 1

    def spin_box(self, sb_name: str, label_text: str, val_range: list[int],
                 tooltip: Optional[str]=None) -> None:
        """Creates a spin box in the current row of the form.

        Args:
            sb_name: The name of the spin box. Not visible by the user.
            label_text: A text that describes what is the spin box for.
            val_range: A list of two integers that are the range.
            tooltip: The tooltip to be shown.
        """
        label = self._qt.QLabel(label_text)
        spin_box = self._qt.QSpinBox(self.widget)
        spin_box.setRange(val_range[0], val_range[1])
        if tooltip is not None:
            label.setToolTip(tooltip)
            spin_box.setToolTip(tooltip)

        spin_box.get_value = spin_box.value
        spin_box.set_value = spin_box.setValue

        setattr(self.widget, sb_name, spin_box)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(spin_box, self._row, 2, 1, 2)
        self._row += 1

    def double_spin_box(self, sb_name: str, label_text: str, val_range: list[float],
                        tooltip: Optional[str]=None) -> None:
        """Creates a double spin box in the current row of the form.

        Args:
            sb_name: The name of the spin box. Not visible by the user.
            label_text: A text that describes what is the spin box for.
            val_range: A list of two floats that are the range.
            tooltip: The tooltip to be shown.
        """
        label = self._qt.QLabel(label_text)
        double_spin_box = self._qt.QDoubleSpinBox(self.widget)
        double_spin_box.setRange(val_range[0], val_range[1])
        double_spin_box.setDecimals(1)
        double_spin_box.setSingleStep(0.1)
        if tooltip is not None:
            label.setToolTip(tooltip)
            double_spin_box.setToolTip(tooltip)

        double_spin_box.get_value = double_spin_box.value
        double_spin_box.set_value = double_spin_box.setValue

        setattr(self.widget, sb_name, double_spin_box)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(double_spin_box, self._row, 2, 1, 2)
        self._row += 1

    def color_select(self, cs_name: str, label_text: str, tooltip: Optional[str]=None) -> None:
        """Creates a color select in the current row of the form.

        Args:
            cs_name: The name of the color select. Not visible by the user.
            label_text: A text that describes what is the color select for.
            tooltip: The tooltip to be shown.
        """

        def choose_color() -> None:
            if not color_dialog.exec():
                return
            color = color_dialog.currentColor().name()
            css = f'QLabel {{ background-color: {color}; }}'
            preview_label.setStyleSheet(css)

        label = self._qt.QLabel(label_text)
        select_button = self._qt.QPushButton('Select')
        preview_label = self._qt.QLabel('')
        color_dialog = self._qt.QColorDialog(select_button)
        color_dialog.setOption(
            self._qt.QColorDialog.ColorDialogOption.DontUseNativeDialog)
        select_button.pressed.connect(choose_color)
        if tooltip is not None:
            label.setToolTip(tooltip)
            select_button.setToolTip(tooltip)
            preview_label.setToolTip(tooltip)

        def set_value(color: str) -> None:
            css = f'QLabel {{ background-color: {color}; }}'
            color_dialog.setCurrentColor(self._qt.QColor(color))
            preview_label.setStyleSheet(css)

        color_dialog.get_value = lambda: color_dialog.currentColor().name()
        color_dialog.set_value = set_value

        setattr(self.widget, f'{cs_name}Preview', preview_label)
        setattr(self.widget, f'{cs_name}Dialog', color_dialog)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(select_button, self._row, 2)
        self._layout.addWidget(preview_label, self._row, 3)
        self._row += 1

    def fill_space(self) -> None:
        """Creates a spacer that will vertically fill all the free space."""
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Policy.Minimum,
                                      self._qt.QSizePolicy.Policy.Expanding)
        self._layout.addItem(spacer, self._row, 0)
        self._row += 1

    def add_widget(self, widget: Any) -> None:
        """Adds a widget to the form."""
        self._layout.addWidget(widget, self._row, 0, 1, 4)
        self._row += 1


def global_settings(aqt: Any, mw: AnkiQt, config: GlobalConf, deck_manager: DeckManager) -> None:
    """Opens a dialog with the Global Settings."""

    def save() -> None:
        enable_damage = deck_defaults_tab.enableDamageInput.isChecked()

        damage = None
        damage_new = None
        damage_learning = None
        if enable_damage:
            damage = deck_defaults_tab.damageInput.value()
            damage_new = deck_defaults_tab.damageNewInput.value()
            damage_learning = deck_defaults_tab.damageLearningInput.value()

        conf = {
            'enable': basic_tab.enableAddon.get_value(),
            'stopOnAnswer': basic_tab.stopOnAnswer.get_value(),
            'stopOnLostFocus': basic_tab.stopOnLostFocus.get_value(),
            'startEmpty': basic_tab.startEmpty.get_value(),
            'globalSettingsShortcut': basic_tab.globalShortcut.get_value(),
            'deckSettingsShortcut': basic_tab.deckShortcut.get_value(),
            'pauseShortcut': basic_tab.pauseShortcut.get_value(),
            'recoverShortcut': basic_tab.recoverShortcut.get_value(),
            'behavUndo': basic_tab.behavUndo.get_value(),
            'behavBury': basic_tab.behavBury.get_value(),
            'behavSuspend': basic_tab.behavSuspend.get_value(),
            'invert': bar_style_tab.invert.get_value(),
            'barPosition': bar_style_tab.positionList.get_value(),
            'barHeight': bar_style_tab.heightInput.get_value(),
            'barBorderRadius': bar_style_tab.borderRadiusInput.get_value(),
            'barStyle': bar_style_tab.styleList.get_value(),
            'barFgColor': bar_style_tab.fgColorDialog.get_value(),
            'barThresholdWarn': bar_style_tab.thresholdWarn.get_value(),
            'barFgColorWarn': bar_style_tab.fgColorWarnDialog.get_value(),
            'barThresholdDanger': bar_style_tab.thresholdDanger.get_value(),
            'barFgColorDanger': bar_style_tab.fgColorDangerDialog.get_value(),
            'barText': bar_style_tab.textList.get_value(),
            'barTextColor': bar_style_tab.textColorDialog.get_value(),
            'enableBgColor': bar_style_tab.enableBgColor.get_value(),
            'barBgColor': bar_style_tab.bgColorDialog.get_value(),
            'shareDrain': deck_defaults_tab.shareDrain.get_value(),
            'maxLife': deck_defaults_tab.maxLifeInput.value(),
            'recover': deck_defaults_tab.recoverInput.value(),
            'fullRecoverSpeed': deck_defaults_tab.fullRecoverInput.value(),
            'damage': damage,
            'damageNew': damage_new,
            'damageLearning': damage_learning,
        }
        config.update(conf)
        if conf['shareDrain']:
            conf['id'] = 'shared'
            deck_manager.set_deck_conf(conf, update_life=False)

        return dialog.accept()

    def clicked(button: Any) -> None:
        if button_box.buttonRole(button) == aqt.QDialogButtonBox.ButtonRole.ResetRole:
            _global_settings_restore_defaults(basic_tab, bar_style_tab, deck_defaults_tab)

    conf = config.get()
    dialog = aqt.QDialog(mw)
    dialog.setWindowTitle(f'Life Drain Global Settings (v{VERSION})')

    basic_tab = _global_basic_tab(aqt, conf)
    bar_style_tab = _global_bar_style_tab(aqt, conf)
    deck_defaults_tab = _global_deck_defaults(aqt, conf)

    tab_widget = aqt.QTabWidget()
    tab_widget.addTab(basic_tab, 'Basic')
    tab_widget.addTab(bar_style_tab, 'Bar Style')
    tab_widget.addTab(deck_defaults_tab, 'Deck Defaults')

    button_box = aqt.QDialogButtonBox(
        aqt.QDialogButtonBox.StandardButton.Ok |
        aqt.QDialogButtonBox.StandardButton.Cancel |
        aqt.QDialogButtonBox.StandardButton.RestoreDefaults,
    )
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)
    button_box.clicked.connect(clicked)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(400, 310)
    dialog.exec()


def _global_basic_tab(aqt: Any, conf: dict[str, Any]) -> Any:

    def generate_form() -> Any:
        tab = Form(aqt)
        tab.check_box('enableAddon', 'Enable Life Drain',
                      'Enable/disable the add-on without restarting Anki.')
        tab.check_box('stopOnAnswer', 'Stop drain on answer shown',
                      'Automatically stops the drain after answering a card.')
        tab.check_box('stopOnLostFocus',
                      'Stop drain while edititing or browsing',
                      '''Automatically stops the drain when opening the \
editor or browser.
May not resume the drain automatically when closing it.''')
        tab.check_box('startEmpty', 'Default initial life is 0',
                      'Life will begin at 0 instead of full. Also affects Recover.')
        tab.label('<b>Special action behavior</b>')
        tab.combo_box('behavUndo', 'Delete', BEHAVIORS, '''How should the \
program behave when deleting a card/note?''')
        tab.combo_box('behavBury', 'Bury', BEHAVIORS, '''How should the \
program behave when burying a card/note?''')
        tab.combo_box('behavSuspend', 'Suspend', BEHAVIORS, '''How should the \
program behave when suspending a card/note?''')
        tab.label('<b>Shortcuts</b>')
        shortcut_tooltip = '''
There is no validation for your shortcut string, so edit with care!
Invalid shortcuts, or already used shortcuts won't work.'''
        tab.text_field('globalShortcut', 'Global Settings', DEFAULTS['globalSettingsShortcut'],
                       'Shortcut for the Global Settings.' + shortcut_tooltip)
        tab.text_field('deckShortcut', 'Deck Settings', DEFAULTS['deckSettingsShortcut'],
                       'Shortcut for the Deck Settings.' + shortcut_tooltip)
        tab.text_field('pauseShortcut', 'Pause', DEFAULTS['pauseShortcut'],
                       'Shortcut for pausing.' + shortcut_tooltip)
        tab.text_field('recoverShortcut', 'Recover', None,
                       'Shortcut for recovering.' + shortcut_tooltip)
        tab.fill_space()
        return tab.widget

    def load_data(widget: Any, conf: dict[str, Any]) -> None:
        widget.enableAddon.set_value(conf['enable'])
        widget.stopOnAnswer.set_value(conf['stopOnAnswer'])
        widget.stopOnLostFocus.set_value(conf['stopOnLostFocus'])
        widget.startEmpty.set_value(conf['startEmpty'])
        widget.behavUndo.set_value(conf['behavUndo'])
        widget.behavBury.set_value(conf['behavBury'])
        widget.behavSuspend.set_value(conf['behavSuspend'])
        widget.globalShortcut.set_value(conf['globalSettingsShortcut'])
        widget.deckShortcut.set_value(conf['deckSettingsShortcut'])
        widget.pauseShortcut.set_value(conf['pauseShortcut'])
        widget.recoverShortcut.set_value(conf['recoverShortcut'])

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _global_bar_style_tab(aqt: Any, conf: dict[str, Any]) -> Any:

    def generate_form() -> Any:
        tab = Form(aqt)
        tab.check_box('invert', 'Invert bar movement',
                      'Reduce life from left to right instead of right to left.')
        tab.combo_box('positionList', 'Position', POSITION_OPTIONS,
                      'Place to show the life bar.')
        tab.spin_box('heightInput', 'Height', [1, 40],
                     'Height of the life bar.')
        tab.spin_box('borderRadiusInput', 'Border radius', [0, 20],
                     'Add a rounded border to the life bar.')
        tab.combo_box('styleList', 'Style', STYLE_OPTIONS, '''Style of the \
life bar (not all options may work on your platform).''')
        tab.color_select('fgColor', 'Bar color (default)',
                         "Color of the life bar's foreground.")
        tab.spin_box('thresholdWarn', 'Warn threshold (%)', [0, 99],
                     'Threshold % to show the life bar with the warn color.')
        tab.color_select('fgColorWarn', 'Bar color (warn)',
                         "Color of the life bar's foreground (warn).")
        tab.spin_box('thresholdDanger', 'Danger threshold (%)', [0, 99],
                     'Threshold % to show the life bar with the danger color.')
        tab.color_select('fgColorDanger', 'Bar color (danger)',
                         "Color of the life bar's foreground (danger).")
        tab.combo_box('textList', 'Text', map(itemgetter('text'), TEXT_FORMAT),
                      'Text shown inside the life bar.')
        tab.color_select('textColor', 'Text color',
                         "Color of the life bar's text.")
        tab.check_box('enableBgColor', 'Enable custom background color', '''\
If checked, you can choose a background color on the next field.''')
        tab.color_select('bgColor', 'Background color',
                         "Color of the life bar's background.")
        tab.fill_space()
        return tab.widget

    def load_data(widget: Any, conf: dict[str, Any]) -> None:
        widget.invert.set_value(conf['invert'])
        widget.positionList.set_value(conf['barPosition'])
        widget.heightInput.set_value(conf['barHeight'])
        widget.borderRadiusInput.set_value(conf['barBorderRadius'])
        widget.styleList.set_value(conf['barStyle'])
        widget.fgColorDialog.set_value(conf['barFgColor'])
        widget.thresholdWarn.set_value(conf['barThresholdWarn'])
        widget.fgColorWarnDialog.set_value(conf['barFgColorWarn'])
        widget.thresholdDanger.set_value(conf['barThresholdDanger'])
        widget.fgColorDangerDialog.set_value(conf['barFgColorDanger'])
        widget.textList.set_value(conf['barText'])
        widget.textColorDialog.set_value(conf['barTextColor'])
        widget.enableBgColor.set_value(conf['enableBgColor'])
        widget.bgColorDialog.set_value(conf['barBgColor'])

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _global_deck_defaults(aqt: Any, conf: dict[str, Any]) -> Any:

    def generate_form() -> Any:
        tab = Form(aqt)
        tab.check_box('shareDrain', 'Share drain across all decks',
                      'Current life will be shared between all decks.')
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''Time in \
seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Answer recover', [0, 1000], '''Time in seconds \
that is recovered after answering a card.''')
        tab.double_spin_box('fullRecoverInput', 'Full recover speed', [-10000, 10000], '''Amount \
to recover each second when clicking the "Recover" button in the deck overview screen. Negative \
values allowed.
Use 0 for the default behavior: instant recovery.
The recover will stop once life reaches 0, maximum, or when leaving deck overview screen.''')
        tab.check_box('enableDamageInput', 'Enable damage',
                      "Enable the damage feature. It will be triggered when \
answering with 'Again'.")
        tab.spin_box('damageNewInput', 'New cards', [-1000, 1000],
                     'Damage value on new cards.')
        tab.spin_box('damageLearningInput', 'Learning cards', [-1000, 1000],
                     'Damage value on learning cards.')
        tab.spin_box('damageInput', 'Review cards', [-1000, 1000],
                     'Damage value on review cards.')
        tab.fill_space()
        return tab.widget

    def load_data(widget: Any, conf: dict[str, Any]) -> None:
        widget.shareDrain.set_value(conf['shareDrain'])
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])
        widget.fullRecoverInput.set_value(conf['fullRecoverSpeed'])

        def update_damageinput() -> None:
            damage_enabled = widget.enableDamageInput.isChecked()
            widget.damageInput.setEnabled(damage_enabled)
            widget.damageNewInput.setEnabled(damage_enabled)
            widget.damageLearningInput.setEnabled(damage_enabled)

        enable_damage = conf['damage'] is not None
        damage = conf['damage'] if enable_damage else 5
        damage_new = conf['damageNew'] if conf['damageNew'] is not None else damage
        damage_learning = conf['damageLearning'] if conf['damageLearning'] is not None else damage

        widget.enableDamageInput.set_value(enable_damage)
        widget.enableDamageInput.stateChanged.connect(update_damageinput)
        widget.damageInput.set_value(damage)
        widget.damageNewInput.set_value(damage_new)
        widget.damageLearningInput.set_value(damage_learning)

        widget.damageInput.setEnabled(enable_damage)
        widget.damageNewInput.setEnabled(enable_damage)
        widget.damageLearningInput.setEnabled(enable_damage)

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _global_settings_restore_defaults(basic_tab: Any, bar_style_tab: Any,
                                      deck_defaults_tab: Any) -> None:
    basic_tab.enableAddon.set_value(DEFAULTS['enable'])
    basic_tab.stopOnAnswer.set_value(DEFAULTS['stopOnAnswer'])
    basic_tab.stopOnLostFocus.set_value(DEFAULTS['stopOnLostFocus'])
    basic_tab.startEmpty.set_value(DEFAULTS['startEmpty'])
    basic_tab.behavUndo.set_value(DEFAULTS['behavUndo'])
    basic_tab.behavBury.set_value(DEFAULTS['behavBury'])
    basic_tab.behavSuspend.set_value(DEFAULTS['behavSuspend'])
    basic_tab.globalShortcut.set_value(DEFAULTS['globalSettingsShortcut'])
    basic_tab.deckShortcut.set_value(DEFAULTS['deckSettingsShortcut'])
    basic_tab.pauseShortcut.set_value(DEFAULTS['pauseShortcut'])
    basic_tab.recoverShortcut.set_value(DEFAULTS['recoverShortcut'])

    bar_style_tab.positionList.set_value(DEFAULTS['barPosition'])
    bar_style_tab.heightInput.set_value(DEFAULTS['barHeight'])
    bar_style_tab.borderRadiusInput.set_value(DEFAULTS['barBorderRadius'])
    bar_style_tab.styleList.set_value(DEFAULTS['barStyle'])
    bar_style_tab.fgColorDialog.set_value(DEFAULTS['barFgColor'])
    bar_style_tab.thresholdWarn.set_value(DEFAULTS['barThresholdWarn'])
    bar_style_tab.fgColorWarnDialog.set_value(DEFAULTS['barFgColorWarn'])
    bar_style_tab.thresholdDanger.set_value(DEFAULTS['barThresholdDanger'])
    bar_style_tab.fgColorDangerDialog.set_value(DEFAULTS['barFgColorDanger'])
    bar_style_tab.textList.set_value(DEFAULTS['barText'])
    bar_style_tab.textColorDialog.set_value(DEFAULTS['barTextColor'])
    bar_style_tab.enableBgColor.set_value(DEFAULTS['enableBgColor'])
    bar_style_tab.bgColorDialog.set_value(DEFAULTS['barBgColor'])

    deck_defaults_tab.shareDrain.set_value(DEFAULTS['shareDrain'])
    deck_defaults_tab.maxLifeInput.set_value(DEFAULTS['maxLife'])
    deck_defaults_tab.recoverInput.set_value(DEFAULTS['recover'])
    enable_damage = DEFAULTS['damage'] is not None
    damage = DEFAULTS['damage'] if enable_damage else 5
    deck_defaults_tab.enableDamageInput.set_value(enable_damage)
    deck_defaults_tab.damageInput.set_value(damage)
    deck_defaults_tab.damageNewInput.set_value(damage)
    deck_defaults_tab.damageLearningInput.set_value(damage)
    deck_defaults_tab.damageInput.setEnabled(enable_damage)
    deck_defaults_tab.damageNewInput.setEnabled(enable_damage)
    deck_defaults_tab.damageLearningInput.setEnabled(enable_damage)


def deck_settings(aqt: Any, mw: AnkiQt, config: DeckConf, global_config: GlobalConf,
                  deck_manager: DeckManager) -> None:
    """Opens a dialog with the Deck Settings."""

    def save() -> None:
        enable_damage = damage_tab.enableDamageInput.isChecked()

        damage = None
        damage_new = None
        damage_learning = None
        if enable_damage:
            damage = damage_tab.damageInput.value()
            damage_new = damage_tab.damageNewInput.value()
            damage_learning = damage_tab.damageLearningInput.value()

        conf = config.get()
        conf.update({
            'enable': basic_tab.enable.isChecked(),
            'maxLife': basic_tab.maxLifeInput.value(),
            'recover': basic_tab.recoverInput.value(),
            'fullRecoverSpeed': basic_tab.fullRecoverInput.value(),
            'damage': damage,
            'damageNew': damage_new,
            'damageLearning': damage_learning,
            'currentValue': basic_tab.currentValueInput.value(),
        })

        global_conf = global_config.get()
        if global_conf['shareDrain']:
            global_config.update(conf)
            conf['id'] = 'shared'
        else:
            config.update(conf)

        deck_manager.set_deck_conf(conf, update_life=True)
        return dialog.accept()

    def clicked(button: Any) -> None:
        if button_box.buttonRole(button) == aqt.QDialogButtonBox.ButtonRole.ResetRole:
            _deck_settings_restore_defaults(basic_tab, damage_tab)

    conf = config.get()
    dialog = aqt.QDialog(mw)
    dialog.setWindowTitle(f'Life Drain Deck Settings for {conf["name"]}')

    global_conf = global_config.get()
    if global_conf['shareDrain']:
        conf = global_conf

    basic_tab = _deck_basic_tab(aqt, conf, deck_manager.get_current_life())
    damage_tab = _deck_damage_tab(aqt, conf)

    tab_widget = aqt.QTabWidget()
    tab_widget.addTab(basic_tab, 'Basic')
    tab_widget.addTab(damage_tab, 'Damage')

    button_box = aqt.QDialogButtonBox(
        aqt.QDialogButtonBox.StandardButton.Ok |
        aqt.QDialogButtonBox.StandardButton.Cancel |
        aqt.QDialogButtonBox.StandardButton.RestoreDefaults,
    )
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)
    button_box.clicked.connect(clicked)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(300, 210)
    dialog.exec()


def _deck_basic_tab(aqt: Any, conf: dict[str, Any], life: float) -> Any:

    def generate_form() -> Any:
        tab = Form(aqt)
        tab.check_box('enable', 'Enable for this deck',
                      'Enable/disable Life Drain for this deck.')
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''Time in \
seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Answer recover', [0, 1000], '''Time in seconds \
that is recovered after answering a card.''')
        tab.double_spin_box('currentValueInput', 'Current life', [0, 10000],
                            'Current life, in seconds.')
        tab.double_spin_box('fullRecoverInput', 'Full recover speed', [-10000, 10000], '''Amount \
to recover each second when clicking the "Recover" button in the deck overview screen. Negative \
values allowed.
Use 0 for the default behavior: instant recovery.
The recover will stop once life reaches 0, maximum, or when leaving deck overview screen.''')
        tab.fill_space()
        return tab.widget

    def load_data(widget: Any, conf: dict[str, Any]) -> None:
        widget.enable.set_value(conf['enable'])
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])
        widget.currentValueInput.set_value(life)
        widget.fullRecoverInput.set_value(conf['fullRecoverSpeed'])

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _deck_damage_tab(aqt: Any, conf: dict[str, Any]) -> Any:

    def generate_form() -> Any:
        tab = Form(aqt)
        tab.check_box('enableDamageInput', 'Enable damage',
                      "Enable the damage feature. It will be triggered when \
answering with 'Again'.")
        tab.spin_box('damageNewInput', 'New cards', [-1000, 1000],
                     'Damage value on new cards.')
        tab.spin_box('damageLearningInput', 'Learning cards', [-1000, 1000],
                     'Damage value on learning cards.')
        tab.spin_box('damageInput', 'Review cards', [-1000, 1000],
                     'Damage value on review cards.')
        tab.fill_space()
        return tab.widget

    def load_data(widget: Any, conf: dict[str, Any]) -> None:
        def update_damageinput() -> None:
            damage_enabled = widget.enableDamageInput.isChecked()
            widget.damageInput.setEnabled(damage_enabled)
            widget.damageNewInput.setEnabled(damage_enabled)
            widget.damageLearningInput.setEnabled(damage_enabled)

        enable_damage = conf['damage'] is not None
        damage = conf['damage'] if enable_damage else 5
        damage_new = conf['damageNew'] if conf['damageNew'] is not None else damage
        damage_learning = conf['damageLearning'] if conf['damageLearning'] is not None else damage

        widget.enableDamageInput.set_value(enable_damage)
        widget.enableDamageInput.stateChanged.connect(update_damageinput)
        widget.damageInput.set_value(damage)
        widget.damageNewInput.set_value(damage_new)
        widget.damageLearningInput.set_value(damage_learning)

        widget.damageInput.setEnabled(enable_damage)
        widget.damageNewInput.setEnabled(enable_damage)
        widget.damageLearningInput.setEnabled(enable_damage)

    tab = generate_form()
    load_data(tab, conf)
    return tab

def _deck_settings_restore_defaults(basic_tab: Any, damage_tab: Any) -> None:
    basic_tab.enable.set_value(DEFAULTS['enable'])
    basic_tab.maxLifeInput.set_value(DEFAULTS['maxLife'])
    basic_tab.recoverInput.set_value(DEFAULTS['recover'])
    basic_tab.currentValueInput.set_value(DEFAULTS['maxLife'])

    enable_damage = DEFAULTS['damage'] is not None
    damage = DEFAULTS['damage'] if enable_damage else 5
    damage_tab.enableDamageInput.set_value(enable_damage)
    damage_tab.damageInput.set_value(damage)
    damage_tab.damageNewInput.set_value(damage)
    damage_tab.damageLearningInput.set_value(damage)
    damage_tab.damageInput.setEnabled(enable_damage)
    damage_tab.damageNewInput.setEnabled(enable_damage)
    damage_tab.damageLearningInput.setEnabled(enable_damage)
