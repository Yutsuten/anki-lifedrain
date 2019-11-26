'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT


class ProgressBar(object):
    '''
    A Progress Bar on Anki.
    This class creates an interface with QProgressBar to make it accept decimal values.
    '''
    _current_value = 1
    _dock = {}
    _max_value = 1
    _mw = None
    _qprogressbar = None
    _qt = None
    _text_format = ''

    def __init__(self, qt, mw):
        self._mw = mw
        self._qt = qt
        self._qprogressbar = qt.QProgressBar()

    def show(self):
        '''
        Shows the progress bar.
        '''
        self._qprogressbar.show()

    def hide(self):
        '''
        Hides the progress bar.
        '''
        self._qprogressbar.hide()

    def reset_bar(self):
        '''
        Resets bar, setting current value to maximum.
        '''
        self._current_value = self._max_value
        self._validate_update_current_value()
        self._update_text()

    def set_max_value(self, max_value):
        '''
        Sets the maximum value for the bar.
        '''
        self._max_value = max_value * 10
        if self._max_value <= 0:
            self._max_value = 1
        self._qprogressbar.setRange(0, self._max_value)

    def set_current_value(self, current_value):
        '''
        Sets the current value for the bar.
        '''
        self._current_value = current_value * 10
        self._validate_update_current_value()
        self._update_text()

    def inc_current_value(self, increment):
        '''
        Increments the current value of the bar.
        Negative values will decrement.
        '''
        self._current_value += increment * 10
        self._validate_update_current_value()
        if self._current_value % 10 == 0 or abs(increment) >= 1:
            self._update_text()

    def get_current_value(self):
        '''
        Gets the current value of the bar.
        '''
        return float(self._current_value) / 10

    def set_style(self, options):
        '''
        Sets the style of the bar.
        '''
        self._qprogressbar.setTextVisible(options['text'] != 0)  # 0 is the index of None
        text_format = TEXT_FORMAT[options['text']]
        if 'format' in text_format:
            self._text_format = text_format['format']
            self._qprogressbar.setFormat(text_format['format'])

        custom_style = STYLE_OPTIONS[options['customStyle']] \
            .replace(' ', '').lower()
        if custom_style != 'default':
            palette = self._qt.QPalette()
            palette.setColor(
                self._qt.QPalette.Base, self._qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                self._qt.QPalette.Highlight, self._qt.QColor(options['foregroundColor'])
            )
            palette.setColor(
                self._qt.QPalette.Button, self._qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                self._qt.QPalette.Window, self._qt.QColor(options['backgroundColor'])
            )

            self._qprogressbar.setStyle(self._qt.QStyleFactory.create(custom_style))
            self._qprogressbar.setPalette(palette)
            self._qprogressbar.setStyleSheet(
                '''
                QProgressBar {
                    max-height: %spx;
                }
                '''
                % (
                    options['height'],
                )
            )
        else:
            self._qprogressbar.setStyleSheet(
                '''
                QProgressBar {
                    text-align:center;
                    background-color: %s;
                    border-radius: %dpx;
                    max-height: %spx;
                    color: %s;
                }
                QProgressBar::chunk {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                '''
                % (
                    options['backgroundColor'],
                    options['borderRadius'],
                    options['height'],
                    options['textColor'],
                    options['foregroundColor'],
                    options['borderRadius']
                )
            )

    def dock_at(self, position):
        '''
        Docks the bar at the specified position in the Anki window.
        '''
        if 'position' in self._dock and self._dock['position'] == position:
            return

        self._dock['position'] = position
        bar_visible = self._qprogressbar.isVisible()

        if 'widget' in self._dock:
            self._dock['widget'].close()
            self._dock['widget'].deleteLater()

        position = POSITION_OPTIONS[position]
        if position == 'Top':
            dock_area = self._qt.Qt.TopDockWidgetArea
        elif position == 'Bottom':
            dock_area = self._qt.Qt.BottomDockWidgetArea

        self._dock['widget'] = self._qt.QDockWidget()
        twidget = self._qt.QWidget()
        self._dock['widget'].setWidget(self._qprogressbar)
        self._dock['widget'].setTitleBarWidget(twidget)

        existing_widgets = [
            widget for widget in self._mw.findChildren(self._qt.QDockWidget)
            if self._mw.dockWidgetArea(widget) == dock_area
        ]
        if not existing_widgets:
            self._mw.addDockWidget(dock_area, self._dock['widget'])
        else:
            self._mw.setDockNestingEnabled(True)
            self._mw.splitDockWidget(
                existing_widgets[0],
                self._dock['widget'],
                self._qt.Qt.Vertical
            )
        self._mw.web.setFocus()

        self._qprogressbar.setVisible(bar_visible)

    def _validate_update_current_value(self):
        '''
        When updating current value, makes sure that the value is [0; max].
        '''
        if self._current_value > self._max_value:
            self._current_value = self._max_value
        elif self._current_value < 0:
            self._current_value = 0
        self._qprogressbar.setValue(self._current_value)
        self._qprogressbar.update()

    def _update_text(self):
        if not self._text_format:
            return
        if self._text_format == 'mm:ss':
            minutes = int(self._current_value / 600)
            seconds = int((self._current_value / 10) % 60)
            self._qprogressbar.setFormat('{0:01d}:{1:02d}'.format(minutes, seconds))
        else:
            current_value = int(self._current_value / 10)
            if self._current_value % 10 != 0:
                current_value += 1
            max_value = int(self._max_value / 10)
            text = self._text_format \
                .replace('%v', str(current_value)) \
                .replace('%m', str(max_value)) \
                .replace('%p', str(int(100 * current_value / max_value)))
            self._qprogressbar.setFormat(text)
