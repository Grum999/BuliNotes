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


# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtWidgets import QFileDialog

import os.path

class WEFileDialog(QFileDialog):
    """A file dialog with image preview"""

    PREVIEW_WIDTH=250

    def __init__(self, *args, **kwargs):
        QFileDialog.__init__(self, *args, **kwargs)

        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setMaximumSize(0xffffff, 0xffffff)

        self.__box = QVBoxLayout()

        self.__lblPreview = QLabel(i18n("Preview"), self)
        self.__lblPreview.setAlignment(Qt.AlignCenter)
        self.__lblPreview.setMinimumSize(WEFileDialog.PREVIEW_WIDTH, 0)

        self.__box.addWidget(self.__lblPreview)

        #self.layout().addLayout(self.__box, 1, 3, 1, 1)
        self.layout().addLayout(self.__box, 1, 3, Qt.AlignLeft)

        self.currentChanged.connect(self.__changed)
        self.fileSelected.connect(self.__fileSelected)
        self.filesSelected.connect(self.__filesSelected)

        self.__fileSelected = ''
        self.__filesSelected = []

    def showEvent(self, event):
        self.resize(self.width() + round(1.5*WEFileDialog.PREVIEW_WIDTH), self.height())


    def __changed(self, path):
        """File has been changed"""

        if not os.path.isdir(path):
            pixmap = QPixmap(path)

            if pixmap.isNull():
                self.__lblPreview.setText("Can't read file")
            else:
                self.__lblPreview.setPixmap(pixmap.scaled(self.__lblPreview.width(), self.__lblPreview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.__lblPreview.setText("No preview")

    def __fileSelected(self, file):
        self.__fileSelected = file

    def __filesSelected(self, files):
        self.__filesSelected = files

    def file(self):
        """return selected file name"""
        return self.__fileSelected

    def files(self):
        """return list of selected files"""
        return self.__filesSelected
