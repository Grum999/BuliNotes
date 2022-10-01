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
# The wmenuitem module provides a set a QWidgetAction to use in menu
# logarithmic values
#
# Main class from this module
#
# - WMenuSlider:
#       WidgetAction
#       Add a slider inside a menu
#
# - WMenuTitle:
#       WidgetAction
#       Add static title label inside a menu
#
# - WMenuBrushesPresetSelector:
#       WidgetAction
#       Add brush preset selector inside a menu
#
# - WMenuColorPicker:
#       WidgetAction
#       Add color picker inside a menu
#
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
from .wcolorselector import WColorPicker


class WMenuSlider(QWidgetAction):
    """Encapsulate a slider as a menu item"""
    maxToolBarSliderWidthChanged = Signal(int)

    class InternalSlider(QWidget):
        textChanged = Signal(str)

        def __init__(self, label, parent=None):
            super(WMenuSlider.InternalSlider, self).__init__(parent)

            self.__layout = QBoxLayout(QBoxLayout.TopToBottom)
            self.__slider = QSlider()
            self.__slider.setOrientation(Qt.Horizontal)
            self.__label = QLabel()

            self.__layout.setSpacing(0)
            self.__layout.addWidget(self.__label)
            self.__layout.addWidget(self.__slider)

            self.setLabelText(label)
            self.setLayout(self.__layout)

        def contentsMargins(self):
            """Return content margins for widget"""
            return self.__layout.contentsMargins()

        def setContentsMargins(self, *parameters):
            """Return content margins for widget"""
            self.__layout.setContentsMargins(*parameters)

        def setLayoutOrientation(self, value):
            """set layout orientation

            Value can be:
                Qt.Horizontal
                Qt.Vertical
            """
            if value not in (Qt.Horizontal, Qt.Vertical):
                return
            elif value == Qt.Vertical:
                self.__layout.setDirection(QBoxLayout.TopToBottom)
                self.__layout.setSpacing(0)
                self.__label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
                self.__slider.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
            else:
                self.__layout.setDirection(QBoxLayout.LeftToRight)
                self.__layout.setSpacing(-1)
                self.__label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)
                self.__slider.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)

        def label(self):
            """Return current label"""
            return self.__label

        def labelText(self):
            """Return current label text"""
            return self.__label.text()

        def setLabelText(self, value):
            """Set current label text"""
            if value == '' or value is None:
                self.textChanged.emit('')
                self.__label.setVisible(False)
                return
            elif isinstance(value, QPixmap):
                self.textChanged.emit('')
                self.__label.setPixmap(value)
            else:
                self.__label.setText(value)
                self.textChanged.emit(value)
            self.__label.setVisible(True)

        def slider(self):
            return self.__slider

    def __init__(self, label, parent=None):
        super(WMenuSlider, self).__init__(parent)
        self.__widget = WMenuSlider.InternalSlider(label, parent)
        self.__maxTbSliderWidth = 250
        self.__updating = False
        self.setDefaultWidget(self.__widget)

    def labelText(self):
        """Return current label text"""
        return self.__widget.labelText()

    def setLabelText(self, value):
        """Set current label text"""
        self.__widget.setLabelText(value)

    def slider(self):
        return self.__widget.slider()

    def maxToolBarSliderWidth(self):
        """Return maximum width for slider when in a toolbar"""
        return self.__maxTbSliderWidth

    def setMaxToolBarSliderWidth(self, value):
        """Set maximum width for slider when in a toolbar"""
        if isinstance(value, int) and value >= 0:
            emitSignal = (self.__maxTbSliderWidth != value)
            self.__maxTbSliderWidth = value
            if emitSignal:
                self.maxToolBarSliderWidthChanged.emit(value)

    def createWidget(self, parent=None):
        """Create dedicated widget for toolbar

        Toolbar widget is linked with QWidgetAction
        """
        def updateSlider(value, targetSlider):
            if self.__updating:
                return
            self.__updating = True
            targetSlider.setValue(value)
            self.__updating = False

        if isinstance(parent, QToolBar):
            returned = WMenuSlider.InternalSlider(self.__widget.labelText(), parent)
            returned.setLayoutOrientation(Qt.Horizontal)
            returned.slider().setRange(self.__widget.slider().minimum(), self.__widget.slider().maximum())
            returned.slider().setValue(self.__widget.slider().value())
            returned.setContentsMargins(0, 0, 0, 0)
            returned.slider().setMaximumWidth(self.__maxTbSliderWidth)

            # link with widget
            self.__widget.slider().rangeChanged.connect(lambda valueMin, valueMax: returned.slider().setRange(valueMin, valueMax))
            self.__widget.slider().valueChanged.connect(lambda value: updateSlider(value, returned.slider()))
            self.__widget.textChanged.connect(lambda value: returned.slider().setToolTip(value))
            self.maxToolBarSliderWidthChanged.connect(lambda value: returned.slider().setMaximumWidth(value))
            returned.slider().valueChanged.connect(lambda value: updateSlider(value, self.__widget.slider()))
            return returned

        return None


class WMenuTitle(QWidgetAction):
    """Encapsulate a QLabel as a menu item title"""
    def __init__(self, label, parent=None):
        super(WMenuTitle, self).__init__(parent)
        self.__widget = QWidget()
        self.__layout = QVBoxLayout()
        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)
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
        self.__presetChooser.setMinimumSize(350, 400)

        self.setDefaultWidget(self.__presetChooser)

    def presetChooser(self):
        return self.__presetChooser


class WMenuColorPicker(QWidgetAction):
    """Encapsulate a WColorPicker as a menu item"""
    def __init__(self, parent=None):
        super(WMenuColorPicker, self).__init__(parent)

        self.__colorPicker = WColorPicker()
        self.__colorPicker.setCompactSize(350)
        self.__colorPicker.setNormalSize(450)
        self.__colorPicker.setConstraintSize(True)
        self.__colorPicker.setContentsMargins(6, 6, 6, 6)

        self.__colorPicker.uiChanged.connect(self.__resizeMenu)
        self.__colorPicker.colorUpdated.connect(self.__closeMenu)

        self.setDefaultWidget(self.__colorPicker)

    def __closeMenu(self):
        if self.__colorPicker.optionShowColorPalette():
            if (self.__colorPicker.optionShowColorRGB() or
               self.__colorPicker.optionShowColorCMYK() or
               self.__colorPicker.optionShowColorHSV() or
               self.__colorPicker.optionShowColorHSL() or
               self.__colorPicker.optionShowColorAlpha() or
               self.__colorPicker.optionShowColorCssRGB() or
               self.__colorPicker.optionShowColorWheel() or
               self.__colorPicker.optionShowColorCombination()):
                return
            for parentWidget in self.associatedWidgets():
                parentWidget.hide()

    def __resizeMenu(self):
        """Resize menu when menu item content size has been changed"""
        if self.sender() and self.sender().parent():
            event = QActionEvent(QEvent.ActionChanged, self)
            QApplication.sendEvent(self.sender().parent(), event)

    def colorPicker(self):
        return self.__colorPicker
