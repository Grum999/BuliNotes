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
# The edialog module provides an extended QDialog widget
#
# Main class from this module
#
# - EDialog:
#       A QDialog for which UI file can be provided in constructor
#
# -----------------------------------------------------------------------------

import PyQt5.uic
from PyQt5.QtCore import (
        pyqtSignal
    )
from PyQt5.QtWidgets import (
        QDialog
    )

from ..pktk import *

# -----------------------------------------------------------------------------


class EDialog(QDialog):
    """Extended QDialog provides some signals and event to manage ui"""

    dialogShown = pyqtSignal()

    def __init__(self, uiFile=None, parent=None):
        super(EDialog, self).__init__(parent)
        self.__eventCallBack = {}
        if isinstance(uiFile, str):
            PyQt5.uic.loadUi(uiFile, self)

    @staticmethod
    def loadUi(fileName):
        """Create an EDialog object from given XML .ui file"""
        return PyQt5.uic.loadUi(fileName, EDialog())

    def showEvent(self, event):
        """Event trigerred when dialog is shown

           At this time, all widgets are initialised and size/visiblity is known

           Example
           =======
                # define callback function
                def my_callback_function():
                    # EDialog shown!"
                    pass

                # initialise a dialog from an xml .ui file
                dlgMain = EDialog.loadUi(uiFileName)

                # execute my_callback_function() when dialog became visible
                dlgMain.dialogShown.connect(my_callback_function)
        """
        super(EDialog, self).showEvent(event)
        self.dialogShown.emit()

    def eventFilter(self, object, event):
        """Manage event filters for dialog"""
        if object in self.__eventCallBack.keys():
            return self.__eventCallBack[object](event)

        return super(EDialog, self).eventFilter(object, event)

    def setEventCallback(self, object, method):
        """Add an event callback method for given object

           Example
           =======
                # define callback function
                def my_callback_function(event):
                    if event.type() == QEvent.xxxx:
                        # Event!
                        return True
                    return False


                # initialise a dialog from an xml .ui file
                dlgMain = EDialog.loadUi(uiFileName)

                # define callback for widget from ui
                dlgMain.setEventCallback(dlgMain.my_widget, my_callback_function)
        """
        if object is None:
            return False

        self.__eventCallBack[object] = method
        object.installEventFilter(self)
