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
# The wstandardcolorselector module provides a widget similar to Krita's
# standard color layer selector
#
# Main class from this module
#
# - WStandardColorSelector:
#       Widget
#       A color selector
#
# -----------------------------------------------------------------------------

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QPushButton
    )


class WStandardColorSelector(QWidget):
    """A button to choose color from standard interface color (same used for layer/frame color)"""
    colorUpdated = Signal(int)       # when color is changed from user interface
    colorChanged = Signal(int)       # when color is changed programmatically

    COLOR_NONE = 0
    COLOR_BLUE = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_ORANGE = 4
    COLOR_MAROON = 5
    COLOR_RED = 6
    COLOR_PURPLE = 7
    COLOR_GRAY = 8
    NB_COLORS = 9

    @staticmethod
    def getColor(colorIndex):
        """Return QColor for given color index"""
        if colorIndex == WStandardColorSelector.COLOR_BLUE:
            return QColor(98, 166, 207)
        elif colorIndex == WStandardColorSelector.COLOR_GREEN:
            return QColor(126, 165, 62)
        elif colorIndex == WStandardColorSelector.COLOR_YELLOW:
            return QColor(198, 185, 61)
        elif colorIndex == WStandardColorSelector.COLOR_ORANGE:
            return QColor(204, 141, 62)
        elif colorIndex == WStandardColorSelector.COLOR_MAROON:
            return QColor(145, 90, 62)
        elif colorIndex == WStandardColorSelector.COLOR_RED:
            return QColor(191, 51, 53)
        elif colorIndex == WStandardColorSelector.COLOR_PURPLE:
            return QColor(156, 93, 172)
        elif colorIndex == WStandardColorSelector.COLOR_GRAY:
            return QColor(101, 103, 101)
        return None

    @staticmethod
    def getColorName(colorIndex):
        """Return QColor for given color index"""
        if colorIndex == WStandardColorSelector.COLOR_BLUE:
            return i18n('Blue')
        elif colorIndex == WStandardColorSelector.COLOR_GREEN:
            return i18n('Green')
        elif colorIndex == WStandardColorSelector.COLOR_YELLOW:
            return i18n('Yellow')
        elif colorIndex == WStandardColorSelector.COLOR_ORANGE:
            return i18n('Orange')
        elif colorIndex == WStandardColorSelector.COLOR_MAROON:
            return i18n('Maroon')
        elif colorIndex == WStandardColorSelector.COLOR_RED:
            return i18n('Red')
        elif colorIndex == WStandardColorSelector.COLOR_PURPLE:
            return i18n('Purple')
        elif colorIndex == WStandardColorSelector.COLOR_GRAY:
            return i18n('Gray')
        return i18n('None')

    @staticmethod
    def isValidColorIndex(colorIndex):
        """Return is given color index is valid"""
        if isinstance(colorIndex, int) and colorIndex >= 0 and colorIndex < WStandardColorSelector.NB_COLORS:
            return True
        return False

    def __init__(self, parent=None):
        super(WStandardColorSelector, self).__init__(parent)

        self.setMouseTracking(True)

        self.__colorIndex = WStandardColorSelector.COLOR_NONE
        self.__colorIndexOver = None

        self.__sizeColor = max(int(QFontMetrics(self.font()).height()*.75), 8)
        if self.__sizeColor % 2 != 0:
            # size must be even number
            self.__sizeColor += 1
        self.__margin = 6
        self.__hmargin = 3

        self.__blockSize = self.__sizeColor+2*self.__margin

        self.__sizeHint = QSize(WStandardColorSelector.NB_COLORS*self.__blockSize, self.__blockSize)

        # in cache
        self.__colorProperties = [(
                                   # QColor
                                   WStandardColorSelector.getColor(index),
                                   # Default rect area
                                   QRect(self.__margin + index*self.__blockSize, self.__margin, self.__sizeColor, self.__sizeColor),
                                   # Selected rect area
                                   QRect(self.__hmargin + index*self.__blockSize, self.__hmargin, self.__sizeColor+self.__margin, self.__sizeColor+self.__margin)
                                   )
                                  for index in range(WStandardColorSelector.COLOR_GRAY+1)
                                  ]

    def sizeHint(self):
        """Return ideal size for widget"""
        return self.__sizeHint

    def mousePressEvent(self, event):
        """A mouse button is clicked on widget"""
        if Qt.LeftButton and event.buttons() == Qt.LeftButton:
            position = event.localPos().toPoint()
            clickIndex = int(position.x()/self.__blockSize)

            if clickIndex >= 0 and clickIndex < WStandardColorSelector.NB_COLORS:
                if QRegion(self.__colorProperties[clickIndex][1]).contains(position):
                    if clickIndex != self.__colorIndex:
                        self.__colorIndex = clickIndex
                        self.update()
                        self.colorUpdated.emit(self.__colorIndex)
                        return

    def mouseMoveEvent(self, event):
        """A mouse move occured on widget"""
        position = event.localPos().toPoint()
        overIndex = int(position.x()/self.__blockSize)

        if overIndex >= 0 and overIndex < WStandardColorSelector.NB_COLORS:

            if QRegion(self.__colorProperties[overIndex][1]).contains(position):
                if overIndex != self.__colorIndexOver:
                    self.setCursor(Qt.PointingHandCursor)
                    self.__colorIndexOver = overIndex
                    self.update()
                    return
                return

        self.__colorIndexOver = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def leaveEvent(self, event):
        """Mouse leav widget, ensure color are painter normally"""
        if self.__colorIndexOver is not None:
            self.__colorIndexOver = None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def paintEvent(self, event):
        super(WStandardColorSelector, self).paintEvent(event)

        painter = QPainter(self)

        position = 0
        incPosition = self.__sizeColor+2*self.__margin

        pen = QPen(QApplication.palette().color(QPalette.Window))
        pen.setWidth(1)
        pen.setCapStyle(Qt.FlatCap)

        pen2 = QPen(QApplication.palette().color(QPalette.WindowText))
        pen2.setWidth(2)
        pen2.setCapStyle(Qt.FlatCap)

        for index, colorProperties in enumerate(self.__colorProperties):
            if index == self.__colorIndexOver and not colorProperties[0] is None:
                # over color: lighter
                color = colorProperties[0].lighter(125)
            else:
                color = colorProperties[0]

            if index == WStandardColorSelector.COLOR_NONE:
                # current selected color = None
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(pen2)
                painter.drawLine(colorProperties[1].topLeft()+QPoint(1, 1), colorProperties[1].bottomRight()+QPoint(0, -1))
                painter.drawLine(colorProperties[1].bottomLeft()+QPoint(1, -1), colorProperties[1].topRight()+QPoint(0, 1))
                painter.setRenderHint(QPainter.Antialiasing, False)
                if index == self.__colorIndex:
                    pen2.setWidth(1)
                    painter.setPen(pen2)
                    painter.drawRect(QRect(colorProperties[2].topLeft(), colorProperties[2].bottomRight()-QPoint(1, 1)))
            elif index == self.__colorIndex:
                painter.setPen(Qt.NoPen)
                painter.fillRect(colorProperties[2], QBrush(color))
                painter.setPen(pen)
                painter.drawRect(QRect(colorProperties[1].topLeft(), colorProperties[1].bottomRight()-QPoint(1, 1)))
                painter.setPen(Qt.NoPen)
            else:
                painter.fillRect(colorProperties[1], QBrush(color))

            position += incPosition

    def colorIndex(self):
        """Return current selected color index"""
        return self.__colorIndex

    def color(self):
        """Return current QColor"""
        return WStandardColorSelector.getColor(self.__colorIndex)

    def setColorIndex(self, colorIndex):
        """Set current button color"""
        if colorIndex is None:
            self.__colorIndex = colorIndex
            self.update()
        elif colorIndex >= WStandardColorSelector.COLOR_NONE and colorIndex <= WStandardColorSelector.COLOR_GRAY:
            self.__colorIndex = colorIndex
            self.update()
            self.colorChanged.emit(self.__colorIndex)


class WMenuStandardColorSelector(QWidgetAction):
    """Encapsulate a WStandardColorSelector as a menu item"""
    def __init__(self, parent=None):
        super(WMenuStandardColorSelector, self).__init__(parent)

        self.__stdColorSelector = WStandardColorSelector()

        self.setDefaultWidget(self.__stdColorSelector)

    def colorSelector(self):
        return self.__stdColorSelector
