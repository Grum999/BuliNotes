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


# -----------------------------------------------------------------------------
from math import ceil

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QPushButton,
    )

from pktk.modules.utils import checkerBoardBrush
from .wmenuitem import WMenuColorPicker


class QEColor(QColor):
    def __init__(self, value=None):
        super(QEColor, self).__init__(value)

        self.__isNone=False

    def isNone(self):
        return self.__isNone

    def setNone(self, value):
        if isinstance(value, bool):
            self.__isNone=value


class WColorButton(QToolButton):
    """A button to choose color"""
    colorChanged = Signal(QEColor)

    def __init__(self, label, parent=None):
        super(WColorButton, self).__init__(parent)

        def newSetText(value):
            # don't let external code trying to set button text: there's no text :)
            pass

        self.__color = Qt.white
        self.__brush = QBrush(self.__color, Qt.SolidPattern)
        self.__cbBrush = checkerBoardBrush(16)
        self.__pen = QPen(QColor("#88888888"))
        self.__pen.setWidth(1)

        self.__noneColor = False

        self.__actionNoColor=QAction(i18n('No color'), self)
        self.__actionNoColor.triggered.connect(self.__setColorNone)
        self.__actionFromColorPicker=WMenuColorPicker()
        self.__actionFromColorPicker.colorPicker().colorUpdated.connect(self.__setColor)
        self.__menu=QMenu(self)
        self.__menu.addAction(self.__actionNoColor)
        self.__menu.addAction(self.__actionFromColorPicker)

        self.setText("")
        self.setText=newSetText

    def __setColorNone(self):
        """Set current color to None"""
        self.__color=QEColor()
        self.__color.setNone(True)
        self.colorChanged.emit(self.__color)

    def __setColor(self, color):
        """Display color palette dialog box"""
        self.setColor(color)
        self.colorChanged.emit(self.__color)

    def paintEvent(self, event):
        super(WColorButton, self).paintEvent(event)

        margin = ceil(self.height()/2)//2
        margin2 = margin<<1
        if not self.icon().isNull():
            rect=QRect(margin, self.height() - margin//2 - 4, self.width() - margin2, margin//2)
        else:
            rect=QRect(margin, margin, self.width() - margin2,  self.height() - margin2)

        painter = QPainter(self)
        painter.setPen(self.__pen)
        if not self.__color.isNone():
            painter.fillRect(rect, self.__cbBrush)
            painter.setBrush(self.__brush)
        painter.drawRect(rect)

    def mouseReleaseEvent(self, event):
        self.__showColorPalette()
        super(WColorButton, self).mouseReleaseEvent(event)

    def color(self):
        """Return current button color"""
        return self.__color

    def setColor(self, color):
        """Set current button color"""
        self.__color = QEColor(color)
        self.__brush.setColor(self.__color)
        self.__actionFromColorPicker.colorPicker().setColor(self.__color)
        self.update()

    def noneColor(self):
        """Return if no color value is managed or not"""
        return self.__noneColor

    def setNoneColor(self, value):
        """Set if no color is managed or not

        If true, button is delayed popup with a menu:
        - "no color"
        - From palette
        """
        if isinstance(value, bool):
            self.__noneColor=value
            if value:
                self.setPopupMode(QToolButton.InstantPopup)
                self.setArrowType(Qt.NoArrow)
                self.setMenu(self.__menu)
                self.setStyleSheet("""WColorButton::menu-indicator { width: 0; } """ )
            else:
                self.setPopupMode(QToolButton.DelayedPopup)
                self.setMenu(None)

    def colorPicker(self):
        """Return color picker instance, allowing to define options for it"""
        return self.__actionFromColorPicker.colorPicker()
