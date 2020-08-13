"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from operator import itemgetter

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT


class Form:
    """Generate form elements."""
    _qt = None
    _form = None
    _row = None
    _conf = None

    def __init__(self, qt):
        self._qt = qt

    def label(self, text, color=None, minw=None, minh=None):
        """Creates a label in the current row of the form.

        Args:
            text: The text to be shown by the label.
            color: Optional. The color of the text in hex format.
        """
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        if minw and minh:
            label.setMinimumSize(minw, minh)
        self._form.lifedrain_layout.addWidget(label, self._row, 0, 1, 4)
        if color:
            label.setStyleSheet('color: {}'.format(color))
        self._row += 1

    def combo_box(self, cb_name, label_text, options):
        """Creates a combo box in the current row of the form.

        Args:
            cb_name: The name of the combo box. Not visible by the user.
            label_text: A text that describes what is the combo box for.
            options: A list of options.
        """
        label = self._qt.QLabel(label_text)
        setattr(self._form, cb_name,
                self._qt.QComboBox(self._form.lifedrain_widget))
        for option in options:
            getattr(self._form, cb_name).addItem(option)
        self._form.lifedrain_layout.addWidget(label, self._row, 0)
        self._form.lifedrain_layout.addWidget(getattr(self._form, cb_name),
                                              self._row, 2, 1, 2)
        self._row += 1

    def check_box(self, cb_name, label_text, tooltip=None):
        """Creates a check box in the current row of the form.

        Args:
            cb_name: The name of the check box. Not visible by the user.
            label_text: A text that describes what is the check box for.
        """
        setattr(self._form, cb_name,
                self._qt.QCheckBox(label_text, self._form.lifedrain_widget))
        if tooltip is not None:
            getattr(self._form, cb_name).setToolTip(tooltip)
        self._form.lifedrain_layout.addWidget(getattr(self._form, cb_name),
                                              self._row, 0, 1, 4)
        self._row += 1

    def spin_box(self, sb_name, label_text, val_range, tooltip=None):
        """Creates a spin box in the current row of the form.

        Args:
            sb_name: The name of the spin box. Not visible by the user.
            label_text: A text that describes what is the spin box for.
            val_range: A list of two integers that are the range.
        """
        label = self._qt.QLabel(label_text)
        setattr(self._form, sb_name,
                self._qt.QSpinBox(self._form.lifedrain_widget))
        getattr(self._form, sb_name).setRange(val_range[0], val_range[1])
        if tooltip is not None:
            label.setToolTip(tooltip)
            getattr(self._form, sb_name).setToolTip(tooltip)
        self._form.lifedrain_layout.addWidget(label, self._row, 0)
        self._form.lifedrain_layout.addWidget(getattr(self._form, sb_name),
                                              self._row, 2, 1, 2)
        self._row += 1

    def color_select(self, cs_name, label_text):
        """Creates a color select in the current row of the form.

        Args:
            cs_name: The name of the color select. Not visible by the user.
            label_text: A text that describes what is the color select for.
        """
        label = self._qt.QLabel(label_text)
        select_button = self._qt.QPushButton('Select')
        cs_preview_name = '%sPreview' % cs_name
        cs_dialog_name = '%sDialog' % cs_name
        setattr(self._form, cs_preview_name, self._qt.QLabel(''))
        setattr(self._form, cs_dialog_name,
                self._qt.QColorDialog(select_button))
        getattr(self._form, cs_dialog_name).setOption(
            self._qt.QColorDialog.DontUseNativeDialog)
        select_button.pressed.connect(lambda: self._select_color_dialog(
            getattr(self._form, cs_dialog_name),
            getattr(self._form, cs_preview_name)))
        self._form.lifedrain_layout.addWidget(label, self._row, 0)
        self._form.lifedrain_layout.addWidget(select_button, self._row, 2)
        self._form.lifedrain_layout.addWidget(
            getattr(self._form, cs_preview_name), self._row, 3)
        self._row += 1

    def fill_space(self):
        """Creates a spacer that will vertically fill all the free space."""
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Minimum,
                                      self._qt.QSizePolicy.Expanding)
        self._form.lifedrain_layout.addItem(spacer, self._row, 0)
        self._row += 1

    @staticmethod
    def _select_color_dialog(qcolor_dialog, preview_label):
        """Shows the select color dialog and updates the preview color.

        Args:
            qcolor_dialog: The instance of the color dialog.
            preview_label: The instance of the color dialog preview label.
        """
        if qcolor_dialog.exec_():
            preview_label.setStyleSheet('QLabel { background-color: %s; }' %
                                        qcolor_dialog.currentColor().name())


