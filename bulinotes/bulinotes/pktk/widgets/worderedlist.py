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
# The worderedlist module provides a widget to easily manage ordering rules
# implementation
#
# Main class from this module
#
# - WOrderedList:
#       Widget
#       A list widget allowing to reorder items + defined ascending/descending
#       sort order
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from ..modules.imgutils import buildIcon
from ..pktk import *


class OrderedItem(QListWidgetItem):
    """An item to order in a list WOrderedList"""
    ROLE_VALUE =         Qt.UserRole + 0x01
    ROLE_SORTASCENDING = Qt.UserRole + 0x02

    def __init__(self, label, value, checked=False, ascending=True):
        super(OrderedItem, self).__init__(label, None, QListWidgetItem.UserType)
        self.setData(OrderedItem.ROLE_VALUE, value)
        self.setData(OrderedItem.ROLE_SORTASCENDING, ascending)
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)

        self.__checkable = True
        self.setCheckState(checked)

    def isSortAscending(self):
        """Return if current sort is ascending"""
        return self.data(OrderedItem.ROLE_SORTASCENDING)

    def isSortDescending(self):
        """Return if current sort is descending"""
        return not self.data(OrderedItem.ROLE_SORTASCENDING)

    def setSortAscending(self, ascending):
        """Set if current sort is descending"""
        if isinstance(ascending, bool) and (not self.__checkable or self.checked()):
            self.setData(OrderedItem.ROLE_SORTASCENDING, ascending)

    def setCheckable(self, checkable):
        """Set if current sort is descending"""
        if isinstance(checkable, bool):
            self.__checkable = checkable
            if checkable:
                self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
                self.setCheckState(self.__checked)
            else:
                self.__checked = self.checkState() == Qt.Checked
                self.setFlags(self.flags() & ~Qt.ItemIsUserCheckable)
                self.setData(Qt.CheckStateRole, None)

    def checked(self):
        """Return if item is checked"""
        return self.__checkable and (self.checkState() == Qt.Checked)

    def setCheckState(self, value):
        """Set item is checked"""
        if isinstance(value, bool):
            if value:
                QListWidgetItem.setCheckState(self, Qt.Checked)
            else:
                QListWidgetItem.setCheckState(self, Qt.Unchecked)

    def value(self):
        """Return current value"""
        return self.data(OrderedItem.ROLE_VALUE)


class StyledOrderedItemDelegate(QStyledItemDelegate):
    """Draw an OrderedItem, especially the arrow to indicate sort direction"""

    def __init__(self, orderedListWidget, parent=None):
        super(StyledOrderedItemDelegate, self).__init__(parent)
        if not isinstance(orderedListWidget, WOrderedList):
            raise EInvalidType("Given `orderedListWidget` must be <WOrderedList>")
        self.__orderedListWidget = orderedListWidget

        # preload icons for performances (even if don't really need for small lists...)
        self.__iconUpEmpty = buildIcon("pktk:arrow_big_empty_up")
        self.__iconUpFilled = buildIcon("pktk:arrow_big_filled_up")
        self.__iconDownEmpty = buildIcon("pktk:arrow_big_empty_down")
        self.__iconDownFilled = buildIcon("pktk:arrow_big_filled_down")

    def paint(self, painter, option, index):
        """Paint item"""
        if option.state & QStyle.State_HasFocus == QStyle.State_HasFocus:
            # remove focus style if active
            option.state = option.state & ~QStyle.State_HasFocus

        # if not index.data(Qt.CheckStateRole):
        #    # when unchecked, text is drawn as disabled state as value is
        #    # not selected
        #    option.state = option.state & ~QStyle.State_Enabled

        # use default constructor to paint item
        super(StyledOrderedItemDelegate, self).paint(painter, option, index)

        # if self.__orderedListWidget.checkOptionAvailable() and not index.data(Qt.CheckStateRole) or not self.__orderedListWidget.sortOptionAvailable():
        if not self.__orderedListWidget.sortOptionAvailable():
            # if check option is available and not checked
            # or not sort option available
            # => do not display sort direction
            return

        self.initStyleOption(option, index)

        # drawing area for arrow
        rect = QRect(option.rect.right() - option.rect.height(), option.rect.top(), option.rect.height(), option.rect.height())
        painter.save()

        # paint background color
        if option.state & QStyle.State_Active:
            colorGroup = QPalette.Active
        else:
            colorGroup = QPalette.Inactive

        if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
            painter.fillRect(rect, option.palette.color(colorGroup, QPalette.Highlight))
        else:
            painter.fillRect(rect, option.palette.color(colorGroup, QPalette.Base))

        # draw arrow
        if self.__orderedListWidget.checkOptionAvailable() and not index.data(Qt.CheckStateRole):
            # empty arrow: use 'disabled' version
            if index.data(OrderedItem.ROLE_SORTASCENDING):
                painter.drawPixmap(rect, self.__iconUpEmpty.pixmap(rect.size(), QIcon.Disabled))
            else:
                painter.drawPixmap(rect, self.__iconDownEmpty.pixmap(rect.size(), QIcon.Disabled))
        else:
            # filled arrow: use 'disabled' version
            if index.data(OrderedItem.ROLE_SORTASCENDING):
                painter.drawPixmap(rect, self.__iconUpFilled.pixmap(rect.size(), QIcon.Normal))
            else:
                painter.drawPixmap(rect, self.__iconDownFilled.pixmap(rect.size(), QIcon.Normal))

        painter.restore()


