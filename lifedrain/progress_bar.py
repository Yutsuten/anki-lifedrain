'''
Copyright (c) Yutsuten <https://github.com/Yutsuten>. Licensed under AGPL-3.0.
See the LICENCE file in the repository root for full licence text.
'''

from aqt import qt, mw

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT, DEFAULTS


class ProgressBar(object):
    '''
    Creates and manages a Progress Bar on Anki.

    This class deals with decimal values, and creates an interface with QProgressBar,
    that only acceps integer values, to make it work as expected.
    '''
    _qprogressbar = None
    _max_value = 1
    _current_value = 1
    _text_format = ''
    _dock = None

    def __init__(self, config, max_value):
        self._qprogressbar = qt.QProgressBar()
        self.set_max_value(max_value)
        self.reset_bar()
        self.set_style(config['progressBarStyle'])
        self.dock_at(config['position'])

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
            palette = qt.QPalette()
            palette.setColor(
                qt.QPalette.Base, qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                qt.QPalette.Highlight, qt.QColor(options['foregroundColor'])
            )
            palette.setColor(
                qt.QPalette.Button, qt.QColor(options['backgroundColor'])
            )
            palette.setColor(
                qt.QPalette.Window, qt.QColor(options['backgroundColor'])
            )

            self._qprogressbar.setStyle(qt.QStyleFactory.create(custom_style))
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

    def dock_at(self, place):
        '''
        Docks the bar at the specified place in the Anki window.
        '''
        bar_visible = self._qprogressbar.isVisible()

        if self._dock is not None:
            self._dock.close()

        place = POSITION_OPTIONS[place]

        if place not in POSITION_OPTIONS:
            place = DEFAULTS['barPosition']

        if place == 'Top':
            dock_area = qt.Qt.TopDockWidgetArea
        elif place == 'Bottom':
            dock_area = qt.Qt.BottomDockWidgetArea

        self._dock = qt.QDockWidget()
        twidget = qt.QWidget()
        self._dock.setWidget(self._qprogressbar)
        self._dock.setTitleBarWidget(twidget)

        existing_widgets = [
            widget for widget in mw.findChildren(qt.QDockWidget)
            if mw.dockWidgetArea(widget) == dock_area
        ]
        if not existing_widgets:
            mw.addDockWidget(dock_area, self._dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existing_widgets[0], self._dock, qt.Qt.Vertical)
        mw.web.setFocus()

        self._qprogressbar.setVisible(bar_visible)

    def __del__(self):
        self._dock.close()
