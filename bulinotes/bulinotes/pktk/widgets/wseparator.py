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


from PyQt5.Qt import *

class WVLine(QFrame):
    """A vertical line widget that can be used as a separator"""

    def __init__(self, parent=None):
        super(WVLine, self).__init__(parent)
        self.setFrameShape(self.VLine|self.Sunken)


class WHLine(QFrame):
    """A horizontal line widget that can be used as a separator"""

    def __init__(self, parent=None):
        super(WHLine, self).__init__(parent)
        self.setFrameShape(self.HLine|self.Sunken)
