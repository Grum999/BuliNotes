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
# The wseparator module provides vertical and horizontal separator widgets
#
# Main class from this module
#
# - WVLine:
#       Widget
#       A vertical separator widget
#
# - WHLine:
#       Widget
#       A horinzontal separator widget
#
# -----------------------------------------------------------------------------


from PyQt5.Qt import *


class WVLine(QFrame):
    """A vertical line widget that can be used as a separator"""

    def __init__(self, parent=None):
        super(WVLine, self).__init__(parent)
        self.setFrameShape(self.VLine | self.Sunken)


class WHLine(QFrame):
    """A horizontal line widget that can be used as a separator"""

    def __init__(self, parent=None):
        super(WHLine, self).__init__(parent)
        self.setFrameShape(self.HLine | self.Sunken)
