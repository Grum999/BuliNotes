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
        self.__value=value

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
    buttonClicked=Signal(QVariant)

    def __init__(self, parent=None):
        super(WMessageButtonBar, self).__init__(parent)

        self.__layout = QHBoxLayout(self)
        self.__layout.setContentsMargins(3,3,3,3)

        self.__label=QLabel()

        self.__layout.addWidget(self.__label)
        self.__layout.addStretch()

        self.__optionAutoHide=True

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
        self.__optionAutoHide=value

    def message(self, message, *buttons):
        """Display message box"""

        for index in reversed(range(self.__layout.count())):
            child = self.__layout.itemAt(index)
            if isinstance(child.widget(), QToolButton):
                child = self.__layout.takeAt(index)
                child.widget().deleteLater()

        self.__label.setText(message)

        nbButtons=0
        for button in buttons:
            if isinstance(button, WMessageButton):
                button.clicked.connect(self.__btnClicked)
                self.__layout.addWidget(button)
                nbButtons+=1
            else:
                raise EInvalidType("Given `buttons` must be <WMessageButton> or <WMessageButtonBarStyle>")


        if nbButtons==0:
            # no buttons?
            # add a "OK" button (consider that's just an information message)
            button=WMessageButton(i18n('Ok'), 0, i18n('Hide message')),
            button.clicked.connect(self.__btnClicked)
            self.__layout.addWidget(button)

        self.show()
