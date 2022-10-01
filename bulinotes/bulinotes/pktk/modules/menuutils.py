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
# The imgutils module provides miscellaneous menu & actions functions
#
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
from ..pktk import *


def buildQAction(icons, title, parent, action=None, parameters=[]):
    """Build a QAction and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    def execute(dummy=None):
        if callable(action):
            action(*parameters)

    if isinstance(icons, list) and len(icons) > 0:
        propertyList = []
        actionIcon = QIcon()

        for icon in icons:
            addPixmap = 2
            if isinstance(icon[0], QPixmap):
                addPixmap = 1
                iconListItem = [icon[0]]
                propertyListPath = ''
            elif isinstance(icon[0], str):
                iconListItem = [icon[0], QSize()]
                propertyListPath = icon[0]
            else:
                continue

            for index in range(1, 3):
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

            if addPixmap == 1:
                actionIcon.addPixmap(*tuple(iconListItem))
            else:
                actionIcon.addFile(*tuple(iconListItem))

            key = '__bcIcon_'
            if iconListItem[addPixmap] == QIcon.Normal:
                key += 'normal'
            elif iconListItem[addPixmap] == QIcon.Active:
                key += 'active'
            elif iconListItem[addPixmap] == QIcon.Disabled:
                key += 'disabled'
            elif iconListItem[addPixmap] == QIcon.Selected:
                key += 'selected'
            if iconListItem[addPixmap+1] == QIcon.Off:
                key += 'off'
            else:
                key += 'on'

            propertyList.append((key, propertyListPath))

        returnedAction = QAction(actionIcon, title, parent)

        for property in propertyList:
            returnedAction.setProperty(*property)

        if callable(action):
            returnedAction.triggered.connect(execute)

        return returnedAction
    elif isinstance(icons, str) and (rfind := re.match("pktk:(.*)", icons)):
        return buildQAction([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                             (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)], title, parent, action, parameters)
    else:
        raise EInvalidType("Given `icons` must be a <str> or a <list> of <tuples>")


def buildQMenu(icons, title, parent):
    """Build a QMenu and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    if isinstance(icons, list) and len(icons) > 0:
        propertyList = []
        menuIcon = QIcon()

        for icon in icons:
            addPixmap = 2
            if isinstance(icon[0], QPixmap):
                addPixmap = 1
                iconListItem = [icon[0]]
                propertyListPath = ''
            elif isinstance(icon[0], str):
                iconListItem = [icon[0], QSize()]
                propertyListPath = icon[0]
            else:
                continue

            for index in range(1, 3):
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

            if addPixmap == 1:
                menuIcon.addPixmap(*tuple(iconListItem))
            else:
                menuIcon.addFile(*tuple(iconListItem))

            key = '__bcIcon_'
            if iconListItem[addPixmap] == QIcon.Normal:
                key += 'normal'
            elif iconListItem[addPixmap] == QIcon.Active:
                key += 'active'
            elif iconListItem[addPixmap] == QIcon.Disabled:
                key += 'disabled'
            elif iconListItem[addPixmap] == QIcon.Selected:
                key += 'selected'
            if iconListItem[addPixmap+1] == QIcon.Off:
                key += 'off'
            else:
                key += 'on'

            propertyList.append((key, propertyListPath))

        returnedMenu = QMenu(title, parent)
        returnedMenu.setIcon(menuIcon)

        for property in propertyList:
            returnedMenu.setProperty(*property)

        return returnedMenu

    elif isinstance(icons, str) and (rfind := re.match("pktk:(.*)", icons)):
        return buildQMenu([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                           (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)], title, parent)
    else:
        raise EInvalidType("Given `icons` must be a <str> or a <list> of <tuples>")


def buildQMenuTree(menuTree, icons, parent):
    """Build a menu with submenu from given `menuTree`

    Call:
        buildQMenuTree('Level1/Level11/Level111', None, qmenuParent)

    Will create submenu from qmenuParent
        qmenuParent
            Level1
                Level11
                    Level111

    Given `icons` can be:
        - None: no icons defined for all built menu
        - <String>: all menu/submenu will have the icon matching string name
        - [<String>]: menu/submenu match in index will have the icon matching string name
                        If number of icons is less than number of submenu, menu for which no index is available will get no icons
                            buildQMenuTree('Level1/Level11/Level111', ['Icon1', 'Icon2'], qmenuParent)
                                qmenuParent
                                    Level1                  'Icon1'
                                        Level11             'Icon2'
                                            Level111        <no icon>


    Returns a list of QMenu
    """

    if not isinstance(parent, QMenu):
        raise EInvalidType('Given `parent` must be a <QMenu>')
    elif not (isinstance(menuTree, str) or isinstance(menuTree, list)):
        raise EInvalidType('Given `menuTree` must be a <str> or <list>')

    returned = []
    if isinstance(menuTree, str):
        menuTreeList = menuTree.split('/')
    else:
        menuTreeList = menuTree

    if len(menuTreeList) == 0:
        return returned

    if icons is None:
        icons = []
    elif isinstance(icons, str):
        icons = [icons]*len(menuTreeList)
    elif not isinstance(icons, list):
        raise EInvalidType('Given `icons` can be <None>, <str> or <list>')

    # start by checking if first menuTreeList item exists as a child from parent
    foundMenu = None
    for item in parent.children():
        if isinstance(item, QMenu) and item.title() == menuTreeList[0]:
            foundMenu = item
            break

    if foundMenu is None:
        # doesn't exist as submenu of parent menu:
        # create a new one
        if len(icons) == 0:
            foundMenu = QMenu(menuTreeList[0], parent)
        else:
            foundMenu = buildQMenu(icons[0], menuTreeList[0], parent)

        parent.addMenu(foundMenu)

    returned.append(foundMenu)
    if len(menuTreeList) > 1:
        menu = buildQMenuTree(menuTreeList[1:], icons[1:], foundMenu)

        if len(menu) > 0:
            returned += menu

    return returned
