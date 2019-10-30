'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from aqt import qt, appVersion

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_OPTIONS, DEFAULTS


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


def select_color_dialog(qcolor_dialog, preview_label):
    '''
    Shows the select color dialog and updates the preview color in settings.
    '''
    if qcolor_dialog.exec_():
        preview_label.setStyleSheet(
            'QLabel { background-color: %s; }'
            % qcolor_dialog.currentColor().name()
        )


def preferences(*args):
    '''
    Appends LifeDrain tab to Global Settings dialog.
    '''
    self = args[0]
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


def preferences_load(*args):
    '''
    Loads LifeDrain global configurations.
    '''
    self = args[0]
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


def deck_settings(*args):
    '''
    Appends a new tab to deck settings dialog.
    '''
    self = args[0]
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


def custom_deck_settings(*args):
    '''
    Adds LifeDrain configurations to custom study dialog.
    '''
    self = args[0]
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
