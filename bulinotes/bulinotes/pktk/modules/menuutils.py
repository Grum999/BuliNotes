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

import re

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

    if isinstance(icons, list) and len(icons)>0:
        propertyList=[]
        actionIcon = QIcon()

        for icon in icons:
            addPixmap=2
            if isinstance(icon[0], QPixmap):
                addPixmap=1
                iconListItem=[icon[0]]
                propertyListPath=''
            elif isinstance(icon[0], str):
                iconListItem=[icon[0], QSize()]
                propertyListPath=icon[0]
            else:
                continue

            for index in range(1,3):
                if index == 1:
                    if len(icon) >= 2:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Normal)
                elif index == 2:
                    if len(icon) >= 3:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Off)

            if addPixmap==1:
                actionIcon.addPixmap(*tuple(iconListItem))
            else:
                actionIcon.addFile(*tuple(iconListItem))


            key = '__bcIcon_'
            if iconListItem[addPixmap]==QIcon.Normal:
                key+='normal'
            elif iconListItem[addPixmap]==QIcon.Active:
                key+='active'
            elif iconListItem[addPixmap]==QIcon.Disabled:
                key+='disabled'
            elif iconListItem[addPixmap]==QIcon.Selected:
                key+='selected'
            if iconListItem[addPixmap+1]==QIcon.Off:
                key+='off'
            else:
                key+='on'

            propertyList.append( (key, propertyListPath) )

        returnedAction=QAction(actionIcon, title, parent)

        for property in propertyList:
            returnedAction.setProperty(*property)

        if callable(action):
            returnedAction.triggered.connect(execute)

        return returnedAction
    elif isinstance(icons, str) and (rfind:=re.match("pktk:(.*)", icons)):
        return buildQAction([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                          (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)], title, parent, action, parameters)
    else:
        raise EInvalidType("Given `icons` must be a <str> or a <list> of <tuples>")

def buildQMenu(icons, title, parent):
    """Build a QMenu and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    if isinstance(icons, list) and len(icons)>0:
        propertyList=[]
        menuIcon = QIcon()

        for icon in icons:
            addPixmap=2
            if isinstance(icon[0], QPixmap):
                addPixmap=1
                iconListItem=[icon[0]]
                propertyListPath=''
            elif isinstance(icon[0], str):
                iconListItem=[icon[0], QSize()]
                propertyListPath=icon[0]
            else:
                continue

            for index in range(1,3):
                if index == 1:
                    if len(icon) >= 2:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Normal)
                elif index == 2:
                    if len(icon) >= 3:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Off)

            if addPixmap==1:
                menuIcon.addPixmap(*tuple(iconListItem))
            else:
                menuIcon.addFile(*tuple(iconListItem))


            key = '__bcIcon_'
            if iconListItem[addPixmap]==QIcon.Normal:
                key+='normal'
            elif iconListItem[addPixmap]==QIcon.Active:
                key+='active'
            elif iconListItem[addPixmap]==QIcon.Disabled:
                key+='disabled'
            elif iconListItem[addPixmap]==QIcon.Selected:
                key+='selected'
            if iconListItem[addPixmap+1]==QIcon.Off:
                key+='off'
            else:
                key+='on'

            propertyList.append( (key, propertyListPath) )

        returnedMenu=QMenu(title, parent)
        returnedMenu.setIcon(menuIcon)

        for property in propertyList:
            returnedMenu.setProperty(*property)

        return returnedMenu

    elif isinstance(icons, str) and (rfind:=re.match("pktk:(.*)", icons)):
        return buildQMenu([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                           (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)], title, parent)
    else:
        raise EInvalidType("Given `icons` must be a <str> or a <list> of <tuples>")
