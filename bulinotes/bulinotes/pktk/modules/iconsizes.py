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
from PyQt5.Qt import *



class IconSizes(object):
    def __init__(self, values, currentIndex=0):
        if not (isinstance(values, list) or isinstance(values, tuple)):
            raise EInvalidType('Given `values` must be a <list>')
        self.__values=[value for value in values if isinstance(value, int)]

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
            self.__index+=1
            return True
        return False

    def prev(self):
        """Go to previous value

        return True if current index has been modified, otherwise false
        """
        if self.__index > 0:
            self.__index-=1
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
            v=self.__values[self.__index]
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
            self.__index=0
            for v in self.__values:
                if v < value:
                    self.__index+=1
                else:
                    break
        if currentIndex == self.__index:
            return False
        return True
