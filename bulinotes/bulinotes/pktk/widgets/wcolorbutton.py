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
# The wcolorbutton module provides a color button choser
#
# Main class from this module
#
# - WColorButton:
#       Widget
#       The color button
#
# - QEColor
#       Extend the QColor to support the None value
#       (no color defined != transparent color)
#
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

from ..modules.imgutils import checkerBoardBrush
from .wmenuitem import WMenuColorPicker


class QEColor(QColor):
    def __init__(self, value=None):
        super(QEColor, self).__init__(value)

        self.__isNone = (value is None)

    def __deepcopy__(self, memo):
        """Used by pickle from copy.deepcopy()"""
        returned = QEColor()
        returned.setNamedColor(self.name())
        returned.setNone(self.__isNone)
        return returned

    def isNone(self):
        return self.__isNone

    def setNone(self, value):
        if isinstance(value, bool):
            self.__isNone = value


class WColorButton(QToolButton):
    """A button to choose color"""
    colorChanged = Signal(QEColor)

    def __init__(self, label=None, parent=None):
        super(WColorButton, self).__init__(parent)

        def newSetText(value):
            # don't let external code trying to set button text: there's no text :)
            pass

        self.__color = QEColor(Qt.white)
        self.__brush = QBrush(self.__color, Qt.SolidPattern)
        self.__cbBrush = checkerBoardBrush(16)
        self.__pen = QPen(QColor("#88888888"))
        self.__pen.setWidth(1)

        self.__noneColor = False
        self.__havePopupMenu = True

        self.__actionNoColor = QAction(i18n('No color'), self)
        self.__actionNoColor.triggered.connect(self.__setColorNone)
        self.__actionFromColorPicker = WMenuColorPicker()
        self.__actionFromColorPicker.colorPicker().colorUpdated.connect(self.__setColor)
        self.__menu = QMenu(self)
        self.__menu.addAction(self.__actionNoColor)
        self.__menu.addAction(self.__actionFromColorPicker)

        self.setText("")
        self.setText = newSetText
        self.setNoneColor(False)
        self.__setPopupMenu()

    def __setPopupMenu(self):
        """Define popup menu according to options"""
        self.__actionNoColor.setVisible(self.__noneColor)

        if self.__havePopupMenu:
            self.setPopupMode(QToolButton.InstantPopup)
            self.setArrowType(Qt.NoArrow)
            self.setMenu(self.__menu)
            self.setStyleSheet("""WColorButton::menu-indicator { width: 0; } """)
        else:
            self.setPopupMode(QToolButton.DelayedPopup)
            self.setMenu(None)

    def __setColorNone(self):
        """Set current color to None"""
        self.__color = QEColor()
        self.__color.setNone(True)
        self.colorChanged.emit(self.__color)

    def __setColor(self, color):
        """Display color palette dialog box"""
        self.setColor(color)
        self.colorChanged.emit(self.__color)

    def paintEvent(self, event):
        super(WColorButton, self).paintEvent(event)

        margin = ceil(self.height()/2)//2
        margin2 = margin << 1
        if not self.icon().isNull():
            rect = QRect(margin, self.height() - margin//2 - 4, self.width() - margin2, margin//2)
        else:
            rect = QRect(margin, margin, self.width() - margin2,  self.height() - margin2)

        painter = QPainter(self)
        painter.setPen(self.__pen)
        if not self.__color.isNone():
            painter.fillRect(rect, self.__cbBrush)
            painter.setBrush(self.__brush)
        painter.drawRect(rect)

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
            self.__noneColor = value
            self.__setPopupMenu()

    def popupMenu(self):
        """Return if button have popup menu (ie: manage colors through menu)"""
        return self.__havePopupMenu

    def setPopupMenu(self, value):
        """Set if button have popup menu

        If true, button is delayed popup with a menu
        Otherwise color selection method have to be implemented
        """
        if isinstance(value, bool):
            self.__havePopupMenu = value
            self.__setPopupMenu()

    def colorPicker(self):
        """Return color picker instance, allowing to define options for it"""
        return self.__actionFromColorPicker.colorPicker()
