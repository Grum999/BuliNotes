# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# Based from C++ Qt example:
#   https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/layouts/flowlayout/flowlayout.cpp?h=5.15
#
#   Original example source code published under BSD License Usage
#       Copyright (C) 2016 The Qt Company Ltd.
#       Contact: https://www.qt.io/licensing/
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The wflowlayout module provides a 'flow' layout model (usually, used to
# manage tags list)
#
# Main class from this module
#
# - WFlowLayout:
#       Layout
#       The flow layout
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )


class WFlowLayout(QLayout):
    """A flow layout to manage inline widgets

    Qt documentation with detailed explanations about flow layout implementation:
        https://doc.qt.io/qt-5/qtwidgets-layouts-flowlayout-example.html
    """

    def __init__(self, parent=None):
        super(WFlowLayout, self).__init__(parent)

        # space between items
        self.__horizontalSpacing = -1
        self.__verticalSpacing = -1

        # list of items
        self.__itemList = []

        #
        self.__minHeightCalculated = 0

    def __del__(self):
        """destructor: cleanup items"""
        while item := self.takeAt(0):
            del item

    def __calculateLayout(self, rect, testOnly):
        """Handles the layout if horizontalSpacing() or verticalSpacing() don't return the default value.

        It uses contentsMargins() to calculate the area available to the layout items
        """
        cMargins = self.contentsMargins()
        left = cMargins.left()
        top = cMargins.top()
        right = cMargins.right()
        bottom = cMargins.bottom()

        effectiveRect = rect.adjusted(left, top, -right, -bottom)
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0

        self.__minHeightCalculated = 0

        for item in self.__itemList:
            maxSize = item.maximumSize()
            hintSize = item.sizeHint()
            expandingH = (item.expandingDirections() & Qt.Horizontal) == Qt.Horizontal

            widget = item.widget()

            spaceX = self.horizontalSpacing()
            if spaceX == -1:
                if widget:
                    spaceX = widget.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
                else:
                    # a layout..?
                    spaceX = 0

            spaceY = self.verticalSpacing()
            if spaceY == -1:
                if widget:
                    spaceY = widget.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
                else:
                    # a layout..?
                    spaceY = 0

            itemWidth = hintSize.width()
            itemMaxWidth = min(maxSize.width(), effectiveRect.width()) - x

            nextX = x + itemWidth + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                # not enough space on current line to display widget
                # go to next line
                x = effectiveRect.x()
                y = y + lineHeight + spaceY

                if expandingH:
                    nextX = x + itemMaxWidth + spaceX
                    itemMaxWidth = min(maxSize.width(), effectiveRect.width()) - x
                else:
                    nextX = x + itemWidth + spaceX
                lineHeight = 0

            if not testOnly:
                if expandingH:
                    item.setGeometry(QRect(QPoint(x, y), QSize(itemMaxWidth, hintSize.height())))
                else:
                    item.setGeometry(QRect(QPoint(x, y), hintSize))

            x = nextX
            lineHeight = max(lineHeight, hintSize.height())

        self.__minHeightCalculated = y + lineHeight - bottom

        return y + lineHeight - rect.y() + bottom

    def __smartSpacing(self, pm):
        """Get the default spacing for either the top-level layouts or the sublayouts.

        The default spacing for top-level layouts, when the parent is a QWidget, will be determined by querying the style.
        The default spacing for sublayouts, when the parent is a QLayout, will be determined by querying the spacing of the parent layout.
        """
        parent = self.parent()
        if parent is None:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()

    def horizontalSpacing(self):
        """Horizontal space between items"""
        if self.__horizontalSpacing >= 0:
            return self.__horizontalSpacing
        else:
            return self.__smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

    def setHorizontalSpacing(self, value):
        """Set horizontal space between items"""
        if (value is None or isinstance(value, int)) and self.__horizontalSpacing != value:
            self.__horizontalSpacing = value
            self.update()

    def verticalSpacing(self):
        """Vertical space between items"""
        if self.__verticalSpacing >= 0:
            return self.__verticalSpacing
        else:
            return self.__smartSpacing(QStyle.PM_LayoutVerticalSpacing)

    def setVerticalSpacing(self, value):
        """Set vertical space between items"""
        if (value is None or isinstance(value, int)) and self.__verticalSpacing != value:
            self.__verticalSpacing = value
            self.update()

    def count(self):
        """Return number of items in layout"""
        return len(self.__itemList)

    def expandingDirections(self):
        """returns the Qt::Orientations in which the layout can make use of more space than its sizeHint()"""
        return Qt.Vertical | Qt.Horizontal

    def sizeHint(self):
        """Return ideal size for widget"""
        return self.minimumSize()

    def itemAt(self, index):
        """Return item given by `index` in layout"""
        if index >= 0 and index < len(self.__itemList):
            returned = self.__itemList[index]
            return returned
        return None

    def takeAt(self, index):
        """Remove item given by `index` from layout and return item"""
        if index >= 0 and index < len(self.__itemList):
            returned = self.__itemList.pop(index)
            return returned
        return None

    def replaceAt(self, index, item):
        """ ** """
        pass

    def addItem(self, item):
        """Append an item to layout"""
        self.insertItem(-1, item)

    def insertItem(self, index, item):
        """Inserts `item` into this box layout at position `index`.

        If `index` is negative, the item is added at the end
        """
        if not isinstance(item, QLayoutItem):
            raise EInvalidType("Given `layout` must be a <QLayoutItem>")
        elif not isinstance(index, int):
            raise EInvalidType("Given `index` must be a <int>")

        if index < 0:
            # append
            self.__itemList.append(item)
        else:
            self.__itemList.insert(index, item)
        self.invalidate()

    def insertLayout(self, index, layout):
        """Inserts `layout` into this box layout at position `index`.

        If `index` is negative, the item is added at the end
        """
        if not isinstance(layout, QLayout):
            raise EInvalidType("Given `layout` must be a <QLayout>")
        elif not isinstance(index, int):
            raise EInvalidType("Given `index` must be a <int>")
        elif hash(layout) == hash(self):
            raise EInvalidType("Given `layout` can't be added to itself")

        self.insertItem(index, layout)

    def insertWidget(self, index, widget):
        """Inserts `widget` into this box layout at position `index`.

        If `index` is negative, the item is added at the end
        """
        if not isinstance(widget, QWidget):
            raise EInvalidType("Given `widget` must be a <QWidget>")
        elif not isinstance(index, int):
            raise EInvalidType("Given `index` must be a <int>")

        self.addChildWidget(widget)
        wi = QWidgetItem(widget)
        self.insertItem(index, wi)

    def addLayout(self, layout):
        """Append an item to layout"""
        self.insertLayout(-1, layout)

    def minimumSize(self):
        """Return minimal size required for layout"""
        size = QSize(0, self.__minHeightCalculated)
        for item in self.__itemList:
            size = size.expandedTo(item.minimumSize())

        cMargins = self.contentsMargins()

        size += QSize(cMargins.left()+cMargins.right(), cMargins.top()+cMargins.bottom())
        return size

    def hasHeightForWidth(self):
        """indicate heightForWidth is implemented"""
        return True

    def heightForWidth(self, width):
        """To adjust to widgets of which height is dependent on width, we implement"""
        return self.__calculateLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        """used to do the actual layout, i.e., calculate the geometry of the layout's items"""
        super(WFlowLayout, self).setGeometry(rect)
        self.__calculateLayout(rect, False)
