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
# The wkeysequenceinput module provides an extended version of QKeySequenceEdit
# widget
#
# Main class from this module
#
# - WKeySequenceInput:
#       Widget
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QKeySequenceEdit

from ..modules.utils import replaceLineEditClearButton


class WKeySequenceInput(QKeySequenceEdit):
    """An improved version of QKeySequenceEdit"""
    keySequenceCleared = Signal()

    def __init__(self, parent=None):
        super(WKeySequenceInput, self).__init__(parent)

        self.__lineEdit = self.findChild(QLineEdit)
        self.__lineEdit.textChanged.connect(self.__textChanged)

    def __textChanged(self, value):
        """Text has been changed"""
        if value == '':
            self.clear()
            self.keySequenceCleared.emit()

    def isClearButtonEnabled(self, value):
        """Return if clear button is displayed or not"""
        self.__lineEdit.isClearButtonEnabled()

    def setClearButtonEnabled(self, value):
        """Display or not clear button"""
        self.__lineEdit.setClearButtonEnabled(value)
        if value:
            replaceLineEditClearButton(self.__lineEdit)

    # def event(self, event):
    #    print("event", event, event.type())
    #    return super(WKeySequenceInput, self).event(event)

    # def keyPressEvent(self, event):
    #    print("keyPressEvent", event, event.text(), event.key(), event.modifiers())
    #    super(WKeySequenceInput, self).keyPressEvent(event)

    # def keyReleaseEvent(self, event):
    #    print("keyReleaseEvent", event, event.text(), event.key(), event.modifiers())
    #    super(WKeySequenceInput, self).keyReleaseEvent(event)

    # def timerEvent(self, event):
    #    print("timerEvent", event)
    #    super(WKeySequenceInput, self).timerEvent(event)
