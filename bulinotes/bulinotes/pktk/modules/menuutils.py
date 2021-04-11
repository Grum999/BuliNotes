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
# Menu&Actions utilities
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtGui import (
        QBrush,
        QPainter,
        QPixmap,
        QIcon
    )
from PyQt5.QtWidgets import (
        QAction,
        QMenu
    )

from .imgutils import buildIcon



def buildQAction(icons, title, parent, action=None, parameters=[]):
    """Build a QAction and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    def execute(dummy=None):
        if callable(action):
            action(*parameters)

    pixmapList=[]
    propertyList=[]
    for icon in icons:
        if isinstance(icon[0], QPixmap):
            pixmapListItem=[icon[0]]
            propertyListPath=''
        elif isinstance(icon[0], str):
            pixmapListItem=[QPixmap(icon[0])]
            propertyListPath=icon[0]

        for index in range(1,3):
            if index == 1:
                if len(icon) >= 2:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Normal)
            elif index == 2:
                if len(icon) >= 3:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Off)

        pixmapList.append(tuple(pixmapListItem))

        key = '__bcIcon_'
        if pixmapListItem[1]==QIcon.Normal:
            key+='normal'
        elif pixmapListItem[1]==QIcon.Active:
            key+='active'
        elif pixmapListItem[1]==QIcon.Disabled:
            key+='disabled'
        elif pixmapListItem[1]==QIcon.Selected:
            key+='selected'
        if pixmapListItem[2]==QIcon.Off:
            key+='off'
        else:
            key+='on'

        propertyList.append( (key, propertyListPath) )

    returnedAction=QAction(buildIcon(pixmapList), title, parent)

    for property in propertyList:
        returnedAction.setProperty(*property)

    if callable(action):
        returnedAction.triggered.connect(execute)

    return returnedAction

def buildQMenu(icons, title, parent):
    """Build a QMenu and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    pixmapList=[]
    propertyList=[]
    for icon in icons:
        if isinstance(icon[0], QPixmap):
            pixmapListItem=[icon[0]]
            propertyListPath=''
        elif isinstance(icon[0], str):
            pixmapListItem=[QPixmap(icon[0])]
            propertyListPath=icon[0]

        for index in range(1,3):
            if index == 1:
                if len(icon) >= 2:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Normal)
            elif index == 2:
                if len(icon) >= 3:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Off)

        pixmapList.append(tuple(pixmapListItem))

        key = '__bcIcon_'
        if pixmapListItem[1]==QIcon.Normal:
            key+='normal'
        elif pixmapListItem[1]==QIcon.Active:
            key+='active'
        elif pixmapListItem[1]==QIcon.Disabled:
            key+='disabled'
        elif pixmapListItem[1]==QIcon.Selected:
            key+='selected'
        if pixmapListItem[2]==QIcon.Off:
            key+='off'
        else:
            key+='on'

        propertyList.append( (key, propertyListPath) )

    returnedMenu=QMenu(title, parent)
    returnedMenu.setIcon(buildIcon(pixmapList))

    for property in propertyList:
        returnedMenu.setProperty(*property)

    return returnedMenu
