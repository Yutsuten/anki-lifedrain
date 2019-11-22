'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_OPTIONS, DEFAULTS


class SettingsUi(object):
    '''
    Contains a set of methods that creates the User Interface
    for configurating the add-on.
    '''
    _qt = None

    def __init__(self, qt):
        self._qt = qt

    def gui_settings_setup_layout(self, widget):
        '''
        Sets up the layout used for the menus used in Life Drain.
        '''
        layout = self._qt.QGridLayout(widget)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 4)
        layout.setColumnStretch(2, 3)
        layout.setColumnStretch(3, 2)
        layout.setColumnMinimumWidth(2, 50)
        return layout

    def create_label(self, form, row, text, color=None):
        '''
        Creates a label that occupies the whole line and wraps if it is too big.
        '''
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        form.lifedrain_layout.addWidget(label, row, 0, 1, 4)
        if color:
            label.setStyleSheet('color: {}'.format(color))

    def create_combo_box(self, form, row, cb_name, label_text, options):
        '''
        Creates a combo box with the specified label and options.
        '''
        label = self._qt.QLabel(label_text)
        setattr(form, cb_name, self._qt.QComboBox(form.lifedrain_widget))
        for option in options:
            getattr(form, cb_name).addItem(option)
        form.lifedrain_layout.addWidget(label, row, 0)
        form.lifedrain_layout.addWidget(getattr(form, cb_name), row, 2, 1, 2)

    def create_check_box(self, form, row, cb_name, label_text):
        '''
        Creates a checkbox with the specified label.
        '''
        label = self._qt.QLabel(label_text)
        setattr(form, cb_name, self._qt.QCheckBox(form.lifedrain_widget))
        form.lifedrain_layout.addWidget(label, row, 0)
        form.lifedrain_layout.addWidget(getattr(form, cb_name), row, 2, 1, 2)

    def create_spin_box(self, form, row, sb_name, label_text, val_range):
        '''
        Creates a spin box with the specified label and range.
        '''
        label = self._qt.QLabel(label_text)
        setattr(form, sb_name, self._qt.QSpinBox(form.lifedrain_widget))
        getattr(form, sb_name).setRange(val_range[0], val_range[1])
        form.lifedrain_layout.addWidget(label, row, 0)
        form.lifedrain_layout.addWidget(getattr(form, sb_name), row, 2, 1, 2)

    def create_color_select(self, form, row, cs_name, label_text):
        '''
        Creates a color select with the specified label.
        '''
        label = self._qt.QLabel(label_text)
        select_button = self._qt.QPushButton('Select')
        cs_preview_name = '%sPreview' % cs_name
        cs_dialog_name = '%sDialog' % cs_name
        setattr(form, cs_preview_name, self._qt.QLabel(''))
        setattr(form, cs_dialog_name, self._qt.QColorDialog(select_button))
        getattr(form, cs_dialog_name).setOption(self._qt.QColorDialog.DontUseNativeDialog)
        select_button.pressed.connect(
            lambda: select_color_dialog(getattr(form, cs_dialog_name), getattr(form, cs_preview_name))
        )
        form.lifedrain_layout.addWidget(label, row, 0)
        form.lifedrain_layout.addWidget(select_button, row, 2)
        form.lifedrain_layout.addWidget(getattr(form, cs_preview_name), row, 3)

    def fill_remaining_space(self, form, row):
        '''
        Fills the remaining space, so what comes after this is in the bottom.
        '''
        spacer = self._qt.QSpacerItem(
            1, 1, self._qt.QSizePolicy.Minimum, self._qt.QSizePolicy.Expanding
        )
        form.lifedrain_layout.addItem(spacer, row, 0)

    @staticmethod
    def select_color_dialog(qcolor_dialog, preview_label):
        '''
        Shows the select color dialog and updates the preview color in settings.
        '''
        if qcolor_dialog.exec_():
            preview_label.setStyleSheet(
                'QLabel { background-color: %s; }'
                % qcolor_dialog.currentColor().name()
            )

    def preferences(self, form):
        '''
        Appends LifeDrain tab to Global Settings dialog.
        '''
        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = self.gui_settings_setup_layout(form.lifedrain_widget)
        row = 0
        self.create_label(form, row, '<b>Bar behaviour</b>')
        row += 1
        self.create_check_box(form, row, 'stopOnAnswer', 'Stop drain on answer shown')
        row += 1
        self.create_check_box(form, row, 'disableAddon', 'Disable Life Drain (!)')
        row += 1
        self.create_label(form, row, '<b>Bar style</b>')
        row += 1
        self.create_combo_box(form, row, 'positionList', 'Position', POSITION_OPTIONS)
        row += 1
        self.create_spin_box(form, row, 'heightInput', 'Height', [1, 40])
        row += 1
        self.create_spin_box(form, row, 'borderRadiusInput', 'Border radius', [0, 20])
        row += 1
        self.create_combo_box(form, row, 'textList', 'Text', TEXT_OPTIONS)
        row += 1
        self.create_combo_box(form, row, 'styleList', 'Style', STYLE_OPTIONS)
        row += 1
        self.create_color_select(form, row, 'bgColor', 'Background color')
        row += 1
        self.create_color_select(form, row, 'fgColor', 'Foreground color')
        row += 1
        self.create_color_select(form, row, 'textColor', 'Text color')
        row += 1
        self.fill_remaining_space(form, row)
        form.tabWidget.addTab(form.lifedrain_widget, 'Life Drain')

    def preferences_load(self, pref):
        '''
        Loads LifeDrain global configurations.
        '''
        conf = pref.mw.col.conf
        pref.form.positionList.setCurrentIndex(
            conf.get('barPosition', DEFAULTS['barPosition'])
        )
        pref.form.heightInput.setValue(
            conf.get('barHeight', DEFAULTS['barHeight'])
        )

        pref.form.bgColorDialog.setCurrentColor(
            self._qt.QColor(conf.get('barBgColor', DEFAULTS['barBgColor']))
        )
        pref.form.bgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }'
            % pref.form.bgColorDialog.currentColor().name()
        )

        pref.form.fgColorDialog.setCurrentColor(
            self._qt.QColor(conf.get('barFgColor', DEFAULTS['barFgColor']))
        )
        pref.form.fgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }'
            % pref.form.fgColorDialog.currentColor().name()
        )

        pref.form.borderRadiusInput.setValue(
            conf.get('barBorderRadius', DEFAULTS['barBorderRadius'])
        )

        pref.form.textList.setCurrentIndex(
            conf.get('barText', DEFAULTS['barText'])
        )

        pref.form.textColorDialog.setCurrentColor(
            self._qt.QColor(conf.get('barTextColor', DEFAULTS['barTextColor']))
        )
        pref.form.textColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }'
            % pref.form.textColorDialog.currentColor().name()
        )

        pref.form.styleList.setCurrentIndex(
            conf.get('barStyle', DEFAULTS['barStyle'])
        )

        pref.form.stopOnAnswer.setChecked(
            conf.get('stopOnAnswer', DEFAULTS['stopOnAnswer']))

        pref.form.disableAddon.setChecked(
            conf.get('disable', DEFAULTS['disable'])
        )

    def deck_settings(self, form):
        '''
        Appends a new tab to deck settings dialog.
        '''
        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = self.gui_settings_setup_layout(form.lifedrain_widget)
        row = 0
        self.create_label(
            form, row,
            'The <b>maximum life</b> is the time in seconds for the life bar go '
            'from full to empty.\n<b>Recover</b> is the time in seconds that is '
            'recovered after answering a card. <b>Damage</b> is the life lost '
            'when a card is answered with \'Again\'.'
        )
        row += 1
        self.create_spin_box(form, row, 'maxLifeInput', 'Maximum life', [1, 10000])
        row += 1
        self.create_spin_box(form, row, 'recoverInput', 'Recover', [0, 1000])
        row += 1
        self.create_check_box(form, row, 'enableDamageInput', 'Enable damage')
        row += 1
        self.create_spin_box(form, row, 'damageInput', 'Damage', [-1000, 1000])
        row += 1
        self.create_spin_box(form, row, 'currentValueInput', 'Current life', [0, 10000])
        row += 1
        self.fill_remaining_space(form, row)
        form.tabWidget.addTab(form.lifedrain_widget, 'Life Drain')

    def custom_deck_settings(self, form, is_anki21):
        '''
        Adds LifeDrain configurations to custom study dialog.
        '''
        form.lifedrain_widget = self._qt.QGroupBox('Life Drain')
        form.lifedrain_layout = self.gui_settings_setup_layout(form.lifedrain_widget)
        row = 0
        self.create_spin_box(form, row, 'maxLifeInput', 'Maximum life', [1, 10000])
        row += 1
        self.create_spin_box(form, row, 'recoverInput', 'Recover', [0, 1000])
        row += 1
        self.create_check_box(form, row, 'enableDamageInput', 'Enable damage')
        row += 1
        self.create_spin_box(form, row, 'damageInput', 'Damage', [-1000, 1000])
        row += 1
        self.create_spin_box(form, row, 'currentValueInput', 'Current life', [0, 10000])
        row += 1
        index = 3 if is_anki21 else 2
        form.verticalLayout.insertWidget(index, form.lifedrain_widget)
