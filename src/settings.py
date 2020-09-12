"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from operator import itemgetter

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT


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
        if placeholder is not None:
            text_field.setPlaceholderText(placeholder)
        if tooltip is not None:
            label.setToolTip(tooltip)
            text_field.setToolTip(tooltip)

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
            if not color_dialog.exec_():
                return
            color = color_dialog.currentColor().name()
            css = 'QLabel { background-color: %s; }' % color
            preview_label.setStyleSheet(css)

        label = self._qt.QLabel(label_text)
        select_button = self._qt.QPushButton('Select')
        preview_label = self._qt.QLabel('')
        color_dialog = self._qt.QColorDialog(select_button)
        color_dialog.setOption(self._qt.QColorDialog.DontUseNativeDialog)
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
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Minimum,
                                      self._qt.QSizePolicy.Expanding)
        self._layout.addItem(spacer, self._row, 0)
        self._row += 1

    def add_widget(self, widget):
        """Adds a widget to the form."""
        self._layout.addWidget(widget, self._row, 0, 1, 4)
        self._row += 1


def global_settings(aqt, config):
    """Opens a dialog with the Global Settings."""

    def save():
        config.set({
            'enable': basic_tab.enableAddon.get_value(),
            'stopOnAnswer': basic_tab.stopOnAnswer.get_value(),
            'barPosition': bar_style_tab.positionList.get_value(),
            'barHeight': bar_style_tab.heightInput.get_value(),
            'barBorderRadius': bar_style_tab.borderRadiusInput.get_value(),
            'barText': bar_style_tab.textList.get_value(),
            'barStyle': bar_style_tab.styleList.get_value(),
            'barFgColor': bar_style_tab.fgColorDialog.get_value(),
            'barTextColor': bar_style_tab.textColorDialog.get_value(),
            'enableBgColor': bar_style_tab.enableBgColor.get_value(),
            'barBgColor': bar_style_tab.bgColorDialog.get_value()
        })
        return dialog.accept()

    conf = config.get()
    dialog = aqt.QDialog()
    dialog.setWindowTitle('Life Drain Global Settings')

    basic_tab = _global_basic_tab(aqt)
    bar_style_tab = _global_bar_style_tab(aqt)

    tab_widget = aqt.QTabWidget()
    tab_widget.addTab(basic_tab, 'Basic')
    tab_widget.addTab(bar_style_tab, 'Bar Style')

    _global_load_basic_tab(basic_tab, conf)
    _global_load_bar_style_tab(bar_style_tab, conf)

    button_box = aqt.QDialogButtonBox(aqt.QDialogButtonBox.Ok |
                                      aqt.QDialogButtonBox.Cancel)
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(400, 310)
    dialog.exec()


def _global_basic_tab(aqt):
    tab = Form(aqt)
    tab.check_box('enableAddon', 'Enable Life Drain',
                  'Enable/disable the add-on without restarting Anki.')
    tab.check_box('stopOnAnswer', 'Stop drain on answer shown',
                  'Automatically stops the drain after answering a card.')
    tab.label('<b>Shortcuts</b>')
    shortcut_tooltip = '''There is no validation for your shortcut \
string, so edit with care!
Invalid shortcuts, or already used shortcuts won't work.
Example of valid shortcuts: 'Ctrl+L', 'Alt+L', 'Shift+L', 'L'.'''
    tab.text_field('globalShortcut', 'Global Settings', 'Ctrl+L',
                   shortcut_tooltip)
    tab.text_field('deckShortcut', 'Deck Settings', 'L', shortcut_tooltip)
    tab.text_field('pauseShortcut', 'Pause', 'P', shortcut_tooltip)
    tab.text_field('recoverShortcut', 'Recover', None, shortcut_tooltip)
    tab.fill_space()
    return tab.widget


def _global_bar_style_tab(aqt):
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


def _global_load_basic_tab(widget, conf):
    widget.enableAddon.set_value(conf['enable'])
    widget.stopOnAnswer.set_value(conf['stopOnAnswer'])


def _global_load_bar_style_tab(widget, conf):
    widget.positionList.set_value(conf['barPosition'])
    widget.heightInput.set_value(conf['barHeight'])
    widget.borderRadiusInput.set_value(conf['barBorderRadius'])
    widget.textList.set_value(conf['barText'])
    widget.styleList.set_value(conf['barStyle'])
    widget.fgColorDialog.set_value(conf['barFgColor'])
    widget.textColorDialog.set_value(conf['barTextColor'])
    widget.enableBgColor.set_value(conf['enableBgColor'])
    widget.bgColorDialog.set_value(conf['barBgColor'])


def deck_settings(aqt, config, deck_manager):
    """Opens a dialog with the Deck Settings."""

    def create_basic_tab():
        tab = Form(aqt)
        tab.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''Time in \
seconds for the life bar go from full to empty.''')
        tab.spin_box('recoverInput', 'Recover', [0, 1000], '''Time in seconds \
that is recovered after answering a card.''')
        tab.spin_box('currentValueInput', 'Current life', [0, 10000],
                     'Current life, in seconds.')
        tab.fill_space()
        return tab.widget

    def create_damage_tab():
        tab = Form(aqt)
        tab.check_box('enableDamageInput', 'Enable damage',
                      "Enable the damage feature.")
        tab.spin_box('damageInput', 'Damage', [-1000, 1000],
                     "Damage value to be dealt when answering with 'Again'.")
        tab.fill_space()
        return tab.widget

    def load_basic_tab(widget, conf, life):
        widget.maxLifeInput.set_value(conf['maxLife'])
        widget.recoverInput.set_value(conf['recover'])
        widget.currentValueInput.set_value(life)

    def load_damage_tab(form, conf):
        def update_damageinput():
            damage_enabled = form.enableDamageInput.isChecked()
            form.damageInput.setEnabled(damage_enabled)
            form.damageInput.setValue(5)

        damage = conf['damage']
        form.enableDamageInput.set_value(damage is not None)
        form.enableDamageInput.stateChanged.connect(update_damageinput)
        form.damageInput.set_value(damage if damage is not None else 5)
        form.damageInput.setEnabled(conf['damage'] is not None)

    def save():
        conf = config.get()
        enable_damage = damage_tab.enableDamageInput.isChecked()
        damage_value = damage_tab.damageInput.value()
        conf.update({
            'maxLife': basic_tab.maxLifeInput.value(),
            'recover': basic_tab.recoverInput.value(),
            'damage': damage_value if enable_damage else None,
            'currentValue': basic_tab.currentValueInput.value()
        })

        deck_manager.set_deck_conf(conf)
        config.set(conf)
        return dialog.accept()

    conf = config.get()
    dialog = aqt.QDialog()
    dialog.setWindowTitle('Life Drain options for {}'.format(conf['name']))

    basic_tab = create_basic_tab()
    damage_tab = create_damage_tab()

    tab_widget = aqt.QTabWidget()
    tab_widget.addTab(basic_tab, 'Basic')
    tab_widget.addTab(damage_tab, 'Damage')

    load_basic_tab(basic_tab, conf, deck_manager.get_current_life())
    load_damage_tab(damage_tab, conf)

    button_box = aqt.QDialogButtonBox(aqt.QDialogButtonBox.Ok |
                                      aqt.QDialogButtonBox.Cancel)
    button_box.rejected.connect(dialog.reject)
    button_box.accepted.connect(save)

    outer_form = Form(aqt, dialog)
    outer_form.add_widget(tab_widget)
    outer_form.add_widget(button_box)

    dialog.setMinimumSize(300, 210)
    dialog.exec()