class GlobalSettingsOld(Form):
    """Creates the User Interfaces for configurating the add-on."""
    _global_conf = None

    def __init__(self, qt, global_conf):
        Form.__init__(self, qt)
        self._global_conf = global_conf

    def generate_form(self, form):
        """Appends a Life Drain tab to the Global Settings dialog.

        Args:
            form: The form instance of the Global Settings dialog.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = self._qt.QGridLayout(form.lifedrain_widget)
        self.label(
            'This form has been deprecated and will be removed the next '
            'release. <b>Open the Add-ons dialog, select Life Drain, then click'
            ' the Config button</b> to open the new Global Settings. You may '
            'also open it with the <b>shortcut Ctrl+L</b>.', '#FF0000', 200, 70)
        self.check_box('enableAddon', 'Enable Life Drain')
        self.check_box('stopOnAnswer', 'Stop drain on answer shown')
        self.label('<b>Bar style</b>')
        self.combo_box('positionList', 'Position', POSITION_OPTIONS)
        self.spin_box('heightInput', 'Height', [1, 40])
        self.spin_box('borderRadiusInput', 'Border radius', [0, 20])
        self.combo_box('textList', 'Text', map(itemgetter('text'), TEXT_FORMAT))
        self.combo_box('styleList', 'Style', STYLE_OPTIONS)
        self.color_select('fgColor', 'Bar color')
        self.color_select('textColor', 'Text color')
        self.check_box('enableBgColor', 'Enable custom background color')
        self.color_select('bgColor', 'Background color')
        self.fill_space()
        form.tabWidget.addTab(form.lifedrain_widget, 'Life Drain')

    def load_form_data(self, pref):
        """Loads Life Drain global settings into the form.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        conf = self._global_conf.get()
        form = pref.form

        form.enableAddon.setChecked(conf['enable'])
        form.stopOnAnswer.setChecked(conf['stopOnAnswer'])
        form.positionList.setCurrentIndex(conf['barPosition'])
        form.heightInput.setValue(conf['barHeight'])
        form.borderRadiusInput.setValue(conf['barBorderRadius'])
        form.textList.setCurrentIndex(conf['barText'])
        form.styleList.setCurrentIndex(conf['barStyle'])
        form.fgColorDialog.setCurrentColor(self._qt.QColor(conf['barFgColor']))
        form.fgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.fgColorDialog.currentColor().name())
        form.textColorDialog.setCurrentColor(
            self._qt.QColor(conf['barTextColor']))
        form.textColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.textColorDialog.currentColor().name())
        form.enableBgColor.setChecked(conf['enableBgColor'])
        form.bgColorDialog.setCurrentColor(self._qt.QColor(conf['barBgColor']))
        form.bgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.bgColorDialog.currentColor().name())

    def save_form_data(self, pref):
        """Saves Life Drain global settings from the form.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        form = pref.form
        conf = {
            'enable': form.enableAddon.isChecked(),
            'stopOnAnswer': form.stopOnAnswer.isChecked(),
            'barPosition': form.positionList.currentIndex(),
            'barHeight': form.heightInput.value(),
            'barBorderRadius': form.borderRadiusInput.value(),
            'barText': form.textList.currentIndex(),
            'barStyle': form.styleList.currentIndex(),
            'barFgColor': form.fgColorDialog.currentColor().name(),
            'barTextColor': form.textColorDialog.currentColor().name(),
            'enableBgColor': form.enableBgColor.isChecked(),
            'barBgColor': form.bgColorDialog.currentColor().name()}
        self._global_conf.set(conf)
        return conf


class GlobalSettings(Form):
    """Creates the User Interfaces for Global Settings."""
    _global_conf = None

    def __init__(self, qt, global_conf):
        Form.__init__(self, qt)
        self._global_conf = global_conf

    def open(self):
        """Opens a dialog with the Global Settings."""
        conf = self._global_conf.get()
        dialog = self._qt.QDialog()

        window_title = 'Life Drain Global Settings'
        dialog.setWindowTitle(window_title)

        layout = self._qt.QGridLayout(dialog)
        self._generate_form(dialog, layout)
        self._load_form_data(dialog, conf)

        def save():
            self._global_conf.set(self._get_form_data(dialog))
            return dialog.accept()

        button_box = self._qt.QDialogButtonBox(
            self._qt.QDialogButtonBox.Ok | self._qt.QDialogButtonBox.Cancel
        )
        button_box.rejected.connect(dialog.reject)
        button_box.accepted.connect(save)
        layout.addWidget(button_box, self._row, 0, 1, 4)

        dialog.setMinimumSize(400, 310)
        dialog.exec()

    def _generate_form(self, form, layout):
        """Generates the Global Settings form.

        Args:
            form: The form instance of the Deck Settings dialog.
            layout: The layout of the form.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = layout

        self.check_box('enableAddon', 'Enable Life Drain')
        self.check_box('stopOnAnswer', 'Stop drain on answer shown')
        self.label('<b>Bar style</b>')
        self.combo_box('positionList', 'Position', POSITION_OPTIONS)
        self.spin_box('heightInput', 'Height', [1, 40])
        self.spin_box('borderRadiusInput', 'Border radius', [0, 20])
        self.combo_box('textList', 'Text', map(itemgetter('text'), TEXT_FORMAT))
        self.combo_box('styleList', 'Style', STYLE_OPTIONS)
        self.color_select('fgColor', 'Bar color')
        self.color_select('textColor', 'Text color')
        self.check_box('enableBgColor', 'Enable custom background color')
        self.color_select('bgColor', 'Background color')
        self.fill_space()

    def _load_form_data(self, form, conf):
        form.enableAddon.setChecked(conf['enable'])
        form.stopOnAnswer.setChecked(conf['stopOnAnswer'])
        form.positionList.setCurrentIndex(conf['barPosition'])
        form.heightInput.setValue(conf['barHeight'])
        form.borderRadiusInput.setValue(conf['barBorderRadius'])
        form.textList.setCurrentIndex(conf['barText'])
        form.styleList.setCurrentIndex(conf['barStyle'])
        form.fgColorDialog.setCurrentColor(self._qt.QColor(conf['barFgColor']))
        form.fgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.fgColorDialog.currentColor().name())
        form.textColorDialog.setCurrentColor(
            self._qt.QColor(conf['barTextColor']))
        form.textColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.textColorDialog.currentColor().name())
        form.enableBgColor.setChecked(conf['enableBgColor'])
        form.bgColorDialog.setCurrentColor(self._qt.QColor(conf['barBgColor']))
        form.bgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.bgColorDialog.currentColor().name())

    @staticmethod
    def _get_form_data(form):
        conf = {
            'enable': form.enableAddon.isChecked(),
            'stopOnAnswer': form.stopOnAnswer.isChecked(),
            'barPosition': form.positionList.currentIndex(),
            'barHeight': form.heightInput.value(),
            'barBorderRadius': form.borderRadiusInput.value(),
            'barText': form.textList.currentIndex(),
            'barStyle': form.styleList.currentIndex(),
            'barFgColor': form.fgColorDialog.currentColor().name(),
            'barTextColor': form.textColorDialog.currentColor().name(),
            'enableBgColor': form.enableBgColor.isChecked(),
            'barBgColor': form.bgColorDialog.currentColor().name()}
        return conf


