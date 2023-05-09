# -----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2021 - Grum999
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
# A Krita plugin designed to manage notes
# -----------------------------------------------------------------------------

import re
import sys
import time

import PyQt5.uic

from krita import (
        DockWidget,
        Krita
    )

from PyQt5.Qt import *
from PyQt5 import QtCore
from PyQt5.QtCore import (
        pyqtSlot
    )

if __name__ != '__main__':
    # script is executed from Krita, loaded as a module
    __PLUGIN_EXEC_FROM__ = 'KRITA'

    from .pktk.pktk import (
            EInvalidStatus,
            EInvalidType,
            EInvalidValue,
            PkTk
        )
    from bulinotes.pktk.modules.utils import checkKritaVersion
    from bulinotes.bn.bnuidocker import BNUiDocker
else:
    # Execution from 'Scripter' plugin?
    __PLUGIN_EXEC_FROM__ = 'SCRIPTER_PLUGIN'

    from importlib import reload

    print("======================================")
    print(f'Execution from {__PLUGIN_EXEC_FROM__}')

    for module in list(sys.modules.keys()):
        if not re.search(r'^bulinotes\.', module) is None:
            print('Reload module {0}: {1}', module, sys.modules[module])
            reload(sys.modules[module])

    from selectionmanager.pktk.pktk import (
            EInvalidStatus,
            EInvalidType,
            EInvalidValue,
            PkTk
        )
    from bulinotes.pktk.modules.utils import checkKritaVersion
    from bulinotes.bn.bnuidocker import BNUiDocker

    print("======================================")


EXTENSION_ID = 'pykrita_bulinotes'
PLUGIN_VERSION = '1.0.2'
PLUGIN_MENU_ENTRY = 'Buli Notes'

REQUIRED_KRITA_VERSION = (5, 1, 0)


class BuliNotesDocker(DockWidget):
    """Class to manage current selection"""

    def __init__(self):
        super(BuliNotesDocker, self).__init__()
        self.__ui = None

        self.setWindowTitle(PLUGIN_MENU_ENTRY)
        if checkKritaVersion(*REQUIRED_KRITA_VERSION):
            self.__ui = BNUiDocker(self, PLUGIN_MENU_ENTRY, EXTENSION_ID, PLUGIN_VERSION)
            self.setWidget(self.__ui)
        else:
            self.setWidget(QLabel('Current version of Krita is not supported\nPlugin require Krita 5'))

    def canvasChanged(self, canvas):
        """Notify when views are added or removed"""
        if self.__ui:
            self.__ui.canvasChanged(canvas)
