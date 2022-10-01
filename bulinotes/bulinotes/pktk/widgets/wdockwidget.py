# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The wconsole module provides a console like output widget
# Note: it's not a TTY console!
#
# Main class from this module
#
# - WConsole:
#       Widget
#       The main console widget
#
# - WConsoleType:
#       Information type for console output line
#
# - WConsoleUserData:
#       User data associated with an output line
#
# - WConsoleGutterArea:
#       Widget to render console gutter
#
# -----------------------------------------------------------------------------

import re

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QVBoxLayout,
        QWidget
    )

from .wcolorselector import (
        WColorPicker,
        WColorComplementary
    )

from ..modules.imgutils import buildIcon
from ..pktk import *


class WDockWidget(QDockWidget):
    """An extension of dock widget"""

    def __init__(self, name, parent):
        super(WDockWidget, self).__init__(name, parent)
        self.topLevelChanged.connect(self.__updateAllDocWidgets)
        self.dockLocationChanged.connect(self.__updateAllDocWidgets)

        self.__widget = QWidget(self)
        self.__sizeGrip = QSizeGrip(self)
        self.__sizeGrip.hide()

        self.__titleBar = WDockWidgetTitleBar(name, self)
        self.setTitleBarWidget(self.__titleBar)

        QDockWidget.setWidget(self, self.__widget)

    def __updateAllDocWidgets(self, area):
        """Dockwidget location/undock has been modified, need to check title for all dock widgets"""
        for dockWidget in self.parentWidget().findChildren(WDockWidget):
            dockWidget.updateStatus()

    def widget(self):
        """--Override default function--

        Return widget"""
        return self.__widget

    def setWidget(self, widget):
        """Override default function"""
        layout = QVBoxLayout(self.__widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        layout.addWidget(self.__sizeGrip, 0, Qt.AlignBottom | Qt.AlignRight)
        self.__widget.setLayout(layout)

    def updateStatus(self):
        """Update title bar/size grip status according to current docked/undocked state"""
        if self.isFloating():
            self.__sizeGrip.show()
        else:
            self.__sizeGrip.hide()

        self.__titleBar.updateStatus()

    def displayTitle(self):
        """Return if title need to be displayed or not

        Undocked state: True
        Docked state: False if tabified otherwise True
        """
        if self.isFloating():
            return True

        groupedDock = self.parentWidget().tabifiedDockWidgets(self)
        if len(groupedDock) > 0:
            # can't just check list len because when a dockWidget is undocked,
            # the dockWidget is still provided in returned list (shouldn't be in list
            # as undocked...)
            for dockWidget in groupedDock:
                if not dockWidget.isFloating():
                    return False
        return True


class WDockWidgetTitleBar(QWidget):
    """A custom title bar for dockwidget"""

    __TOOLBUTTON_CSS = """
QToolButton {
border-radius: 2px;
}
QToolButton:hover {
border: none;
background-color: rgba(255,255,255,50);
}
        """

    def __init__(self, title, parent):
        super(WDockWidgetTitleBar, self).__init__(parent)
        self.__parent = parent
        self.__title = ''

        self.__layoutMain = QHBoxLayout()
        self.__layoutMain.setContentsMargins(3, 2, 1, 1)
        self.__layoutMain.setSpacing(1)

        self.__lblTitle = QLabel(self)
        self.__lblTitle.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        self.__font = self.font()
        self.__font.setPointSizeF(self.__font.pointSizeF()*0.9)
        self.__fntMetric = QFontMetrics(self.__font)
        self.__height = self.__fntMetric.height()

        self.__btClose = QToolButton()
        self.__btClose.clicked.connect(self.__parent.close)
        self.__btClose.setToolTip(i18n('Close'))
        self.__btClose.setIcon(buildIcon('pktk:close'))
        self.__btClose.setFocusPolicy(Qt.NoFocus)
        self.__btClose.setAutoRaise(True)
        self.__btClose.setStyleSheet(WDockWidgetTitleBar.__TOOLBUTTON_CSS)

        self.__btPinned = QToolButton()
        self.__btPinned.clicked.connect(self.__setPinned)
        self.__btPinned.setToolTip(i18n('Unpin from dock'))
        self.__btPinned.setIcon(buildIcon('pktk:unpinned'))
        self.__btPinned.setFocusPolicy(Qt.NoFocus)
        self.__btPinned.setAutoRaise(True)
        self.__btPinned.setStyleSheet(WDockWidgetTitleBar.__TOOLBUTTON_CSS)

        self.__btUnpinned = QToolButton()
        self.__btUnpinned.clicked.connect(self.__setPinned)
        self.__btUnpinned.setToolTip(i18n('Pin to dock'))
        self.__btUnpinned.setIcon(buildIcon('pktk:pinned'))
        self.__btUnpinned.setFocusPolicy(Qt.NoFocus)
        self.__btUnpinned.setAutoRaise(True)
        self.__btUnpinned.setStyleSheet(WDockWidgetTitleBar.__TOOLBUTTON_CSS)
        self.__btUnpinned.hide()

        self.__layoutMain.addWidget(self.__lblTitle)
        self.__layoutMain.addWidget(self.__btPinned)
        self.__layoutMain.addWidget(self.__btUnpinned)
        self.__layoutMain.addWidget(self.__btClose)

        self.setMinimumSize(1, self.__height)

        self.__lblTitle.setFont(self.__font)
        self.__btClose.setFixedSize(self.__height, self.__height)
        self.__btClose.setIconSize(QSize(self.__height-2, self.__height-2))
        self.__btPinned.setFixedSize(self.__height, self.__height)
        self.__btPinned.setIconSize(QSize(self.__height-2, self.__height-2))
        self.__btUnpinned.setFixedSize(self.__height, self.__height)
        self.__btUnpinned.setIconSize(QSize(self.__height-2, self.__height-2))

        self.setTitle(title)
        self.setLayout(self.__layoutMain)

    def __updateTitle(self):
        """Update title ellipsis"""
        if self.__parent.displayTitle():
            self.__lblTitle.setText(self.__fntMetric.elidedText(self.__title, Qt.ElideRight, self.__lblTitle.width() - 2))
        else:
            self.__lblTitle.setText('')

    def __setPinned(self, value):
        """Set docker pinned/unpinned"""
        self.__parent.setFloating(not self.__parent.isFloating())

    def updateStatus(self):
        """Update title bar according to current docked/undocked status"""
        if self.__parent.isFloating():
            self.__btPinned.hide()
            self.__btUnpinned.show()
        else:
            self.__btPinned.show()
            self.__btUnpinned.hide()

        self.__updateTitle()

    def title(self):
        """Return current title"""
        return self.__lblTitle.text()

    def setTitle(self, title):
        """Set title bar content"""
        if isinstance(title, str) and title != self.__title:
            self.__title = title
            self.__lblTitle.setText(title)
            self.__updateTitle()

    def resizeEvent(self, event):
        """Update title ellipsis when resized"""
        self.__updateTitle()
