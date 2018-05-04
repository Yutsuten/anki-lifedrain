"""
Anki Add-on: Life Drain
Add a bar that is reduced as time passes. Completing reviews recovers it.

**
Some of the code used here was originally done by Glutanimate, from the
Addon Progress Bar.
For this reason, I copied the copyright of that Addon and appended my name.
**

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
            (c) Yutsuten 2018 <https://github.com/Yutsuten>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from anki.hooks import addHook, wrap
from aqt.qt import *
from aqt import mw
from aqt.progress import ProgressManager
from aqt.utils import showInfo
from aqt.reviewer import Reviewer


progressBarStyle = {
    'height': 15,
    'textColor': '#dddddd',
    'backgroundColor': '#222222',
    'foregroundColor': '#666666',
    'borderRadius': 0,
    'customStyle': 'default'
}

class AnkiProgressBar(object):
    _qProgressBar = None
    _maxValue = 1
    _currentValue = 1

    def __init__(self, maxValue, style, dockPlace):
        self._qProgressBar = QProgressBar()
        self.setMaxValue(maxValue)
        self.resetBar()
        self.setTextVisible(False)
        self.setStyle(style)
        self._dockAt(dockPlace)

    def resetBar(self):
        self._currentValue = self._maxValue

    def setMaxValue(self, maxValue):
        self._maxValue = maxValue
        if (self._maxValue <= 0):
            self._maxValue = 1
        self._qProgressBar.setRange(0, self._maxValue)

    def setCurrentValue(self, currentValue):
        self._currentValue = currentValue
        if (self._currentValue > self._maxValue):
            self._currentValue = self._maxValue
        elif (self._currentValue < 0):
            self._currentValue = 0
        self._qProgressBar.setValue(self._currentValue)

    def setTextVisible(self, flag):
        self._qProgressBar.setTextVisible(flag)

    def setStyle(self, options):
        if (options['customStyle'] != 'default'):
            palette = QPalette()
            palette.setColor(QPalette.Base, QColor(options['backgroundColor']))
            palette.setColor(QPalette.Highlight, QColor(options['foregroundColor']))
            palette.setColor(QPalette.Button, QColor(options['backgroundColor']))
            palette.setColor(QPalette.WindowText, QColor(options['textColor']))
            palette.setColor(QPalette.Window, QColor(options['backgroundColor']))

            pbdStyle = QStyleFactory.create("%s" % (options['customStyle']))

            self._qProgressBar.setStyle(pbdStyle)
            self._qProgressBar.setPalette(palette)
        else:
            self._qProgressBar.setStyleSheet(
                '''
                QProgressBar {
                    text-align:center;
                    color: %s;
                    background-color: %s;
                    border-radius: %dpx;
                    max-height: %spx;
                }
                QProgressBar::chunk {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                '''
                % (
                    options['textColor'],
                    options['backgroundColor'],
                    options['borderRadius'],
                    options['height'],
                    options['foregroundColor'],
                    options['borderRadius']
                )
            )

    def _dockAt(self, place):
        """
        - Valid place values: top, bottom
        Default to bottom
        """
        if (place not in ['top', 'bottom']):
            place = 'bottom'

        if (place == 'top'):
            dockArea = Qt.TopDockWidgetArea
        elif (place == 'bottom'):
            dockArea = Qt.BottomDockWidgetArea

        dock = QDockWidget()
        tWidget = QWidget()
        dock.setWidget(self._qProgressBar)
        dock.setTitleBarWidget(tWidget)

        existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]
        if (len(existing_widgets) == 0):
            mw.addDockWidget(dockArea, dock)
        else:
            mw.setDockNestingEnabled(True)
            mw.splitDockWidget(existing_widgets[0], dock, Qt.Vertical)
        mw.web.setFocus()


lifeBar = AnkiProgressBar(100, progressBarStyle, 'bottom')
lifeBar.setCurrentValue(60)

