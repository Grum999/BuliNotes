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


# Build resources files:
#   cd .../.../resources
#   /usr/lib/qt5/bin/rcc --binary -o ./lighttheme_icons.rcc light_icons.qrc
#   /usr/lib/qt5/bin/rcc --binary -o ./darktheme_icons.rcc dark_icons.qrc


import krita
import os

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


from pktk import PkTk

# -----------------------------------------------------------------------------
PkTk.setModuleInfo(
    'uitheme',
    '1.0.0',
    'UITheme',
    'Provides a class to manage resources for theme easily'
)

# -----------------------------------------------------------------------------
class UITheme(object):
    """Manage theme

    By default, DARK and LIGHT themes are managed
    """

    DARK_THEME = 'dark'
    LIGHT_THEME = 'light'

    STYLES_SHEET = {
        'dark': {
                'warning-label': 'background-color: rgba(255, 255, 200, 75%); color:#440000; border: 1px solid rgba(255, 255, 200, 25%); border-radius: 3px; font-weight: bold;'
            },
        'light': {

            }
    }


    def __init__(self, rccPath, autoReload=True):
        """The given `rccPath` is full path to directory where .rcc files can be found

        The .rcc file names must mathc the following pattern:
        - darktheme_icons.rcc
        - lighttheme_icons.rcc


        If `autoReload` is True, theme is reloaded automatically when theme is changed
        Otherwise it have to be implemented explicitely in plugin
        """
        self.__theme = UITheme.DARK_THEME
        self.__registeredResource = None
        self.__rccPath=rccPath
        self.__autoReload=autoReload
        self.__kraActiveWindow=None
        self.__notifier=None

        if autoReload:
            Krita.instance().notifier().windowCreated.connect(self.__windowCreated)

        self.loadResources()


    def __windowCreated(self):
        """Krita window is created

        If auto reload has been defined for theme, need to connect 'themeChanged' signal
        """
        if self.__kraActiveWindow is None:
            self.__kraActiveWindow=Krita.instance().activeWindow()
            if self.__autoReload and not self.__kraActiveWindow is None:
                self.__kraActiveWindow.themeChanged.connect(self.loadResources)


    def loadResources(self):
        """Load resources for current theme"""
        # Need to clear pixmap cache otherwise some icons are not reloaded from new resource file
        QPixmapCache.clear()

        if not self.__registeredResource is None:
            QResource.unregisterResource(self.__registeredResource)

        palette = QApplication.palette()

        if palette.color(QPalette.Window).value() <= 128:
            self.__theme = UITheme.DARK_THEME
        else:
            self.__theme = UITheme.LIGHT_THEME

        self.__registeredResource = os.path.join(self.__rccPath, f'{self.__theme}theme_icons.rcc')

        if not QResource.registerResource(self.__registeredResource):
            self.__registeredResource = None


    def theme(self):
        """Return current theme"""
        return self.__theme


    def style(self, name):
        """Return style according to current theme"""
        if name in UITheme.STYLES_SHEET[self.__theme]:
            return UITheme.STYLES_SHEET[self.__theme][name]
        elif self.__theme != UITheme.DARK_THEME and name in UITheme.STYLES_SHEET[UITheme.DARK_THEME]:
            return UITheme.STYLES_SHEET[UITheme.DARK_THEME][name]
        return ''
