# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# adapted from solution found on Stack Overflow
# https://stackoverflow.com/a/68227820
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The wlogslider module provides an extended version of QSlider that manage
# logarithmic values
#
# Main class from this module
#
# - WLogSlider:
#       Widget
#       The main slider widget
#
# -----------------------------------------------------------------------------

from math import log10

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QSlider
    )


class WLogSlider(QSlider):
    """A slider with logarithmic scale"""
    naturalValueChanged = Signal(float)

    def __init__(self, parent=None):
        super(WLogSlider, self).__init__(parent)

        self.__naturalMinimumValue = 0.01
        self.__naturalMaximumValue = 100.00

        self.__scale = 1000
        self.__naturalValue = 1
        self.valueChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value):
        """Value has been modified"""
        self.__naturalValue = pow(10, (value / self.__scale))
        self.naturalValueChanged.emit(self.__naturalValue)

    def setNaturalMin(self, value):
        """Set minimum value"""
        if value > 0:
            self.__naturalMinimumValue = value
            self.setMinimum(int(log10(value) * self.__scale))

    def setNaturalMax(self, value):
        """Set maximum value"""
        if value > 0:
            self.__naturalMaximumValue = value
            self.setMaximum(int(log10(value) * self.__scale))

    def setNaturalValue(self, value):
        """Set value"""
        self.__naturalValue = value
        self.setValue(int(log10(value) * self.__scale))

    def naturalValue(self, value):
        """return value"""
        return self.__naturalValue

    def scale(self):
        """Return scale"""
        return self.__scale

    def setScale(self, value):
        """Define scale for slider"""
        if isinstance(value, (int, float)) and value > 0 and value != self.__scale:
            self.__scale = value
            # need to recalculate min/max according to new scale
            self.setNaturalMin(self.__naturalMinimumValue)
            self.setNaturalMax(self.__naturalMaximumValue)
            self.setNaturalValue(self.__naturalValue)