class WOrderedList(QListWidget):
    """A ListWidget ready to use for:

    - Ordering items manually by drag'n'drog
    - Ordering items programmatically
    - Allows to check/uncheck/invert items (all, selection)
    - Allows to manage ascending/descending value for items

    Primarily this widget is used to manage columns/fields:
    - display a list of fields/columns
    - select fields/columns
    - reorder fields/columns
    - define sort order applied on fields/columns



    checkOptionAvailable()                  sortOptionAvailable()
        When True, checkbox is                  When True, arrow is
        available on left side                  available on right side
           ↓                                          ↓
        +-----------------------------------------------+
        | [ ] Item 01                                 ▽ |           reorderOptionAvailable()
        | [ ] Item 02                                 △ |               When True, item can be reordered
        | [X] Item 03                                 ▼ |               with drag'n'drop
        | [X] Item 04                                 ▲ |
        +-----------------------------------------------+
        When an item is unchecked, sort arrow is "empty" => mean that sort order is ignored


    """
    itemOrderChanged = Signal()

    def __init__(self, parent=None):
        super(WOrderedList, self).__init__(parent)

        self.__delegate = StyledOrderedItemDelegate(self)

        self.setItemDelegate(self.__delegate)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setUniformItemSizes(True)

        self.__optionSort = True
        self.__optionCheck = True
        self.__optionReorder = True

    def mouseReleaseEvent(self, event):
        item = self.itemAt(event.pos())

        if self.__optionSort and event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier and isinstance(item, QListWidgetItem):
            # if pressed button is not left button, ignore event to not modify order direction
            # if a modifiers is pressed, might be in a selection then ignore event to not modify order direction
            # why item is a "OrderedItem" object but isinstance() only return True for "QListWidgetItem"??

            # get current rect for item
            rect = self.visualItemRect(item)

            if event.pos().x() > rect.right() - rect.height():
                # click on right side square (width = height): invert current order direction
                item.setSortAscending(not item.isSortAscending())
                return

        super(WOrderedList, self).mouseReleaseEvent(event)

    def dropEvent(self, event):
        super(WOrderedList, self).dropEvent(event)
        if event.isAccepted():
            self.itemOrderChanged.emit()

    def sortOptionAvailable(self):
        """Return if ascending/descending sort option is available for items"""
        return self.__optionSort

    def setSortOptionAvailable(self, value):
        """Set if ascending/descending sort option is available for items"""
        if isinstance(value, bool):
            self.__optionSort = value
            model = self.model()
            # need to update each item from model; update() made on QListWidget didn't update anything
            for index in range(self.count()):
                self.update(model.index(index, 0))

    def checkOptionAvailable(self):
        """Return if check/uncheck option is available for items"""
        return self.__optionCheck

    def setCheckOptionAvailable(self, value):
        """Set if ascending/descending sort option is available for items"""
        if isinstance(value, bool):
            self.__optionCheck = value
            for index in range(self.count()):
                self.item(index).setCheckable(self.__optionCheck)

    def reorderOptionAvailable(self):
        """Return if ordering items option is available"""
        return self.__optionReorder

    def setReorderOptionAvailable(self, value):
        """Set if ordering items option is available"""
        if isinstance(value, bool):
            self.__optionReorder = value
            if self.__optionReorder:
                self.setDragDropMode(QAbstractItemView.InternalMove)
            else:
                self.setDragDropMode(QAbstractItemView.NoDragDrop)

    def addItem(self, label, value, checked=True, ascending=True):
        """Create and add new item in list

        return a <OrderedItem> object
        """
        item = OrderedItem(label, value, checked, ascending)
        QListWidget.addItem(self, item)
        return item

    def addItems(self, items):
        """Add multiple items at once

        Given `items` is a list of <OrderedItem>
        """
        for item in items:
            if isinstance(item, OrderedItem):
                QListWidget.addItem(self, item)

    def insertItem(self, row, label, value, checked=True, ascending=True):
        """Create and insert new item in list

        return a <OrderedItem> object
        """
        item = OrderedItem(label, value, checked, ascending)
        QListWidget.addItem(self, row, item)
        return item

    def insertItems(self, row, items):
        """Add multiple items at once

        Given `items` is a list of <OrderedItem>
        """
        for item in items:
            if isinstance(item, OrderedItem):
                QListWidget.insertItem(self, row, item)
                row += 1

    def items(self, checkedOnly=True):
        """Return a list of <OrderedItem> objects

        If `checkedOnly` is True, only checked items are returned, otherwise all objects are returned
        """
        returned = []
        for index in range(self.count()):
            item = self.item(index)
            if checkedOnly and item.checkState() == Qt.Checked or not checkedOnly:
                returned.append(item)
        return returned

    def setCheckState(self, value, selectedOnly=False):
        """Set checked status to `value` for items

        If `selectedOnly` is False, change check state for all items
        otherwise change check state for all selected items only
        """
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be <bool>")
        elif not self.__optionCheck:
            return

        if selectedOnly:
            for item in self.selectedItems():
                item.setCheckState(value)
        else:
            for index in range(self.count()):
                self.item(index).setCheckState(value)

    def setSortAscending(self, value, selectedOnly=False):
        """Set sort direction 'ascending' for items if `value` is True

        If `selectedOnly` is False, change check state for all items
        otherwise change check state for all selected items only
        """
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be <bool>")
        elif not self.__optionSort:
            return

        if selectedOnly:
            for item in self.selectedItems():
                item.setSortAscending(value)
        else:
            for index in range(self.count()):
                self.item(index).setSortAscending(value)
