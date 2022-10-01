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
# The wlabelelide module provides a label widget able to manage elide '...' if
# label content is too large to fit in allowed label width
#
# Main class from this module
#
# - WLabelElide:
#       Widget
#       The main label widget
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )


class WLabelElide(QLabel):
    """A label that manage elide"""

    def __init__(self, elide=Qt.ElideNone, *parameters):
        super(WLabelElide, self).__init__(*parameters)

        self.__elide = Qt.ElideNone
        self.__elipsisText = '…'
        self.__elipsisWidth = 0
        self.__hElipsisWidth = 0
        self.__textWidth = 0
        self.__fontMetrics = QFontMetrics(self.font())

        self.__hashFnt = None
        self.__hashTxt = None

        self.setElide(elide)
        self.__calculateMetrics()

    def __calculateMetrics(self):
        """Calculate metrics used during paint process"""
        hashFnt = hash(self.font())
        hashTxt = hash(self.text())

        if hashFnt == self.__hashFnt and hashTxt == self.__hashTxt:
            # don't need to recalculate values
            return
        fontMetrics = QFontMetrics(self.font())
        self.__textWidth = fontMetrics.horizontalAdvance(self.text())

        self.__elipsisWidth = fontMetrics.horizontalAdvance(self.__elipsisText)
        self.__hElipsisWidth = self.__elipsisWidth*0.8

        self.__hashFnt = hash(self.font())
        self.__hashTxt = hash(self.text())

    def elide(self):
        """Return current elide mode"""
        return self.__elide

    def setElide(self, value):
        """Return current elide mode"""
        if self.__elide != value and value in (Qt.ElideLeft, Qt.ElideRight, Qt.ElideMiddle, Qt.ElideNone):
            self.__elide = value
            self.update()

    def elipsis(self):
        """Return current elispis text"""
        return self.__elipsisText

    def setElipsis(self, value):
        """Set elipsis text"""
        if self.__elipsisText != value and isinstance(value, str):
            self.__elipsisText = value
            self.update()

    def paintEvent(self, event):
        """paint label taking in account elide mode"""
        if self.__elide == Qt.ElideNone:
            # no elide, use default label paint
            super(WLabelElide, self).paintEvent(event)
            return

        rect = event.rect()
        self.__calculateMetrics()

        if self.__textWidth <= rect.width():
            # no elide (text fit in current rect), use default label paint
            super(WLabelElide, self).paintEvent(event)
            return

        styleOptions = QStyleOption()
        styleOptions.initFrom(self)

        painter = QPainter(self)
        painter.setFont(self.font())

        if self.__elide == Qt.ElideRight:
            dRect = QRect(rect.left(), rect.top(), rect.width() - self.__elipsisWidth, rect.height())
            painter.drawText(dRect, Qt.AlignLeft, self.text())

            dRect = QRect(rect.left() + dRect.width(), rect.top(), self.__elipsisWidth, rect.height())
            painter.drawText(dRect, Qt.AlignLeft, self.__elipsisText)

            dRect = QRect(dRect.left() - self.__hElipsisWidth, rect.top(), self.__hElipsisWidth+2, rect.height())
            gradient = QLinearGradient(dRect.topLeft(), dRect.topRight())
            gradient.setColorAt(0, QColor(Qt.transparent))
            gradient.setColorAt(1, styleOptions.palette.color(QPalette.Window))
            painter.fillRect(dRect, gradient)
        elif self.__elide == Qt.ElideLeft:
            dRect = QRect(rect.left() + self.__elipsisWidth, rect.top(), rect.width() - self.__elipsisWidth, rect.height())
            painter.drawText(dRect, Qt.AlignRight, self.text())

            dRect = QRect(rect.left(), rect.top(), self.__elipsisWidth, rect.height())
            painter.drawText(dRect, Qt.AlignLeft, self.__elipsisText)

            dRect = QRect(dRect.right(), rect.top(), self.__hElipsisWidth, rect.height())
            gradient = QLinearGradient(dRect.topLeft(), dRect.topRight())
            gradient.setColorAt(0, styleOptions.palette.color(QPalette.Window))
            gradient.setColorAt(1, QColor(Qt.transparent))
            painter.fillRect(dRect, gradient)
        elif self.__elide == Qt.ElideMiddle:
            hWidth = (rect.width()-self.__elipsisWidth)//2
            dRect = QRect(rect.left(), rect.top(), hWidth, rect.height())
            painter.drawText(dRect, Qt.AlignLeft, self.text())

            dRect = QRect(dRect.right() - self.__hElipsisWidth, rect.top(), self.__hElipsisWidth+2, rect.height())
            gradient = QLinearGradient(dRect.topLeft(), dRect.topRight())
            gradient.setColorAt(0, QColor(Qt.transparent))
            gradient.setColorAt(1, styleOptions.palette.color(QPalette.Window))
            painter.fillRect(dRect, gradient)

            dRect = QRect(rect.left() + hWidth + self.__elipsisWidth, rect.top(), hWidth, rect.height())
            painter.drawText(dRect, Qt.AlignRight, self.text())

            dRect = QRect(dRect.left(), rect.top(), self.__hElipsisWidth, rect.height())
            gradient = QLinearGradient(dRect.topLeft(), dRect.topRight())
            gradient.setColorAt(0, styleOptions.palette.color(QPalette.Window))
            gradient.setColorAt(1, QColor(Qt.transparent))
            painter.fillRect(dRect, gradient)

            dRect = QRect(rect.left() + hWidth, rect.top(), self.__elipsisWidth, rect.height())
            painter.drawText(dRect, Qt.AlignLeft, self.__elipsisText)
