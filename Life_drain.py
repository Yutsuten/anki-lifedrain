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

############## USER CONFIGURATION START ##############

# LIFE BAR PROPERTIES
maxLife = 120 # Value in seconds
recover = 25

# LIFE BAR APPEARANCE
showPercent = False # Show the progress text percentage or not.
showNumber = False # Show the progress text as a fraction

qtxt = "#dddddd" # Percentage color, if text visible.
qbg = "#222222" # Background color of progress bar.
qfg = "#666666" # Foreground color of progress bar.
qbr = 0 # Border radius (> 0 for rounded corners).

# Optionally restricts progress bar width
maxWidth = "15px"  # (e.g. "5px". default: "")

orientationHV = Qt.Horizontal # Show bar horizontally (side to side). Use with top/bottom dockArea.
# orientationHV = Qt.Vertical # Show bar vertically (up and down). Use with right/left dockArea.

invertTF = False # If set to True, inverts and goes from right to left or top to bottom.

#dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.
dockArea = Qt.BottomDockWidgetArea # Shows bar at the bottom. Use with horizontal orientation.
#dockArea = Qt.RightDockWidgetArea # Shows bar at right. Use with vertical orientation.
#dockArea = Qt.LeftDockWidgetArea # Shows bar at left. Use with vertical orientation.

pbStyle = "" # Stylesheet used only if blank. Else uses QPalette + theme style.
'''pbStyle options (insert a quoted word above):
    -- "plastique", "windowsxp", "windows", "windowsvista", "motif", "cde", "cleanlooks"
    -- "macintosh", "gtk", or "fusion" might also work
    -- "windowsvista" unfortunately ignores custom colors, due to animation?
    -- Some styles don't reset bar appearance fully on undo. An annoyance.
    -- Themes gallery: http://doc.qt.io/qt-4.8/gallery.html'''

##############  USER CONFIGURATION END  ##############

lifeBar = None
currentLife = maxLife
drainThread = None
progressManager = ProgressManager(mw)
timer = None
updateFrequency = 1 # In seconds
nightModeImported = 0
separatorStripCss = '''
    QMainWindow::separator {
        width: 0px;
        height: 0px;
    }
    '''

pbdStyle = QStyleFactory.create("%s" % (pbStyle)) # Don't touch.

# Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.Base, QColor(qbg))
palette.setColor(QPalette.Highlight, QColor(qfg))
palette.setColor(QPalette.Button, QColor(qbg))
palette.setColor(QPalette.WindowText, QColor(qtxt))
palette.setColor(QPalette.Window, QColor(qbg))

if maxWidth:
    if orientationHV == Qt.Horizontal:
        restrictSize = "max-height: %s;" % maxWidth
    else:
        restrictSize = "max-width: %s;" % maxWidth
else:
    restrictSize = ""

try:
    import Night_Mode
    Night_Mode.nm_css_menu += separatorStripCss
    nightModeImported = 1
except ImportError:
    nightModeImported = 0

def _removeSeparatorStrip():
    global nightModeImported
    if not nightModeImported or (nightModeImported and not Night_Mode.nm_state_on):
        mw.setStyleSheet(separatorStripCss)

def _dock(lifeBar):
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    dock = QDockWidget()
    tWidget = QWidget()
    dock.setObjectName("pbDockLifeBar")
    dock.setWidget(lifeBar)
    dock.setTitleBarWidget(tWidget)

    ## Note: if there is another widget already in this dock position, we have to add ourself to the list
    # first check existing widgets
    existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]

    # then add ourselves
    mw.addDockWidget(dockArea, dock)

    # stack with any existing widgets
    if len(existing_widgets) > 0:
        mw.setDockNestingEnabled(True)
        if dockArea == Qt.TopDockWidgetArea or dockArea == Qt.BottomDockWidgetArea:
            stack_method = Qt.Vertical
        if dockArea == Qt.LeftDockWidgetArea or dockArea == Qt.RightDockWidgetArea:
            stack_method = Qt.Horizontal
        mw.splitDockWidget(dock, existing_widgets[0], stack_method)

    mw.web.setFocus()
    return dock

def _createLifeBar():
    lifeBar = QProgressBar()
    lifeBar.setRange(0, maxLife)
    lifeBar.setTextVisible(showPercent or showNumber)
    lifeBar.setInvertedAppearance(invertTF)
    lifeBar.setOrientation(orientationHV)
    if pbdStyle == None:
        lifeBar.setStyleSheet(
        '''
        QProgressBar {
            text-align:center;
            color:%s;
            background-color: %s;
            border-radius: %dpx;
            %s
        }
        QProgressBar::chunk {
            background-color: %s;
            margin: 0px;
            border-radius: %dpx;
        }
        ''' % (qtxt, qbg, qbr, restrictSize, qfg, qbr))
    else:
        lifeBar.setStyle(pbdStyle)
        lifeBar.setPalette(palette)
    _dock(lifeBar)
    return lifeBar

def _renderBar(state, oldState):
    global lifeBar, timer, updateFrequency
    if state == "overview":
        if timer:
            timer.stop()
        _updateBar()
    elif state == "deckBrowser":
        if timer:
            timer.stop()
        if lifeBar:
            lifeBar.hide()
    elif state == "review":
        if timer:
            timer.start()
        else:
            timer = progressManager.timer(updateFrequency * 1000, _drainLife, True)

def _updateBar():
    global lifeBar
    if lifeBar:
        lifeBar.hide()
        lifeBar.setValue(currentLife)
        lifeBar.show()
        _removeSeparatorStrip()

def _updateLife(recovered):
    global currentLife, maxLife
    currentLife += recovered * updateFrequency
    if currentLife > maxLife:
        currentLife = maxLife
    elif currentLife < 0:
        currentLife = 0

def _drainLife():
    _enableDrain(True)
    _updateLife(-1)
    _updateBar()

def _recoverLife():
    _enableDrain(True)
    _updateLife(recover)
    _updateBar()

def _undoReview():
    _enableDrain(True)
    # As _recoverLife is ran too, must multiply by 2
    _updateLife(-2 * recover)
    _updateBar()

def _showAnswer():
    _enableDrain(True)

def _enableDrain(enable):
    global timer
    if timer:
        if enable and not timer.isActive():
            timer.start()
        elif not enable and timer.isActive():
            timer.stop()

def _initializeBar():
    global lifeBar, currentLife, maxLife
    if not lifeBar:
        lifeBar = _createLifeBar()
    currentLife = maxLife

def keyHandler(self, evt, _old):
    global timer
    key = unicode(evt.text())
    if key == 'p' and timer:
        _enableDrain(not timer.isActive())
    else:
        return _old(self, evt)

Reviewer._keyHandler = wrap(Reviewer._keyHandler, keyHandler, "around")

addHook("profileLoaded", _initializeBar)
addHook("afterStateChange", _renderBar)
addHook("showQuestion", _recoverLife)
addHook("showAnswer", _showAnswer)
addHook("reset", _undoReview)

