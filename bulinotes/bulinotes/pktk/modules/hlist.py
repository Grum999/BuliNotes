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
# The hlist module provides access to a list that manage a maximum number of
# items, and avoid duplicate entry (initialy built to manage history)
#
# Main class from this module
#
# - HList:
#       A class with high level methods for history list management
#
# -----------------------------------------------------------------------------

import os
import sys

from PyQt5.QtCore import (
        pyqtSignal as Signal,
        QObject
    )


from ..pktk import *


class HList(QObject):
    """A HList is a list on which a maximum number of items is defined

    When a new item is append to list, if maximum number is reached, the first
    item of list is removed

    If an item already exists in history, he's moved from the current position to
    the last position
    """
    changed = Signal()

    def __init__(self, items=[], maxItems=25, uniqueItems=True):
        super(HList, self).__init__(None)
        self.__list = []
        self.__maxItems = 0
        self.__uniqueItems = True
        self.setMaxItems(maxItems)
        self.setItems(items)
        self.__setUniqueItems(uniqueItems)

    def __setUniqueItems(self, value):
        """Define if items are unique or not in list

        Property is defined when HList is created
        """
        if not isinstance(value, bool):
            raise EInvalidType('Given `value` must be an <bool>')
        self.__uniqueItems = value

    def setMaxItems(self, value):
        """Define maximum items that can be stored by history

        If provided number is lower than current number of items, list is truncated
        """
        if not isinstance(value, int):
            raise EInvalidType('Given `value` must be an <int>')
        if value < 0:
            # negative value = no maximum items in history
            value = -1
        if self.__maxItems != value:
            self.__maxItems = value
            if len(self.__list) > self.__maxItems:
                self.__list = self.__list[-self.__maxItems:]
                self.changed.emit()

    def maxItems(self):
        """Return current maximum items in a list"""
        return self.__maxItems

    def setItems(self, items):
        """Set history content"""
        if not isinstance(items, list):
            raise EInvalidType('Given `items` must be a <list>')

        self.__list.clear()
        for item in items:
            self.append(item, False)
        self.changed.emit()

    def append(self, value, notifyChange=True):
        """Add a value to history"""
        position = None
        if self.__uniqueItems:
            try:
                position = self.__list.index(value)
            except Exception:
                # value not found
                position = None
        if position is not None:
            self.__list.pop(position)
        if len(self.__list) >= self.__maxItems:
            if self.__maxItems > 1:
                self.__list = self.__list[-self.__maxItems+1:]
            else:
                self.__list = []
        self.__list.append(value)
        if notifyChange:
            self.changed.emit()

    def remove(self, value, notifyChange=True):
        """remove a value from history"""
        position = None
        try:
            position = self.__list.index(value)
        except Exception:
            # value not found
            position = None

        if position is not None:
            self.__list.pop(position)

        if notifyChange:
            self.changed.emit()

    def pop(self, notifyChange=True):
        """Pop last value added"""
        returned = None
        if len(self.__list) > 0:
            returned = self.__list.pop()
            if notifyChange:
                self.changed.emit()
        return returned

    def last(self):
        """Return last value added"""
        if len(self.__list) > 0:
            return self.__list[-1]
        else:
            return None

    def clear(self, notifyChange=True):
        """Clear history"""
        self.__list.clear()
        if notifyChange:
            self.changed.emit()

    def length(self):
        """return number of items in History"""
        return len(self.__list)

    def list(self):
        """return items in History"""
        return self.__list
