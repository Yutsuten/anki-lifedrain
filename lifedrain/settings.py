"""
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
"""

from operator import itemgetter

from .defaults import DEFAULTS, POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT


class Settings(object):
    """Creates the User Interfaces for configurating the add-on."""

    _qt = None
    _form = None
    _row = None
    _conf = None

    def __init__(self, qt):
        """Saves the qt library to generate the Settings UI later.

        Args:
            qt: The PyQt library.
        """
        self._qt = qt

    def preferences_ui(self, form):
        """Appends a Life Drain tab to the Global Settings dialog.

        Args:
            form: The form instance of the Global Settings dialog.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = self._gui_settings_setup_layout(
            form.lifedrain_widget)
        self._create_label('<b>Bar behaviour</b>')
        self._create_check_box('stopOnAnswer', 'Stop drain on answer shown')
        self._create_check_box('disableAddon', 'Disable Life Drain (!)')
        self._create_label('<b>Bar style</b>')
        self._create_combo_box('positionList', 'Position', POSITION_OPTIONS)
        self._create_spin_box('heightInput', 'Height', [1, 40])
        self._create_spin_box('borderRadiusInput', 'Border radius', [0, 20])
        self._create_combo_box('textList', 'Text',
                               map(itemgetter('text'), TEXT_FORMAT))
        self._create_combo_box('styleList', 'Style', STYLE_OPTIONS)
        self._create_color_select('fgColor', 'Bar color')
        self._create_color_select('textColor', 'Text color')
        self._fill_remaining_space()
        form.tabWidget.addTab(form.lifedrain_widget, 'Life Drain')

    def deck_settings_ui(self, form):
        """Appends a Life Drain tab to Deck Settings dialog.

        Args:
            form: The form instance of the Global Settings dialog.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QWidget()
        form.lifedrain_layout = self._gui_settings_setup_layout(
            form.lifedrain_widget)
        self._create_label(
            'The <b>maximum life</b> is the time in seconds for the life bar '
            'go from full to empty.\n<b>Recover</b> is the time in seconds '
            'that is recovered after answering a card. <b>Damage</b> is the '
            'life lost when a card is answered with \'Again\'.')
        self._create_spin_box('maxLifeInput', 'Maximum life', [1, 10000])
        self._create_spin_box('recoverInput', 'Recover', [0, 1000])
        self._create_check_box('enableDamageInput', 'Enable damage')
        self._create_spin_box('damageInput', 'Damage', [-1000, 1000])
        self._create_spin_box('currentValueInput', 'Current life', [0, 10000])
        self._fill_remaining_space()
        form.tabWidget.addTab(form.lifedrain_widget, 'Life Drain')

    def custom_deck_settings_ui(self, form):
        """Adds Life Drain settings to Filtered Deck Settings dialog.

        Args:
            form: The form instance of the Filtered Deck Settings dialog.
        """
        self._form = form
        self._row = 0

        form.lifedrain_widget = self._qt.QGroupBox('Life Drain')
        form.lifedrain_layout = self._gui_settings_setup_layout(
            form.lifedrain_widget)
        self._create_spin_box('maxLifeInput', 'Maximum life', [1, 10000])
        self._create_spin_box('recoverInput', 'Recover', [0, 1000])
        self._create_check_box('enableDamageInput', 'Enable damage')
        self._create_spin_box('damageInput', 'Damage', [-1000, 1000])
        self._create_spin_box('currentValueInput', 'Current life', [0, 10000])
        form.verticalLayout.insertWidget(3, form.lifedrain_widget)

    def preferences_load(self, pref):
        """Loads Life Drain global settings into the form.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        self._conf = pref.mw.col.conf
        form = pref.form

        form.positionList.setCurrentIndex(self._get_conf('barPosition'))
        form.heightInput.setValue(self._get_conf('barHeight'))
        form.fgColorDialog.setCurrentColor(
            self._qt.QColor(self._get_conf('barFgColor')))
        form.fgColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.fgColorDialog.currentColor().name())
        form.borderRadiusInput.setValue(self._get_conf('barBorderRadius'))
        form.textList.setCurrentIndex(self._get_conf('barText'))
        form.textColorDialog.setCurrentColor(
            self._qt.QColor(self._get_conf('barTextColor')))
        form.textColorPreview.setStyleSheet(
            'QLabel { background-color: %s; }' %
            form.textColorDialog.currentColor().name())
        form.styleList.setCurrentIndex(self._get_conf('barStyle'))
        form.stopOnAnswer.setChecked(self._get_conf('stopOnAnswer'))
        form.disableAddon.setChecked(self._get_conf('disable'))

    @staticmethod
    def preferences_save(pref):
        """Saves Life Drain global settings from the form.

        Args:
            pref: The instance of the Global Settings dialog.
        """
        conf = pref.mw.col.conf
        form = pref.form

        conf['barPosition'] = form.positionList.currentIndex()
        conf['barHeight'] = form.heightInput.value()
        conf['barFgColor'] = form.fgColorDialog.currentColor().name()
        conf['barBorderRadius'] = form.borderRadiusInput.value()
        conf['barText'] = form.textList.currentIndex()
        conf['barTextColor'] = form.textColorDialog.currentColor().name()
        conf['barStyle'] = form.styleList.currentIndex()
        conf['stopOnAnswer'] = form.stopOnAnswer.isChecked()
        conf['disable'] = form.disableAddon.isChecked()
        conf.pop('barBgColor', None)
        return conf

    def deck_settings_load(self, settings, current_life):
        """Loads Life Drain deck settings into the form.

        Args:
            settings: The instance of the Deck Settings dialog.
            current_life: The current amount of life.
        """
        self._conf = settings.mw.col.decks.confForDid(settings.deck['id'])
        form = settings.form

        form.maxLifeInput.setValue(self._get_conf('maxLife'))
        form.recoverInput.setValue(self._get_conf('recover'))
        form.enableDamageInput.setChecked(self._get_conf('enableDamage'))
        form.damageInput.setValue(self._get_conf('damage'))
        form.currentValueInput.setValue(current_life)

    @staticmethod
    def deck_settings_save(settings):
        """Saves Life Drain deck settings from the form.

        Args:
            settings: The instance of the Deck Settings dialog.
        """
        conf = settings.mw.col.decks.confForDid(settings.deck['id'])
        form = settings.form

        conf['maxLife'] = form.maxLifeInput.value()
        conf['recover'] = form.recoverInput.value()
        conf['enableDamage'] = form.enableDamageInput.isChecked()
        conf['damage'] = form.damageInput.value()
        conf.pop('currentValue', None)

        deck_conf = conf.copy()
        deck_conf['currentValue'] = form.currentValueInput.value()
        return deck_conf

    def _gui_settings_setup_layout(self, widget):
        """Sets up the form layout used on Life Drain's settings UI.

        Args:
            widget: A Life Drain widget.
        """
        layout = self._qt.QGridLayout(widget)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 4)
        layout.setColumnStretch(2, 3)
        layout.setColumnStretch(3, 2)
        layout.setColumnMinimumWidth(2, 50)
        return layout

    def _create_label(self, text, color=None):
        """Creates a label in the current row of the form.

        Args:
            text: The text to be shown by the label.
            color: Optional. The color of the text in hex format.
        """
        label = self._qt.QLabel(text)
        label.setWordWrap(True)
        self._form.lifedrain_layout.addWidget(label, self._row, 0, 1, 4)
        if color:
            label.setStyleSheet('color: {}'.format(color))
        self._row += 1

    def _create_combo_box(self, cb_name, label_text, options):
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

    def _create_check_box(self, cb_name, label_text):
        """Creates a check box in the current row of the form.

        Args:
            cb_name: The name of the check box. Not visible by the user.
            label_text: A text that describes what is the check box for.
        """
        label = self._qt.QLabel(label_text)
        setattr(self._form, cb_name,
                self._qt.QCheckBox(self._form.lifedrain_widget))
        self._form.lifedrain_layout.addWidget(label, self._row, 0)
        self._form.lifedrain_layout.addWidget(getattr(self._form, cb_name),
                                              self._row, 2, 1, 2)
        self._row += 1

    def _create_spin_box(self, sb_name, label_text, val_range):
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
        self._form.lifedrain_layout.addWidget(label, self._row, 0)
        self._form.lifedrain_layout.addWidget(getattr(self._form, sb_name),
                                              self._row, 2, 1, 2)
        self._row += 1

    def _create_color_select(self, cs_name, label_text):
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

    def _fill_remaining_space(self):
        """Creates a spacer that will vertically fill all the free space."""
        spacer = self._qt.QSpacerItem(1, 1, self._qt.QSizePolicy.Minimum,
                                      self._qt.QSizePolicy.Expanding)
        self._form.lifedrain_layout.addItem(spacer, self._row, 0)
        self._row += 1

    def _get_conf(self, key):
        """Gets the value of a configuration."""
        return self._conf.get(key, DEFAULTS[key])

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
