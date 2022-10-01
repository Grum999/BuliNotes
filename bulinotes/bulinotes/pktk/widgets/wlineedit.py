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
# The wlineedit module provides an extended version of QLineEdit
#
# Main class from this module
#
# - WLineEdit:
#       Widget
#       The main line edit widget
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from ..modules.utils import (
        replaceLineEditClearButton,
        regExIsValid
    )
from ..pktk import *


class WLineEdit(QLineEdit):
    """A QLineEdit with signals emitted when focus In/Out changed"""
    focusIn = Signal()
    focusOut = Signal()
    keyPressed = Signal(QKeyEvent, str, str)

    def __init__(self, parent=None):
        super(WLineEdit, self).__init__(parent)
        self.__regExValue = False
        self.__regExValid = None
        self.setClearButtonEnabled(True)
        replaceLineEditClearButton(self)

    def __checkRegEx(self):
        """Check if current value is a valid regular expression"""
        if self.__regExValue:
            self.__regExValid = regExIsValid(self.text())

    def focusInEvent(self, event):
        super(WLineEdit, self).focusInEvent(event)
        self.focusIn.emit()

    def focusOutEvent(self, event):
        super(WLineEdit, self).focusOutEvent(event)
        self.focusOut.emit()

    def keyPressEvent(self, event):
        before = self.text()
        super(WLineEdit, self).keyPressEvent(event)
        self.__checkRegEx()
        self.keyPressed.emit(event, self.text(), before)

    def isRegExValid(self):
        """return is regular expression is valid or not

        If field is not a regular expression editor, return None

        Note: there's no signal concerning regex... need to connec keyPressed Signal and check if regular expression is valid
        """
        return self.__regExValid

    def isRegEx(self):
        """Return if line editor is defined as a regex editor"""
        return self.__regExValue

    def setRegEx(self, value):
        """Set if line editor is defined as a regex editor"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be <bool>")

        if self.__regExValue != value:
            self.__regExValue = value
            if self.__regExValue:
                self.__regExValid = None
                self.__checkRegEx()
