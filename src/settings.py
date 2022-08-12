"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from operator import itemgetter

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT, BEHAVIORS
from .version import VERSION


class Form:
    """Generates a form.

    The form is consisted of a (fixed) layout and widget elements, may be used
    on places like dialogs and tabs.
    """
    widget = None

    _qt = None
    _row = None
    _layout = None

    def __init__(self, qt, widget=None):
        self._qt = qt
        self._row = 0
        self.widget = widget if widget is not None else qt.QWidget()
        self._layout = qt.QGridLayout(self.widget)

    def label(self, text, color=None):
        """Creates a label in the current row of the form.

        Args:
            text: The text to be shown by the label.
            color: Optional. The color of the text in hex format.
        """
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        if color:
            label.setStyleSheet('color: {}'.format(color))

        self._layout.addWidget(label, self._row, 0, 1, 4)
        self._row += 1

    def text_field(self, tf_name, label_text, placeholder=None, tooltip=None):
        """Creates a text field in the current row of the form.

        Args:
            tf_name: The name of the text field. Not visible by the user.
            label_text: A text that describes what is the text field for.
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

    def combo_box(self, cb_name, label_text, options, tooltip=None):
        """Creates a combo box in the current row of the form.

        Args:
            cb_name: The name of the combo box. Not visible by the user.
            label_text: A text that describes what is the combo box for.
            options: A list of options.
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

    def check_box(self, cb_name, label_text, tooltip=None):
        """Creates a check box in the current row of the form.

        Args:
            cb_name: The name of the check box. Not visible by the user.
            label_text: A text that describes what is the check box for.
        """
        check_box = self._qt.QCheckBox(label_text, self.widget)
        if tooltip is not None:
            check_box.setToolTip(tooltip)

        check_box.get_value = check_box.isChecked
        check_box.set_value = check_box.setChecked

        setattr(self.widget, cb_name, check_box)
        self._layout.addWidget(check_box, self._row, 0, 1, 4)
        self._row += 1

    def spin_box(self, sb_name, label_text, val_range, tooltip=None):
        """Creates a spin box in the current row of the form.

        Args:
            sb_name: The name of the spin box. Not visible by the user.
            label_text: A text that describes what is the spin box for.
            val_range: A list of two integers that are the range.
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

    def color_select(self, cs_name, label_text, tooltip=None):
        """Creates a color select in the current row of the form.

        Args:
            cs_name: The name of the color select. Not visible by the user.
            label_text: A text that describes what is the color select for.
        """

        def choose_color():
            if not color_dialog.exec():
                return
            color = color_dialog.currentColor().name()
            css = 'QLabel { background-color: %s; }' % color
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

        def set_value(color):
            css = 'QLabel { background-color: %s; }' % color
            color_dialog.setCurrentColor(self._qt.QColor(color))
            preview_label.setStyleSheet(css)

        color_dialog.get_value = lambda: color_dialog.currentColor().name()
        color_dialog.set_value = set_value

        setattr(self.widget, '%sPreview' % cs_name, preview_label)
        setattr(self.widget, '%sDialog' % cs_name, color_dialog)
        self._layout.addWidget(label, self._row, 0)
        self._layout.addWidget(select_button, self._row, 2)
        self._layout.addWidget(preview_label, self._row, 3)
        self._row += 1

    def fill_space(self):
        """Creates a spacer that will vertically fill all the free space."""
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Policy.Minimum,
                                      self._qt.QSizePolicy.Policy.Expanding)
        self._layout.addItem(spacer, self._row, 0)
        self._row += 1

    def add_widget(self, widget):
        """Adds a widget to the form."""
        self._layout.addWidget(widget, self._row, 0, 1, 4)
        self._row += 1


def global_settings(aqt, main_window, config, deck_manager):
    """Opens a dialog with the Global Settings."""

    def save():
        enable_damage = deck_defaults.enableDamageInput.isChecked()

        damage = None
        damage_new = None
        damage_learning = None
        if enable_damage:
            damage = deck_defaults.damageInput.value()
            damage_new = deck_defaults.damageNewInput.value()
            damage_learning = deck_defaults.damageLearningInput.value()

            # When damage_*** is set to None, it defaults to damage
            if damage_new == damage:
                damage_new = None
            if damage_learning == damage:
                damage_learning = None

        conf = {
            'enable': basic_tab.enableAddon.get_value(),
            'stopOnAnswer': basic_tab.stopOnAnswer.get_value(),
            'stopOnLostFocus': basic_tab.stopOnLostFocus.get_value(),
            'globalSettingsShortcut': basic_tab.globalShortcut.get_value(),
            'deckSettingsShortcut': basic_tab.deckShortcut.get_value(),
            'pauseShortcut': basic_tab.pauseShortcut.get_value(),
            'recoverShortcut': basic_tab.recoverShortcut.get_value(),
            'behavUndo': basic_tab.behavUndo.get_value(),
            'behavBury': basic_tab.behavBury.get_value(),
            'behavSuspend': basic_tab.behavSuspend.get_value(),
            'barPosition': bar_style_tab.positionList.get_value(),
            'barHeight': bar_style_tab.heightInput.get_value(),
            'barBorderRadius': bar_style_tab.borderRadiusInput.get_value(),
            'barText': bar_style_tab.textList.get_value(),
            'barStyle': bar_style_tab.styleList.get_value(),
            'barFgColor': bar_style_tab.fgColorDialog.get_value(),
            'barTextColor': bar_style_tab.textColorDialog.get_value(),
            'enableBgColor': bar_style_tab.enableBgColor.get_value(),
            'barBgColor': bar_style_tab.bgColorDialog.get_value(),
            'shareDrain': deck_defaults.shareDrain.get_value(),
            'maxLife': deck_defaults.maxLifeInput.value(),
            'recover': deck_defaults.recoverInput.value(),
            'damage': damage,
            'damageNew': damage_new,
            'damageLearning': damage_learning,
        }
        config.set(conf)
        if conf['shareDrain']:
            conf['id'] = 'shared'
            deck_manager.set_deck_conf(conf, update_life=False)

        return dialog.accept()

    conf = config.get()
    dialog = aqt.QDialog(main_window)
    dialog.setWindowTitle(f'Life Drain Global Settings (v{VERSION})')

    basic_tab = _global_basic_tab(aqt, conf)
    bar_style_tab = _global_bar_style_tab(aqt, conf)
    deck_defaults = _global_deck_defaults(aqt, conf)

    tab_widget = aqt.QTabWidget()
    tab_widget.addTab(basic_tab, 'Basic')
    tab_widget.addTab(bar_style_tab, 'Bar Style')
    tab_widget.addTab(deck_defaults, 'Deck Defaults')

    button_box = aqt.QDialogButtonBox(
        aqt.QDialogButtonBox.StandardButton.Ok |
        aqt.QDialogButtonBox.StandardButton.Cancel)
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(400, 310)
    dialog.exec()


def _global_basic_tab(aqt, conf):

    def generate_form():
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
        tab.text_field('globalShortcut', 'Global Settings', 'Ctrl+L',
                       'Shortcut for the Global Settings.' + shortcut_tooltip)
        tab.text_field('deckShortcut', 'Deck Settings', 'L',
                       'Shortcut for the Deck Settings.' + shortcut_tooltip)
        tab.text_field('pauseShortcut', 'Pause', 'P',
                       'Shortcut for pausing.' + shortcut_tooltip)
        tab.text_field('recoverShortcut', 'Recover', None,
                       'Shortcut for recovering.' + shortcut_tooltip)
        tab.fill_space()
        return tab.widget

    def load_data(widget, conf):
        widget.enableAddon.set_value(conf['enable'])
        widget.stopOnAnswer.set_value(conf['stopOnAnswer'])
        widget.stopOnLostFocus.set_value(conf['stopOnLostFocus'])
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


def _global_bar_style_tab(aqt, conf):

    def generate_form():
        tab = Form(aqt)
        tab.combo_box('positionList', 'Position', POSITION_OPTIONS,
                      'Place to show the life bar.')
        tab.spin_box('heightInput', 'Height', [1, 40],
                     'Height of the life bar.')
        tab.spin_box('borderRadiusInput', 'Border radius', [0, 20],
                     'Add a rounded border to the life bar.')
        tab.combo_box('textList', 'Text', map(itemgetter('text'), TEXT_FORMAT),
                      'Text shown inside the life bar.')
        tab.combo_box('styleList', 'Style', STYLE_OPTIONS, '''Style of the \
life bar (not all options may work on your platform).''')
        tab.color_select('fgColor', 'Bar color',
                         "Color of the life bar's foreground.")
        tab.color_select('textColor', 'Text color',
                         "Color of the life bar's text.")
        tab.check_box('enableBgColor', 'Enable custom background color', '''\
If checked, you can choose a background color on the next field.''')
        tab.color_select('bgColor', 'Background color',
                         "Color of the life bar's background.")
        tab.fill_space()
        return tab.widget

    def load_data(widget, conf):
        widget.positionList.set_value(conf['barPosition'])
        widget.heightInput.set_value(conf['barHeight'])
        widget.borderRadiusInput.set_value(conf['barBorderRadius'])
        widget.textList.set_value(conf['barText'])
        widget.styleList.set_value(conf['barStyle'])
        widget.fgColorDialog.set_value(conf['barFgColor'])
        widget.textColorDialog.set_value(conf['barTextColor'])
        widget.enableBgColor.set_value(conf['enableBgColor'])
        widget.bgColorDialog.set_value(conf['barBgColor'])

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _global_deck_defaults(aqt, conf):

    def generate_form():
        tab = Form(aqt)
        tab.check_box('shareDrain', 'Share drain across all decks',
                      "Current life will be shared between all decks.")
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''Time in \
seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Recover', [0, 1000], '''Time in seconds \
that is recovered after answering a card.''')
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

    def load_data(widget, conf):
        widget.shareDrain.set_value(conf['shareDrain'])
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])

        def update_damageinput():
            damage_enabled = widget.enableDamageInput.isChecked()
            widget.damageInput.setEnabled(damage_enabled)
            widget.damageNewInput.setEnabled(damage_enabled)
            widget.damageLearningInput.setEnabled(damage_enabled)

        enable_damage = conf['damage'] is not None
        damage = conf['damage'] if enable_damage else 5

        if conf['damageNew'] is not None:
            damage_new = conf['damageNew']
        else:
            damage_new = damage

        if conf['damageLearning'] is not None:
            damage_learning = conf['damageLearning']
        else:
            damage_learning = damage

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


def deck_settings(aqt, main_window, config, global_config, deck_manager):
    """Opens a dialog with the Deck Settings."""

    def save():
        enable_damage = damage_tab.enableDamageInput.isChecked()

        damage = None
        damage_new = None
        damage_learning = None
        if enable_damage:
            damage = damage_tab.damageInput.value()
            damage_new = damage_tab.damageNewInput.value()
            damage_learning = damage_tab.damageLearningInput.value()

            # When damage_*** is set to None, it defaults to damage
            if damage_new == damage:
                damage_new = None
            if damage_learning == damage:
                damage_learning = None

        conf = config.get()
        conf.update({
            'maxLife': basic_tab.maxLifeInput.value(),
            'recover': basic_tab.recoverInput.value(),
            'damage': damage,
            'damageNew': damage_new,
            'damageLearning': damage_learning,
            'currentValue': basic_tab.currentValueInput.value(),
        })

        global_conf = global_config.get()
        if global_conf['shareDrain']:
            global_config.set(conf)
            conf['id'] = 'shared'
        else:
            config.set(conf)

        deck_manager.set_deck_conf(conf)
        return dialog.accept()

    conf = config.get()
    dialog = aqt.QDialog(main_window)
    dialog.setWindowTitle(f'Life Drain options for {conf["name"]}')

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
        aqt.QDialogButtonBox.StandardButton.Cancel)
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(300, 210)
    dialog.exec()


def _deck_basic_tab(aqt, conf, life):

    def generate_form():
        tab = Form(aqt)
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''Time in \
seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Recover', [0, 1000], '''Time in seconds \
that is recovered after answering a card.''')
        tab.spin_box('currentValueInput', 'Current life', [0, 10000],
                     'Current life, in seconds.')
        tab.fill_space()
        return tab.widget

    def load_data(widget, conf):
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])
        widget.currentValueInput.set_value(int(life))

    tab = generate_form()
    load_data(tab, conf)
    return tab


def _deck_damage_tab(aqt, conf):

    def generate_form():
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

    def load_data(widget, conf):
        def update_damageinput():
            damage_enabled = widget.enableDamageInput.isChecked()
            widget.damageInput.setEnabled(damage_enabled)
            widget.damageNewInput.setEnabled(damage_enabled)
            widget.damageLearningInput.setEnabled(damage_enabled)

        enable_damage = conf['damage'] is not None
        damage = conf['damage'] if enable_damage else 5

        if conf['damageNew'] is not None:
            damage_new = conf['damageNew']
        else:
            damage_new = damage

        if conf['damageLearning'] is not None:
            damage_learning = conf['damageLearning']
        else:
            damage_learning = damage

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
