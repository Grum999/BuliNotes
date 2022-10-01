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
# The wexportoptions module provides widgets with basic interface that can be
# used to manage PNG & JPEG export options
# Both widghet returns InfoObject() instance that can be passed to krita's
# 'Save as' method
#
# Main class from this module
#
# - WExportOptionsPng:
#       Widget
#       Manage the export options for PNG file
#
# - WExportOptionsJpeg:
#       Widget
#       Manage the export options for JPEG file
#
# -----------------------------------------------------------------------------

import PyQt5.uic

import os
import sys

from krita import InfoObject

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from ..modules.utils import loadXmlUi
from .wcolorselector import WColorPicker
from .wcolorbutton import WColorButton
from ..pktk import *


class WExportOptionsPng(QWidget):
    """A wdiget to manage PNG export options"""
    optionUpdated = Signal()          # when an option is changed from user interface
    optionChanged = Signal()          # when options are changed programmatically

    def __init__(self, parent=None):
        super(WExportOptionsPng, self).__init__(parent)

        uiFileName = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wexportoptionspng.ui')

        # temporary add <plugin> path to sys.path to let 'pktk.widgets.xxx' being accessible during xmlLoad()
        # because of WColorButton path that must be absolut in UI file
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        loadXmlUi(uiFileName, self)

        # remove temporary added path
        sys.path.pop()

        self.rbStoreAlpha.toggled.connect(self.__transparentColorState)
        self.pbBgColor.colorPicker().setStandardLayout('hsv')
        self.pbBgColor.colorPicker().setOptionMenu(WColorPicker.OPTION_MENU_ALL & ~WColorPicker.OPTION_MENU_ALPHA)
        self.__transparentColorState(self.rbStoreAlpha.isChecked())

        self.hsCompressionLevel.valueChanged.connect(self.__propUpdated)
        self.cbIndexed.stateChanged.connect(self.__propUpdated)
        self.cbInterlacing.stateChanged.connect(self.__propUpdated)
        self.cbSaveICCProfile.stateChanged.connect(self.__propUpdated)
        self.cbForceConvertsRGB.stateChanged.connect(self.__propUpdated)
        self.rbStoreAlpha.toggled.connect(self.__propUpdated)
        self.rbUseBgColor.toggled.connect(self.__propUpdated)
        self.pbBgColor.colorChanged.connect(self.__propUpdated)

    def __propUpdated(self, value):
        """A property has been updated"""
        self.optionUpdated.emit()

    def __transparentColorState(self, checked):
        """Change Transparent color button state (enabled/disables) according to current 'Store Alpha Channel' option"""
        self.pbBgColor.setEnabled(not checked)

    def options(self, asInfoObject=False):
        """Return current options

        If `asInfoObject` is True, return a InfoObject otherwise a dictionary
        """
        if asInfoObject:
            color = self.pbBgColor.color()

            returned = InfoObject()
            returned.setProperty('compression', self.hsCompressionLevel.value())
            returned.setProperty('indexed', self.cbIndexed.isChecked())
            returned.setProperty('interlaced', self.cbInterlacing.isChecked())
            returned.setProperty('saveSRGBProfile', self.cbSaveICCProfile.isChecked())
            returned.setProperty('forceSRGB', self.cbForceConvertsRGB.isChecked())
            returned.setProperty('alpha', self.rbStoreAlpha.isChecked())
            returned.setProperty('transparencyFillcolor', QColor(color))
        else:
            returned = {
                'compression': self.hsCompressionLevel.value(),
                'indexed': self.cbIndexed.isChecked(),
                'interlaced': self.cbInterlacing.isChecked(),
                'saveSRGBProfile': self.cbSaveICCProfile.isChecked(),
                'forceSRGB': self.cbForceConvertsRGB.isChecked(),
                'alpha': self.rbStoreAlpha.isChecked(),
                'transparencyFillcolor': self.pbBgColor.color()
            }

        return returned

    def setOptions(self, options=None):
        """Set current options

        Given `options` can be a dictionary or an InfoObject
        If None is provided, default options are set
        """
        def ioProp(property, default):
            returned = options.property(property)
            if returned is None:
                returned = default
            return returned

        if options is None:
            options = {}

        if isinstance(options, dict):
            self.hsCompressionLevel.setValue(options.get('compression', 6))
            self.sbCompressionLevel.setValue(options.get('compression', 6))
            self.cbIndexed.setChecked(options.get('indexed', False))
            self.cbInterlacing.setChecked(options.get('interlaced', False))
            self.cbSaveICCProfile.setChecked(options.get('saveSRGBProfile', False))
            self.cbForceConvertsRGB.setChecked(options.get('forceSRGB', False))
            self.rbStoreAlpha.setChecked(options.get('alpha', False))
            self.pbBgColor.setColor(options.get('transparencyFillcolor', Qt.white))
        elif isinstance(options, InfoObject):
            self.hsCompressionLevel.setValue(ioProp('compression', 6))
            self.sbCompressionLevel.setValue(ioProp('compression', 6))
            self.cbIndexed.setChecked(ioProp('indexed', False))
            self.cbInterlacing.setChecked(ioProp('interlaced', False))
            self.cbSaveICCProfile.setChecked(ioProp('saveSRGBProfile', False))
            self.cbForceConvertsRGB.setChecked(ioProp('forceSRGB', False))
            self.rbStoreAlpha.setChecked(ioProp('alpha', False))
            self.pbBgColor.setColor(ioProp('transparencyFillcolor', Qt.white))

        self.__transparentColorState(self.rbStoreAlpha.isChecked())

        self.optionChanged.emit()