class DeckSettings(Form):
    """Creates the User Interface for Deck Settings."""
    _deck_conf = None

    def __init__(self, qt, deck_conf):
        Form.__init__(self, qt)
        self._deck_conf = deck_conf

    def open(self, life, set_deck_conf):
        """Opens a dialog with the Deck Settings."""
        conf = self._deck_conf.get()
        settings_dialog = self._qt.QDialog()

        window_title = 'Life Drain options for {}'.format(conf['name'])
        settings_dialog.setWindowTitle(window_title)

        layout = self._qt.QGridLayout(settings_dialog)
        self._generate_form(settings_dialog, layout)
        self._load_form_data(settings_dialog, conf, life)

        def save():
            conf = self._deck_conf.get()
            conf.update(self._get_form_data(settings_dialog))
            set_deck_conf(conf)
            self._deck_conf.set(conf)
            return settings_dialog.accept()

        button_box = self._qt.QDialogButtonBox(
            self._qt.QDialogButtonBox.Ok | self._qt.QDialogButtonBox.Cancel
        )
        button_box.rejected.connect(settings_dialog.reject)
        button_box.accepted.connect(save)
        layout.addWidget(button_box, self._row, 0, 1, 4)

        settings_dialog.setMinimumSize(300, 210)
        settings_dialog.exec()

    def _generate_form(self, form, layout):
        """Generates the Deck Settings form.

        Args:
            form: The form instance of the Deck Settings dialog.
            layout: The layout of the form.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = layout
        self.spin_box('maxLifeInput', 'Maximum life', [1, 10000], '''The time \
in seconds for the life bar go from full to empty.''')
        self.spin_box('recoverInput', 'Recover', [0, 1000], '''The time in \
seconds that is recovered after answering a card.''')
        self.check_box('enableDamageInput', 'Enable damage', '''Enable damage \
if a card is answered with 'Again'.''')
        self.spin_box('damageInput', 'Damage', [-1000, 1000], '''The damage \
value to be dealt if answering with 'Again'.''')
        self.spin_box('currentValueInput', 'Current life', [0, 10000], '''The \
current life, in seconds.''')
        self.fill_space()

    @staticmethod
    def _load_form_data(form, conf, life):
        def update_damageinput_state():
            damage_enabled = form.enableDamageInput.isChecked()
            form.damageInput.setEnabled(damage_enabled)
            form.damageInput.setValue(5)

        form.maxLifeInput.setValue(conf['maxLife'])
        form.recoverInput.setValue(conf['recover'])
        damage = conf['damage']
        form.enableDamageInput.setChecked(damage is not None)
        form.enableDamageInput.stateChanged.connect(update_damageinput_state)
        form.damageInput.setValue(damage if damage is not None else 5)
        form.damageInput.setEnabled(conf['damage'] is not None)
        form.currentValueInput.setValue(life)

    @staticmethod
    def _get_form_data(form):
        """Gets Life Drain deck settings from the form."""
        enable_damage = form.enableDamageInput.isChecked()
        return {
            'maxLife': form.maxLifeInput.value(),
            'recover': form.recoverInput.value(),
            'damage': form.damageInput.value() if enable_damage else None,
            'currentValue': form.currentValueInput.value()
        }
