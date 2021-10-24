#-----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2021 - Grum999
#
# A toolkit to make pykrita plugin coding easier :-)
# -----------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.
# If not, see https://www.gnu.org/licenses/
# -----------------------------------------------------------------------------


import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from ..modules.timeutils import Timer
from .wstandardcolorselector import WStandardColorSelector
from ..pktk import *

class WToolBox(QWidget):
    """The widget toolbox is a dialog box that can be used as a tool box

    Provide a title bar with button "compact" and "close"

    Also provide a bottom toolbar with sizegrip
    """
    compactModeUpdated=Signal(bool) # when color is changed from user interface
    compactModeChanged=Signal(bool) # when color is changed programmatically
    pinnedModeUpdated=Signal(bool) # when pinned mode is changed programmatically
    pinnedModeChanged=Signal(bool) # when pinned mode is changed programmatically
    geometryUpdated=Signal(QRect)   # when geometry has been modified (no tracking)


    __BBAR_TOOLBUTTON_CSS="""
QToolButton {
border-radius: 2px;
}
QToolButton:hover {
border: none;
background-color: rgba(255,255,255,50);
}
QToolButton:checked {
border: none;
background-color: rgba(0,0,0,50);
}            """


    def __init__(self, parent=None):
        if parent is None:
            parent=Krita.instance().activeWindow().qwindow()

        super(WToolBox, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

        self.__globalPos = None
        self.__moving=False
        self.__moved=False
        self.__factor=0.85
        self.__isCompact=False
        self.__isPinned=False
        self.__colorIndex=WStandardColorSelector.COLOR_NONE
        self.__centralDefaultWidget=QLabel(self)
        self.__centralWidget=self.__centralDefaultWidget

        self.__buildUi()

    def __buildUi(self):
        """Build window interface"""
        self.__layoutMain=QVBoxLayout(self)
        self.__layoutMain.setContentsMargins(0,0,0,0)
        self.__layoutMain.setSpacing(1)

        self.__layoutBBar=QHBoxLayout(self)
        self.__layoutBBar.setContentsMargins(1,1,1,1)
        self.__layoutBBar.setSpacing(1)


        self.__titleBar=WToolBoxTitleBar(self, self.__isCompact)
        self.__titleBar.compactModeUpdated.connect(self.__setCompact)
        self.__titleBar.pinnedModeUpdated.connect(self.__setPinned)

        self.__sizeGrip=QSizeGrip(self)
        self.__sizeGrip.installEventFilter(self)

        self.__layoutBBar.addWidget(self.__sizeGrip, 0, Qt.AlignBottom|Qt.AlignRight)

        self.__bottomBar=QWidget(self)
        self.__bottomBar.setLayout(self.__layoutBBar)
        self.__bottomBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.__layoutMain.addWidget(self.__titleBar)
        self.__layoutMain.addWidget(self.__centralDefaultWidget)
        self.__layoutMain.addWidget(self.__bottomBar)

        self.setLayout(self.__layoutMain)

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __setCompact(self, value):
        """Slot from title bar compactModeUpdated()"""
        if isinstance(value, bool) and value!=self.__isCompact:
            self.__isCompact=value
            self.__updateUi()
            self.compactModeUpdated.emit(value)

    def __setPinned(self, value):
        """Slot from title bar pinnedModeUpdated()"""
        if isinstance(value, bool) and value!=self.__isPinned:
            self.__isPinned=value
            self.pinnedModeUpdated.emit(value)

    def __updateUi(self):
        #self.__bottomBar.resize(self.__bottomBar.width(), self.__titleBar.height())
        self.__bottomBar.setFixedHeight(self.__titleBar.height())

    def eventFilter(self, source, event):
        if source==self.__sizeGrip and isinstance(event, QMouseEvent):
            if event.type()==QEvent.MouseButtonRelease:
                self.geometryUpdated.emit(self.geometry())

        return super(WToolBox, self).eventFilter(source, event)

    def mousePressEvent(self, event):
        """User press anywhere on note window, so enter on drag mode"""
        self.__globalPos=event.globalPos()
        self.__moved=False
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """If in drag mode, move current note window"""
        if self.__globalPos and not self.__moving:
            self.__moving=True
            delta = QPoint(event.globalPos() - self.__globalPos)

            # -- the really dirty trick...
            # Don't really know why but without it, when moving window on my
            # secondary screen there's a really weird "shake" effect and
            # defined position sometime gets out of hand...
            #
            # having a 1ms timer is enough to fix the problem
            # suspecting something with too much event or something like that...
            Timer.sleep(1)
            # --

            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.__globalPos = event.globalPos()
            self.__moving=False
            self.__moved=True

    def mouseReleaseEvent(self, event):
        """Exit drag mode"""
        if self.__moved:
            self.__moved=False
            self.geometryUpdated.emit(self.geometry())

        self.__globalPos=None
        self.setCursor(Qt.ArrowCursor)

    def setCenteredPosition(self):
        tmpFrameGeometry = self.frameGeometry()
        # center window on current screen
        # tmpFrameGeometry.moveCenter(QDesktopWidget().availableGeometry().center())
        # center window on Krita window
        tmpFrameGeometry.moveCenter(Krita.instance().activeWindow().qwindow().geometry().center())
        self.move(tmpFrameGeometry.topLeft())

    def isCompact(self):
        """Is compact mode activated"""
        return self.__isCompact

    def setCompact(self, value):
        """Set compact mode"""
        if isinstance(value, bool) and value!=self.__isCompact:
            self.__isCompact=value
            self.__titleBar.setCompact(value)
            self.__updateUi()
            self.compactModeChanged.emit(value)

    def isPinned(self):
        """Is pinned mode activated"""
        return self.__isPinned

    def setPinned(self, value):
        """Set pinned mode"""
        if isinstance(value, bool) and value!=self.__isPinned:
            self.__isPinned=value
            self.__titleBar.setPinned(value)
            self.pinnedModeChanged.emit(value)

    def centralWidget(self):
        """Return current central widget"""
        return self.__centralWidget

    def setCentralWidget(self, widget):
        """Set central widget for window"""
        if widget is None:
            if self.__centralWidget!=self.__centralDefaultWidget:
                self.__layoutMain.replaceWidget(self.__centralWidget, self.__centralDefaultWidget)
                self.__centralWidget=None
        elif isinstance(widget, QWidget):
            if self.__centralWidget!=widget:
                self.__layoutMain.replaceWidget(self.__centralWidget, widget)
                self.__centralWidget=widget

    def bottomBarClear(self):
        """Remove all items in bottom bar (except size grip)"""
        while self.__layoutBBar.count()>1:
            self.__layoutBBar.removeItem(self.self.__layoutBBar.itemAt(0))

    def bottomBarAddWidget(self, widget, applyCss=True):
        """Add a widget in bottom bar"""
        if isinstance(widget, QToolButton):
            if applyCss==True:
                widget.setStyleSheet(WToolBox.__BBAR_TOOLBUTTON_CSS)
            elif isinstance(applyCss, str):
                widget.setStyleSheet(applyCss)
            # do not use addWidget() because of resize item
            self.__layoutBBar.insertWidget(self.__layoutBBar.count()-1, widget)
        elif isinstance(widget, QWidget):
            if isinstance(applyCss, str):
                widget.setStyleSheet(applyCss)
            # do not use addWidget() because of resize item
            self.__layoutBBar.insertWidget(self.__layoutBBar.count()-1, widget)

    def bottomBarAddStretch(self, stretch=0):
        """Add a stretch in bottom bar"""
        # do not use addStretch() because of resize item
        self.__layoutBBar.insertStretch(self.__layoutBBar.count()-1, stretch)

    def title(self):
        """Return title"""
        return self.__titleBar.title()

    def setTitle(self, value):
        """Set title"""
        self.__titleBar.setTitle(value)

    def colorIndex(self):
        """Return current title color index"""
        return self.__colorIndex

    def setColorIndex(self, colorIndex):
        """Set title color index content"""
        if WStandardColorSelector.isValidColorIndex(colorIndex) and colorIndex!=self.__colorIndex:
            self.__colorIndex=colorIndex
            self.__titleBar.setColorIndex(self.__colorIndex)


class WToolBoxTitleBar(QWidget):
    compactModeUpdated=Signal(bool) # when compact mode is changed from user interface
    pinnedModeUpdated=Signal(bool) # when pinned mode is changed programmatically

    __TOOLBUTTON_CSS="""
QToolButton {
border-radius: 2px;
}
QToolButton:hover {
border: none;
background-color: rgba(255,255,255,50);
}
        """

    def __init__(self, parent, compact=False, pinned=False):
        super(WToolBoxTitleBar, self).__init__(parent)
        self.__parent=parent
        self.__layoutMain=QHBoxLayout()
        self.__layoutMain.setContentsMargins(1,1,1,1)
        self.__layoutMain.setSpacing(1)

        self.__inInit=True

        self.__factor=0.95
        self.__height=0
        self.__compact=None
        self.__pinned=None

        self.__colorIndex=WStandardColorSelector.COLOR_NONE

        self.__lblTitle = QLabel("")
        self.__lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.__lblTitle.minimumSizeHint=self.minimumSizeHint

        self.__font = self.font()
        self.__originalFontSizePt=self.__font.pointSizeF()
        self.__originalFontSizePx=self.__font.pixelSize()

        self.__fntMetric=QFontMetrics(self.__font)

        self.__btClose = QToolButton()
        self.__btClose.clicked.connect(self.__parent.close)
        self.__btClose.setToolTip(i18n('Close note'))
        self.__btClose.setIcon(QIcon(':/pktk/images-white/normal/close'))
        self.__btClose.setFocusPolicy(Qt.NoFocus)
        self.__btClose.setAutoRaise(True)
        self.__btClose.setStyleSheet(WToolBoxTitleBar.__TOOLBUTTON_CSS)

        self.__btCompact = QToolButton()
        self.__btCompact.clicked.connect(self.setCompact)
        self.__btCompact.setToolTip(i18n('Compact view'))
        self.__btCompact.setIcon(QIcon(':/pktk/images-white/normal/compact_on'))
        self.__btCompact.setFocusPolicy(Qt.NoFocus)
        self.__btCompact.setAutoRaise(True)
        self.__btCompact.setCheckable(True)
        self.__btCompact.setStyleSheet(WToolBoxTitleBar.__TOOLBUTTON_CSS)

        self.__btPinned = QToolButton()
        self.__btPinned.clicked.connect(self.setPinned)
        self.__btPinned.setToolTip(i18n('Compact view'))
        self.__btPinned.setIcon(QIcon(':/pktk/images-white/disabled/pinned'))
        self.__btPinned.setFocusPolicy(Qt.NoFocus)
        self.__btPinned.setAutoRaise(True)
        self.__btPinned.setCheckable(True)
        self.__btPinned.setStyleSheet(WToolBoxTitleBar.__TOOLBUTTON_CSS)

        self.__title=''
        self.__color=None

        self.setCompact(compact)
        self.setPinned(pinned)

        self.__layoutMain.addWidget(self.__lblTitle)
        self.__layoutMain.addWidget(self.__btPinned)
        self.__layoutMain.addWidget(self.__btCompact)
        self.__layoutMain.addWidget(self.__btClose)

        self.setCompact(False)

        self.setLayout(self.__layoutMain)
        self.__inInit=False

    def minimumSizeHint(self):
        return QSize(0, self.__height)

    def setCompact(self, value):
        if value==self.__compact:
            return

        self.__compact=value

        if value:
            self.__factor=0.65
            self.__btCompact.setChecked(True)
            self.__btCompact.setIcon(QIcon(':/pktk/images-white/normal/compact_off'))
            self.__btCompact.setToolTip(i18n('Normal view'))
        else:
            self.__factor=0.95
            self.__btCompact.setChecked(False)
            self.__btCompact.setIcon(QIcon(':/pktk/images-white/normal/compact_on'))
            self.__btCompact.setToolTip(i18n('Compact view'))

        if self.__originalFontSizePt>-1:
            self.__font.setPointSizeF(self.__originalFontSizePt*self.__factor)
        else:
            self.__font.setPixelSize(int(self.__originalFontSizePx*self.__factor))

        self.__fntMetric=QFontMetrics(self.__font)
        self.__height=self.__fntMetric.height()

        self.setMinimumSize(1, self.__height)

        self.__lblTitle.setFont(self.__font)
        self.__btClose.setFixedSize(self.__height, self.__height)
        self.__btClose.setIconSize(QSize(self.__height-2,self.__height-2))
        self.__btCompact.setFixedSize(self.__height, self.__height)
        self.__btCompact.setIconSize(QSize(self.__height-2,self.__height-2))
        self.__btPinned.setFixedSize(self.__height, self.__height)
        self.__btPinned.setIconSize(QSize(self.__height-2,self.__height-2))

        if not self.__inInit:
            self.compactModeUpdated.emit(value)

    def setPinned(self, value):
        """Set toolbox pinned"""
        if value==self.__pinned:
            return

        self.__pinned=value

        if value:
            self.__btPinned.setChecked(True)
            self.__btPinned.setIcon(QIcon(':/pktk/images-white/normal/pinned'))
            self.__btPinned.setToolTip(i18n('Unpin'))
        else:
            self.__btPinned.setChecked(False)
            self.__btPinned.setIcon(QIcon(':/pktk/images-white/disabled/pinned'))
            self.__btPinned.setToolTip(i18n('Pin'))

        if not self.__inInit:
            self.pinnedModeUpdated.emit(value)

    def __updateTitle(self):
        """Update title ellipsis"""
        self.__lblTitle.setText(self.__fntMetric.elidedText(self.__title, Qt.ElideRight, self.__lblTitle.width() - 2))

    def title(self):
        """Return current title"""
        return self.__lblTitle.text()

    def setTitle(self, title):
        """Set title bar content"""
        if isinstance(title, str) and title!=self.__title:
            self.__title=title
            self.__lblTitle.setText(title)

    def colorIndex(self):
        """Return current title color index"""
        return self.__colorIndex

    def setColorIndex(self, colorIndex):
        """Set title color index content"""
        if WStandardColorSelector.isValidColorIndex(colorIndex) and colorIndex!=self.__colorIndex:
            self.__colorIndex=colorIndex

            if colorIndex==WStandardColorSelector.COLOR_NONE:
                self.setAutoFillBackground(False)
            else:
                palette=self.__lblTitle.palette()
                self.setAutoFillBackground(True)
                palette.setColor(QPalette.Window, WStandardColorSelector.getColor(colorIndex).darker(200))
                palette.setColor(QPalette.WindowText, Qt.white)
                self.setPalette(palette)

    def resizeEvent(self, event):
        """Update title ellipsis when resized"""
        self.__updateTitle()

    def height(self):
        """Return current applied height"""
        return self.__height
