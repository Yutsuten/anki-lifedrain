# Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
# See the LICENCE file in the repository root for full licence text.

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Literal

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT

if TYPE_CHECKING:
    from aqt.main import AnkiQt


class ProgressBar:
    """Implements a Progress Bar to be used on Anki.

    Creates an interface with QProgressBar to make its usage on Anki easier. It
    also adds a (limited) ability to use decimal values as the current value.
    """

    def __init__(self, mw: AnkiQt, qt: Any):
        """Initializes a QProgressBar and keeps main window and PyQt references.

        Args:
            mw: Anki's main window.
            qt: The PyQt library.
        """
        self._mw = mw
        self._qt = qt
        self._qprogressbar = qt.QProgressBar()
        self._current_value: float = 1
        self._dock: dict[str, Any] = {}
        self._max_value: float = 1
        self._text_format: str = ''
        self._current_bar_color: str = ''
        self._bar_options: dict[str, Any] = {}

    def set_visible(self, *, visible: bool) -> None:
        """Sets the visibility of the Progress Bar.

        Args:
            visible: A flag indicating if the Progress Bar should be visible.
        """
        self._qprogressbar.setVisible(visible)

    def reset_bar(self) -> None:
        """Resets the current value back to the maximum."""
        self._current_value = self._max_value
        self._validate_current_value()
        self._update_text()
        self._update_bar_color()

    def set_max_value(self, max_value: float) -> None:
        """Sets the maximum value for the bar.

        Args:
            max_value: The maximum value of the bar. Up to 1 decimal place.
        """
        self._max_value = max(1, max_value)
        self._qprogressbar.setRange(0, self._max_value * 10)

    def set_current_value(self, current_value: float) -> None:
        """Sets the current value for the bar.

        Args:
            current_value: The current value of the bar. Up to 1 decimal place.
        """
        self._current_value = current_value
        self._validate_current_value()
        self._update_text()
        self._update_bar_color()

    def inc_current_value(self, increment: float) -> None:
        """Increments the current value of the bar.

        Args:
            increment: A positive or negative number. Up to 1 decimal place.
        """
        self._current_value += increment
        self._validate_current_value()
        self._update_text()
        self._update_bar_color()

    def get_current_value(self) -> float:
        """Gets the current value of the bar."""
        return self._current_value

    def set_style(self, options: dict[str, Any]) -> None:
        """Sets the styling of the Progress Bar.

        Args:
            options: A dictionary with bar styling information.
        """
        self._bar_options = options
        text_format = TEXT_FORMAT[options['text']]
        self._qprogressbar.setTextVisible('format' in text_format)
        if 'format' in text_format:
            self._text_format = text_format['format']
            self._qprogressbar.setFormat(text_format['format'])
        self._current_bar_color = ''
        self._update_bar_color()
        self._qprogressbar.setInvertedAppearance(options['invert'])

    def dock_at(self, position_index: Literal[0, 1]) -> None:
        """Docks the bar at the specified position in the Anki window.

        Args:
            position_index: The position where the Progress Bar will be placed.
        """
        if 'position' in self._dock and self._dock['position'] == position_index:
            return

        self._dock['position'] = position_index
        bar_visible = self._qprogressbar.isVisible()

        if 'widget' in self._dock:
            self._dock['widget'].close()
            self._dock['widget'].deleteLater()

        position = POSITION_OPTIONS[position_index]
        if position == 'Top':
            dock_area = self._qt.Qt.DockWidgetArea.TopDockWidgetArea
        else:  # position == 'Bottom':
            dock_area = self._qt.Qt.DockWidgetArea.BottomDockWidgetArea

        self._dock['widget'] = self._qt.QDockWidget()
        self._dock['widget'].setWidget(self._qprogressbar)
        self._dock['widget'].setTitleBarWidget(self._qt.QWidget())

        existing_widgets = [
            widget for widget in self._mw.findChildren(self._qt.QDockWidget)
            if self._mw.dockWidgetArea(widget) == dock_area  # pyright: ignore [reportGeneralTypeIssues]
        ]
        if not existing_widgets:
            self._mw.addDockWidget(dock_area, self._dock['widget'])
        else:
            self._mw.setDockNestingEnabled(enabled=True)
            self._mw.splitDockWidget(
                existing_widgets[0],  # pyright: ignore [reportGeneralTypeIssues]
                self._dock['widget'],
                self._qt.Qt.Vertical,
            )
        self._mw.web.setFocus()
        self._qprogressbar.setVisible(bar_visible)

    def _validate_current_value(self) -> None:
        """Asserts that the current value is between [0; max]."""
        if self._current_value > self._max_value:
            self._current_value = self._max_value
        elif self._current_value < 0:
            self._current_value = 0
        self._qprogressbar.setValue(int(self._current_value * 10))
        self._qprogressbar.update()

    def _update_text(self) -> None:
        """Updates the Progress Bar text."""
        if not self._text_format:
            return
        if self._text_format == 'mm:ss':
            minutes = int(self._current_value / 60)
            seconds = int(self._current_value) % 60
            self._qprogressbar.setFormat(f'{minutes:01d}:{seconds:02d}')
        else:
            current_value = math.ceil(self._current_value)
            max_value = int(self._max_value)
            text = self._text_format
            text = text.replace('%v', str(current_value))
            text = text.replace('%m', str(max_value))
            text = text.replace('%p', str(int(100 * current_value / max_value)))
            self._qprogressbar.setFormat(text)

    def _update_bar_color(self) -> None:
        """Updates the Progress Bar color styling."""
        options = self._bar_options

        life_percentage = self._current_value / self._max_value * 100
        bar_color = options['fgColor']
        if life_percentage <= options['thresholdDanger']:
            bar_color = options['fgColorDanger']
        elif life_percentage <= options['thresholdWarn']:
            bar_color = options['fgColorWarn']

        if self._current_bar_color == bar_color:
            return

        self._current_bar_color = bar_color
        custom_style = STYLE_OPTIONS[options['customStyle']] \
            .replace(' ', '').lower()
        if custom_style != 'default':
            qstyle = self._qt.QStyleFactory.create(custom_style)
            self._qprogressbar.setStyle(qstyle)

            palette = self._qt.QPalette()
            fg_color = self._qt.QColor(bar_color)
            palette.setColor(self._qt.QPalette.Highlight, fg_color)

            if 'bgColor' in options:
                bg_color = self._qt.QColor(options['bgColor'])
                palette.setColor(self._qt.QPalette.Base, bg_color)
                palette.setColor(self._qt.QPalette.Window, bg_color)

            self._qprogressbar.setPalette(palette)

            bar_elem_dict = {'max-height': f'{options["height"]}px'}
            bar_elem = self._dict_to_css(bar_elem_dict)
            self._qprogressbar.setStyleSheet(
                f'QProgressBar {{ {bar_elem} }}')
        else:
            bar_elem_dict = {
                'text-align': 'center',
                'border-radius': f'{options["borderRadius"]}px',
                'max-height': f'{options["height"]}px',
                'color': options['textColor']}

            if 'bgColor' in options:
                bar_elem_dict['background-color'] = options['bgColor']

            bar_elem = self._dict_to_css(bar_elem_dict)
            bar_chunk = self._dict_to_css({
                'background-color': bar_color,
                'margin': '0px',
                'border-radius': f'{options["borderRadius"]}px'})

            self._qprogressbar.setStyleSheet(
                f'QProgressBar {{ {bar_elem} }}'
                f'QProgressBar::chunk {{ {bar_chunk} }}')

    @staticmethod
    def _dict_to_css(dictionary: dict[str, str]) -> str:
        """Convert a python dict to a stylesheet.

        Args:
            dictionary: The python dics to be converted to CSS.
        """
        css = ''
        for key, value in dictionary.items():
            css += f'\n{key}: {value};'
        return css
