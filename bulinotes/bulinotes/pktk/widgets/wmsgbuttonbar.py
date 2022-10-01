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
# The wmsgbuttonbar module provides an area to display message with button
# logarithmic values
#
# Main class from this module
#
# - WMessageButtonBar:
#       Widget
#       The main button bar widget
#
# - WMessageButton:
#       Widget
#       Button to add in button bar
#
# -----------------------------------------------------------------------------

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )


from ..pktk import *


class WMessageButton(QToolButton):
    """A button for WMessageButtonBar"""
    def __init__(self, label, value, toolTip=None, parent=None):
        super(WMessageButton, self).__init__(parent)

        self.setText(label)
        self.__value = value

        if isinstance(toolTip, str):
            self.setToolTip(toolTip)

    def value(self):
        """Return value for button"""
        return self.__value


class WMessageButtonBar(QWidget):
    """The widget message button bar is a widget that allow to:
    - display a message
    - display buttons


    Example:
        msgBtnBar=WMessageButtonBar()
        msgBtnBar.buttonClicked.connect(buttonClickedCallback)


        msgBtnBar.message('File has been modified\nDoyou want to reload it?',
                          WMessageButton('Reload', 0),
                          WMessageButton('Overwrite', 1),
                          WMessageButton('Cancel', 2)
                        )

        Will provide:
            +--------------------------------------------------------------------------+
            | File has been modified                     [Reload] [Overwrite] [Cancel] |
            | Do you want to reload it?                                                |
            +--------------------------------------------------------------------------+
    """
    buttonClicked = Signal(QVariant)

    def __init__(self, parent=None):
        super(WMessageButtonBar, self).__init__(parent)

        w = QWidget()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(w)

        self.__layout = QHBoxLayout(w)
        self.__layout.setContentsMargins(3, 3, 3, 3)

        self.__label = QLabel()

        self.__layout.addWidget(self.__label)
        self.__layout.addStretch()

        self.__optionAutoHide = True

        self.hide()

    def __btnClicked(self, dummy=None):
        if self.__optionAutoHide:
            self.hide()
        self.buttonClicked.emit(self.sender().value())

    def autoHide(self):
        """Return if WMessageButtonBar is hidden automatically when a button is clicked"""
        return self.__optionAutoHide

    def setAutoHide(self, value):
        """Set if WMessageButtonBar is hidden automatically when a button is clicked"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be <bool>")
        self.__optionAutoHide = value

    def message(self, message, *buttons):
        """Display message box"""

        for index in reversed(range(self.__layout.count())):
            child = self.__layout.itemAt(index)
            if isinstance(child.widget(), QToolButton):
                child = self.__layout.takeAt(index)
                child.widget().deleteLater()

        self.__label.setText(message)

        nbButtons = 0
        for button in buttons:
            if isinstance(button, WMessageButton):
                button.clicked.connect(self.__btnClicked)
                self.__layout.addWidget(button)
                nbButtons += 1
            else:
                raise EInvalidType("Given `buttons` must be <WMessageButton>")

        if nbButtons == 0:
            # no buttons?
            # add a "OK" button (consider that's just an information message)
            button = WMessageButton(i18n('Ok'), 0, i18n('Hide message'))
            button.clicked.connect(self.__btnClicked)
            self.__layout.addWidget(button)

        self.show()
