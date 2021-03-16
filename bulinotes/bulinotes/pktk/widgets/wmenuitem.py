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
import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QAction,
        QApplication,
        QFrame,
        QHBoxLayout,
        QVBoxLayout,
        QLabel,
        QMenu,
        QSlider,
        QWidget
    )

from krita import PresetChooser



class WMenuSlider(QWidgetAction):
    """Encapsulate a slider as a menu item"""
    def __init__(self, label, parent=None):
        super(WMenuSlider, self).__init__(parent)

        self.__widget = QWidget()
        self.__layout = QVBoxLayout()
        self.__slider = QSlider()
        self.__slider.setOrientation(Qt.Horizontal)

        if not label is None and label != '':
            self.__layout.addWidget(QLabel(label))
        self.__layout.addWidget(self.__slider)
        self.__widget.setLayout(self.__layout)
        self.setDefaultWidget(self.__widget)

    def slider(self):
        return self.__slider


class WMenuTitle(QWidgetAction):
    """Encapsulate a QLabel as a menu item title"""
    def __init__(self, label, parent=None):
        super(WMenuTitle, self).__init__(parent)

        self.__widget = QWidget()
        self.__layout = QVBoxLayout()
        self.__label = QLabel(label)
        self.__label.setStyleSheet("background-color: palette(light);padding: 3; font: bold;")
        self.__layout.addWidget(self.__label)
        self.__widget.setLayout(self.__layout)
        self.setDefaultWidget(self.__widget)


class WMenuBrushesPresetSelector(QWidgetAction):
    """Encapsulate a PresetChooser as a menu item"""
    def __init__(self, parent=None):
        super(WMenuBrushesPresetSelector, self).__init__(parent)

        self.__presetChooser = PresetChooser()
        self.__presetChooser.setMinimumSize(350,400)

        self.setDefaultWidget(self.__presetChooser)

    def presetChooser(self):
        return self.__presetChooser
