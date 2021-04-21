#-----------------------------------------------------------------------------
# Buli Commander
# Copyright (C) 2020 - Grum999
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
# A Krita plugin designed to manage documents
# -----------------------------------------------------------------------------

class EList(object):
    """A EList is a list on which we can use next() and prev() method to get values

    When initialised, current values point on nothing (return None) and next() should be call first
    """

    def __init__(self, value):
        if not isinstance(value, list):
            raise Exception("Given `value` must be a list")

        self.__list = value
        self.__index = -1

    def value(self, index=None):
        """Return current value

        If `index` is provided, return value for given index.
        If given index is outside bounds, return 'None'
        """
        if not index is None:
            if index >= 0 and index < len(self.__list):
                return self.__list[self.__index]
            return None
        elif self.__index >= 0 and self.__index < len(self.__list):
            return self.__list[self.__index]
        else:
            return None

    def next(self, move=True):
        """Move to next item and return value

        If `move` is False, return next value without moving

        If there's no more item, do not move and return None
        """
        if move:
            if self.__index < len(self.__list):
                self.__index+=1
                return self.value()

            return None
        else:
            return self.value(self.__index + 1)

    def prev(self, move=True):
        """Move to previous item and return value

        If `move` is False, return previous value without moving

        If there's no previous item, do not move and return None
        """
        if move:
            if self.__index > 0:
                self.__index-=1
                return self.value()

            return None
        else:
            return self.value(self.__index - 1)

    def first(self, move=True):
        """Move to first item and return value

        If `move` is False, return first value without moving
        """
        if move:
            self.__index = 0
            return self.value()
        else:
            if len(self.__list) > 0:
                return self.__list[0]
            return None

    def last(self, move=True):
        """Move to last item and return value

        If `move` is False, return last value without moving
        """
        if move:
            self.__index = len(self.__list) - 1
            return self.value()
        else:
            if len(self.__list) > 0:
                return self.__list[len(self.__list) - 1]
            return None

    def index(self):
        """Return current index"""
        return self.__index

    def setIndex(self, value):
        """Set current index

        if value is outside bounds, force to bound value
        """
        if not isinstance(value, int):
            raise Exception("Given `index` must be an <int>")

        if value < 0:
            self.__index = 0
        elif value >= len(self.__list):
            self.__index = len(self.__list) - 1
        else:
            self.__index = value

        return self.value()

    def list(self):
        """Return list"""
        return self.__list

    def length(self):
        """Return list length"""
        return len(self.__list)

    def resetIndex(self):
        """Reset index to none"""
        self.__index=-1