class WExportOptionsJpeg(QWidget):
    """A wdiget to manage JPEG export options"""
    optionUpdated = Signal()          # when an option is changed from user interface
    optionChanged = Signal()          # when options are changed programmatically

    def __init__(self, parent=None):
        super(WExportOptionsJpeg, self).__init__(parent)

        uiFileName = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wexportoptionsjpeg.ui')

        # temporary add <plugin> path to sys.path to let 'pktk.widgets.xxx' being accessible during xmlLoad()
        # because of WColorButton path that must be absolut in UI file
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        loadXmlUi(uiFileName, self)

        # remove temporary added path
        sys.path.pop()

        self.pbBgColor.colorPicker().setStandardLayout('hsv')
        self.pbBgColor.colorPicker().setOptionMenu(WColorPicker.OPTION_MENU_ALL & ~WColorPicker.OPTION_MENU_ALPHA)

        self.hsQuality.valueChanged.connect(self.__propUpdated)
        self.hsSmoothing.valueChanged.connect(self.__propUpdated)
        self.cbxSubsampling.currentIndexChanged.connect(self.__propUpdated)
        self.cbProgressive.stateChanged.connect(self.__propUpdated)
        self.cbOptimize.stateChanged.connect(self.__propUpdated)
        self.cbSaveICCProfile.stateChanged.connect(self.__propUpdated)
        self.pbBgColor.colorChanged.connect(self.__propUpdated)

    def __propUpdated(self, value=None):
        """A property has been updated"""
        self.optionUpdated.emit()

    def options(self, asInfoObject=False):
        """Return current options

        If `asInfoObject` is True, return a InfoObject otherwise a dictionary
        """
        if asInfoObject:
            color = self.pbBgColor.color()

            returned = InfoObject()
            returned.setProperty('quality', self.hsQuality.value())
            returned.setProperty('smoothing', self.hsSmoothing.value())
            returned.setProperty('subsampling', self.cbxSubsampling.currentIndex())
            returned.setProperty('progressive', self.cbProgressive.isChecked())
            returned.setProperty('optimize', self.cbOptimize.isChecked())
            returned.setProperty('saveProfile', self.cbSaveICCProfile.isChecked())
            returned.setProperty('transparencyFillcolor', QColor(color))
        else:
            returned = {
                'quality': self.hsQuality.value(),
                'smoothing': self.hsSmoothing.value(),
                'subsampling': self.cbxSubsampling.currentIndex(),
                'progressive': self.cbProgressive.isChecked(),
                'optimize': self.cbOptimize.isChecked(),
                'saveProfile': self.cbSaveICCProfile.isChecked(),
                'transparencyFillcolor': self.pbBgColor.color()
            }

        return returned

    def setOptions(self, options=None):
        """Set current options

        Given `options` can be a dictionary or an InfoObject
        If None is provided, default options are set
        """
        def ioProp(property, default):
            returned = options.property(property)
            if returned is None:
                returned = default
            return returned

        if options is None:
            options = {}

        if isinstance(options, dict):
            self.hsQuality.setValue(options.get('quality', 85))
            self.sbQuality.setValue(options.get('quality', 85))
            self.hsSmoothing.setValue(options.get('smoothing', 15))
            self.sbSmoothing.setValue(options.get('smoothing', 15))
            self.cbxSubsampling.setCurrentIndex(options.get('subsampling', 0))
            self.cbProgressive.setChecked(options.get('progressive', True))
            self.cbOptimize.setChecked(options.get('optimize', True))
            self.cbSaveICCProfile.setChecked(options.get('saveProfile', False))
            self.pbBgColor.setColor(options.get('transparencyFillcolor', Qt.white))
        elif isinstance(options, InfoObject):
            self.hsQuality.setValue(ioProp('quality', 85))
            self.sbQuality.setValue(ioProp('quality', 85))
            self.hsSmoothing.setValue(ioProp('smoothing', 15))
            self.sbSmoothing.setValue(ioProp('smoothing', 15))
            self.cbxSubsampling.setCurrentIndex(ioProp('subsampling', 0))
            self.cbProgressive.setChecked(ioProp('progressive', True))
            self.cbOptimize.setChecked(ioProp('optimize', True))
            self.cbSaveICCProfile.setChecked(ioProp('saveProfile', False))
            self.pbBgColor.setColor(ioProp('transparencyFillcolor', Qt.white))

        self.optionChanged.emit()
