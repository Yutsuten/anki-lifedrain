'''
Script with the implementation of AnkiProgressBar.
'''
from aqt import qt, mw

from .defaults import POSITION_OPTIONS, STYLE_OPTIONS, TEXT_FORMAT, DEFAULTS


class AnkiProgressBar(object):
    '''
    Creates and manages a Progress Bar on Anki.

    This class deals with decimal values, and creates an interface with QProgressBar,
    that only acceps integer values, to make it work as expected.
    '''
    _qProgressBar = None
    _maxValue = 1
    _currentValue = 1
    _textFormat = ''
    _dock = None

    def __init__(self, config, maxValue):
        self._qProgressBar = qt.QProgressBar()
        self.setMaxValue(maxValue)
        self.resetBar()
        self.setStyle(config['progressBarStyle'])
        self.dockAt(config['position'])

    def show(self):
        '''
        Shows the progress bar.
        '''
        self._qProgressBar.show()

    def hide(self):
        '''
        Hides the progress bar.
        '''
        self._qProgressBar.hide()

    def resetBar(self):
        '''
        Resets bar, setting current value to maximum.
        '''
        self._currentValue = self._maxValue
        self._validateUpdateCurrentValue()
        self._updateText()

    def setMaxValue(self, maxValue):
        '''
        Sets the maximum value for the bar.
        '''
        self._maxValue = maxValue * 10
        if self._maxValue <= 0:
            self._maxValue = 1
        self._qProgressBar.setRange(0, self._maxValue)

    def setCurrentValue(self, currentValue):
        '''
        Sets the current value for the bar.
        '''
        self._currentValue = currentValue * 10
        self._validateUpdateCurrentValue()
        self._updateText()

    def incCurrentValue(self, increment):
        '''
        Increments the current value of the bar.
        Negative values will decrement.
        '''
        self._currentValue += increment * 10
        self._validateUpdateCurrentValue()
        self._updateText()

    def getCurrentValue(self):
        '''
        Gets the current value of the bar.
        '''
        return float(self._currentValue) / 10

    def setStyle(self, options):
        '''
        Sets the style of the bar.
        '''
        self._qProgressBar.setTextVisible(options['text'] != 0)  # 0 is the index of None
        textFormat = TEXT_FORMAT[options['text']]
        if 'format' in textFormat:
            self._textFormat = textFormat['format']
            self._qProgressBar.setFormat(textFormat['format'])

        customStyle = STYLE_OPTIONS[options['customStyle']] \
            .replace(' ', '').lower()
        if customStyle != 'default':
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

            self._qProgressBar.setStyle(qt.QStyleFactory.create(customStyle))
            self._qProgressBar.setPalette(palette)
            self._qProgressBar.setStyleSheet(
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
            self._qProgressBar.setStyleSheet(
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

    def _validateUpdateCurrentValue(self):
        '''
        When updating current value, makes sure that the value is [0; max].
        '''
        if self._currentValue > self._maxValue:
            self._currentValue = self._maxValue
        elif self._currentValue < 0:
            self._currentValue = 0
        self._qProgressBar.setValue(self._currentValue)
        self._qProgressBar.update()

    def _updateText(self):
        if not self._textFormat:
            return
        if self._textFormat == 'mm:ss':
            minutes = int(self._currentValue / 600)
            seconds = int((self._currentValue / 10) % 60)
            self._qProgressBar.setFormat('{0:01d}:{1:02d}'.format(minutes, seconds))
        else:
            text = self._textFormat \
                .replace('%v', str(int(self._currentValue / 10))) \
                .replace('%m', str(int(self._maxValue / 10))) \
                .replace('%p', str(int(100 * self._currentValue / self._maxValue)))
            self._qProgressBar.setFormat(text)

    def dockAt(self, place):
        '''
        Docks the bar at the specified place in the Anki window.
        '''
        barVisible = self._qProgressBar.isVisible()

        if self._dock is not None:
            self._dock.close()

        place = POSITION_OPTIONS[place]

        if place not in POSITION_OPTIONS:
            place = DEFAULTS['barPosition']

        if place == 'Top':
            dockArea = qt.Qt.TopDockWidgetArea
        elif place == 'Bottom':
            dockArea = qt.Qt.BottomDockWidgetArea

        self._dock = qt.QDockWidget()
        tWidget = qt.QWidget()
        self._dock.setWidget(self._qProgressBar)
        self._dock.setTitleBarWidget(tWidget)

        existingWidgets = [
            widget for widget in mw.findChildren(qt.QDockWidget)
            if mw.dockWidgetArea(widget) == dockArea
        ]
        if not existingWidgets:
            mw.addDockWidget(dockArea, self._dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existingWidgets[0], self._dock, qt.Qt.Vertical)
        mw.web.setFocus()

        self._qProgressBar.setVisible(barVisible)

    def __del__(self):
        self._dock.close()
