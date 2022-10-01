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
# The iconsize module provides classes used to manage icons size in QListView
#
# Main class from this module
#
# - IconSizes:
#       Provides basics methods to manage sizes in a given set of possible sizes
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *

from ..pktk import *


class IconSizes(object):
    def __init__(self, values, currentIndex=0):
        if not (isinstance(values, list) or isinstance(values, tuple)):
            raise EInvalidType('Given `values` must be a <list>')
        self.__values = [value for value in values if isinstance(value, int)]

        if len(self.__values) == 0:
            raise EInvalidValue('Given `values` must be a non empty list of <int>')

        self.__index = 0

        self.setIndex(currentIndex)

    def __repr__(self):
        return f"<IconSizes({self.__index}, {self.__values[self.__index]})>"

    def next(self):
        """Go to next value

        return True if current index has been modified, otherwise false
        """
        if self.__index < len(self.__values) - 1:
            self.__index += 1
            return True
        return False

    def prev(self):
        """Go to previous value

        return True if current index has been modified, otherwise false
        """
        if self.__index > 0:
            self.__index -= 1
            return True
        return False

    def index(self):
        """Return current index"""
        return self.__index

    def setIndex(self, index):
        """Set current index

        return True if current index has been modified, otherwise false
        """
        if index == self.__index:
            return False
        if not isinstance(index, int):
            raise EInvalidType('Given `values` must be a <int>')

        if index < 0:
            self.__index = 0
        elif index > len(self.__values) - 1:
            self.__index = len(self.__values) - 1
        else:
            self.__index = index

        return True

    def value(self, asQSize=False):
        """Return current value"""
        if asQSize:
            v = self.__values[self.__index]
            return QSize(v, v)
        return self.__values[self.__index]

    def setValue(self, value):
        """Set current value

        If value doesn't exist in list of values, return the first value less than current

        return True if current index has been modified, otherwise false
        """
        currentIndex = self.__index
        if value in self.__values:
            self.__index = self.__values.index(value)
        else:
            self.__index = 0
            for v in self.__values:
                if v < value:
                    self.__index += 1
                else:
                    break
        if currentIndex == self.__index:
            return False
        return True
