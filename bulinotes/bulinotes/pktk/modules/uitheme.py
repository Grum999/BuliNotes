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
# The uitheme module provides a generic class to use to manage current theme
#
# Main class from this module
#
# - UITheme:
#       Main class to manage themes
#       Provide init ans static methods to load theme (icons, colors) according
#       to current Krita theme
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Build resources files:
#   cd .../.../resources
#   /usr/lib/qt5/bin/rcc --binary -o ./lighttheme_icons.rcc light_icons.qrc
#   /usr/lib/qt5/bin/rcc --binary -o ./darktheme_icons.rcc dark_icons.qrc
# -----------------------------------------------------------------------------

import krita
import os
import re

from PyQt5.QtCore import (
        QResource
    )
from PyQt5.QtGui import (
        QPalette,
        QPixmapCache
    )
from PyQt5.QtWidgets import (
        QApplication
    )


from ..pktk import *


# -----------------------------------------------------------------------------

class UITheme(object):
    """Manage theme

    By default, DARK and LIGHT themes are managed
    """

    DARK_THEME = 'dark'
    LIGHT_THEME = 'light'

    STYLES_SHEET = {
        'dark': {
                'warning-label': 'background-color: rgba(255, 255, 200, 75%); color:#440000; border: 1px solid rgba(255, 255, 200, 25%); border-radius: 3px; font-weight: bold;',
                'warning-box': 'background-color: rgba(255, 255, 200, 100%); color:#440000; border: 1px solid rgba(255, 255, 200, 100%); border-radius: 3px;'
            },
        'light': {

            }
    }

    __themes = {}
    __kraActiveWindow = None

    @staticmethod
    def load(rccPath=None, autoReload=True):
        """Initialise theme"""
        def initThemeChanged():
            # initialise theme when main window is created
            if UITheme.__kraActiveWindow is None:
                UITheme.__kraActiveWindow = Krita.instance().activeWindow()
                if UITheme.__kraActiveWindow is not None:
                    UITheme.__kraActiveWindow.themeChanged.connect(UITheme.reloadResources)

        if rccPath is None:
            # by default if no path is provided, load default PkTk theme
            rccPath = PkTk.PATH_RESOURCES

        if rccPath not in UITheme.__themes:
            UITheme.__themes[rccPath] = UITheme(rccPath, autoReload)

        # Initialise connector on theme changed
        initThemeChanged()

        # If not initialised (main window not yet created), initialise it when main window is created
        if UITheme.__kraActiveWindow is None:
            Krita.instance().notifier().windowCreated.connect(initThemeChanged)

    @staticmethod
    def reloadResources(clearPixmapCache=None):
        """Reload resources"""
        if clearPixmapCache is None:
            clearPixmapCache = True
        for theme in UITheme.__themes:
            if UITheme.__themes[theme].getAutoReload():
                # reload
                UITheme.__themes[theme].loadResources(clearPixmapCache)
                if clearPixmapCache:
                    clearPixmapCache = False

    @staticmethod
    def style(name):
        """Return style according to current theme"""
        for theme in UITheme.__themes:
            # return style from first theme (should be the same for all themes)
            return UITheme.__themes[theme].getStyle(name)

    @staticmethod
    def theme():
        """Return style according to current theme"""
        for theme in UITheme.__themes:
            # return style from first theme (should be the same for all themes)
            return UITheme.__themes[theme].getTheme()

    def __init__(self, rccPath, autoReload=True):
        """The given `rccPath` is full path to directory where .rcc files can be found
        If None, default resources from PkTk will be loaded

        The .rcc file names must match the following pattern:
        - darktheme_icons.rcc
        - lighttheme_icons.rcc


        If `autoReload` is True, theme is reloaded automatically when theme is changed
        Otherwise it have to be implemented explicitely in plugin
        """
        self.__theme = UITheme.DARK_THEME
        self.__registeredResource = None
        self.__rccPath = rccPath
        self.__autoReload = autoReload
        self.__kraActiveWindow = None

        self.loadResources(False)

    def loadResources(self, clearPixmapCache=True):
        """Load resources for current theme"""
        # Need to clear pixmap cache otherwise some icons are not reloaded from new resource file
        if clearPixmapCache:
            QPixmapCache.clear()

        if self.__registeredResource is not None:
            QResource.unregisterResource(self.__registeredResource)

        palette = QApplication.palette()

        if palette.color(QPalette.Window).value() <= 128:
            self.__theme = UITheme.DARK_THEME
        else:
            self.__theme = UITheme.LIGHT_THEME

        if re.search(r"\.rcc$", self.__rccPath):
            self.__registeredResource = self.__rccPath
        else:
            self.__registeredResource = os.path.join(self.__rccPath, f'{self.__theme}theme_icons.rcc')

        if not QResource.registerResource(self.__registeredResource):
            self.__registeredResource = None

    def getTheme(self):
        """Return current theme"""
        return self.__theme

    def getStyle(self, name):
        """Return style according to current theme"""
        if name in UITheme.STYLES_SHEET[self.__theme]:
            return UITheme.STYLES_SHEET[self.__theme][name]
        elif self.__theme != UITheme.DARK_THEME and name in UITheme.STYLES_SHEET[UITheme.DARK_THEME]:
            return UITheme.STYLES_SHEET[UITheme.DARK_THEME][name]
        return ''

    def getAutoReload(self):
        """Return if autoreload is activated for theme"""
        return self.__autoReload
