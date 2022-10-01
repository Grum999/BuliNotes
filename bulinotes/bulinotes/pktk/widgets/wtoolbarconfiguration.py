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
# The wtoolbarconfiguration module provides widgets to easily manage configuration
# of toolbar
#
# Main class from this module
#
# - WToolbarConfiguration:
#       Widget
#       The main configuration widget, provide an UI to manage toolbar and their
#       buttons
#
# - ToolbarConfiguration:
#       Easly export/import configuration as dictionaries
#
# -----------------------------------------------------------------------------

import PyQt5.uic

import os
import re
import sys
import hashlib

from krita import InfoObject

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from ..modules.imgutils import (buildIcon, QIconPickable)
from ..modules.utils import (loadXmlUi, replaceLineEditClearButton)
from .wiodialog import (WDialogStrInput, WDialogBooleanInput)
from ..pktk import *


class ToolbarConfiguration(object):
    """A toolbar configuration definition"""

    @staticmethod
    def importToolbar(fromDict, wToolbarConfiguration):
        """From an exported toolbar configuration, create a ToolbarConfiguration"""
        if not isinstance(fromDict, dict):
            raise EInvalidType('Given `fromDict` must be a <dict>')
        elif 'id' not in fromDict:
            raise EInvalidValue('Given `fromDict` must contain "id" key')
        elif 'label' not in fromDict:
            raise EInvalidValue('Given `fromDict` must contain "label" key')
        elif 'actions' not in fromDict:
            raise EInvalidValue('Given `fromDict` must contain "actions" key')
        returned = ToolbarConfiguration(fromDict['id'], fromDict['label'], fromDict['style'])

        for actionId in fromDict['actions']:
            action = wToolbarConfiguration.availableActionFromId(actionId)
            if action:
                returned.addAction(action)

        return returned

    def __init__(self, id, label, style=Qt.ToolButtonFollowStyle):
        """initialise toolbar configuration"""
        if not isinstance(id, str):
            raise EInvalidType("Given `id` must be <str>")
        elif not isinstance(label, str):
            raise EInvalidType("Given `label` must be <str>")

        self.__id = id
        self.__label = label
        self.__style = style
        self.__actions = []

    def id(self):
        """Return current id"""
        return self.__id

    def label(self):
        """Return current label"""
        return self.__label

    def setLabel(self, label):
        """Set current label"""
        if not isinstance(label, str):
            raise EInvalidType("Given `label` must be <str>")
        self.__label = label

    def style(self):
        """Return current label"""
        return self.__style

    def setStyle(self, style):
        """Set current label"""
        if not isinstance(style, int):
            raise EInvalidType("Given `style` must be <int>")
        elif style < 0 or style > 4:
            raise EInvalidValue("Given `style` value is invalid")
        self.__style = style

    def addAction(self, action):
        """Add an action to toolbar configuration"""
        self.__actions.append(AvailableActionNode(action.id(), action.label(), False, action.icon(), action.isSeparator()))

    def removeAction(self, index):
        """Remove an action from toolbar configuration

        Action is removed from given `index`
        """
        if index > -1 and index < len(self.__actions):
            self.__actions.pop(index)

    def actionIndex(self, action):
        """Return index for first occurence of action in toolbar

        If no occurence is found, return -1
        """
        for index in range(len(self.__actions)):
            if self.__actions[index] == action:
                return index
        return -1

    def actions(self):
        """Return actions"""
        return self.__actions

    def action(self, index):
        """Return action for given `index`"""
        return self.__actions[index]

    def clear(self):
        """Clear all actions"""
        self.__actions = []

    def export(self):
        """Export toolbar configuration as a dictionary that can be converted into a JSON

        For action, only action Id is exported
        """
        return {
                'id': self.__id,
                'label': self.__label,
                'actions': [action.id() for action in self.__actions],
                'style': self.__style
            }


class AvailableActionNode:
    """A node for ActionNode

    Built from a given dictionary data
    """

    def __init__(self, id, label, isGroup=False, icon=None, isSeparator=False):
        """Initialise nodes

        Given `id` is <str> and define unique Id

        Given `label` is <str> and define display value in tree

        Given `isGroup` is <bool>
            If True, given `id` is a group identifier
            If False, given `id` is an action identifier

        Given `icon` is <QIcon>
            If None:
                If item is a group, default group icon is applied,
            Otherwise given icon is applied

        Given `parent` is an AvailableActionNode (defined as a group)
        Otherwise raise an error
            If parent is None, item is added to root
        """
        # parent is a GenericKeyValueNode
        if not isinstance(id, str):
            raise EInvalidType("Given `id` must be a <str>")
        elif not isinstance(label, str):
            raise EInvalidType("Given `label` must be a <str>")
        elif not isinstance(isGroup, bool):
            raise EInvalidType("Given `isGroup` must be a <bool>")
        elif not (icon is None or isinstance(icon, QIcon)):
            raise EInvalidType("Given `icon` must be a <QIcon> or None")

        self.__parent = None

        # initialise default values
        self.__id = id
        self.__label = label
        self.__isGroup = isGroup
        self.__icon = None

        self.__isAvailable = True
        self.__isSeparator = isSeparator

        self.__hash = hash((self.__id, self.__isGroup))

        if icon is None:
            self.__icon = QIconPickable(buildIcon("pktk:folder_open"))
        else:
            self.__icon = QIconPickable(icon)

        # Initialise node childs
        self.__childs = []

    def __eq__(self, other):
        """Return if other AvailableActionNode is the same than current one"""
        if isinstance(other, AvailableActionNode):
            return (self.__hash == other.__hash)
        return False

    def __hash__(self):
        """Return hash for AvailableActionNode"""
        return self.__hash

    def childs(self):
        """Return list of children"""
        return self.__childs

    def child(self, row):
        """Return child at given position"""
        if row < 0 or row >= len(self.__childs):
            return None
        return self.__childs[row]

    def addChild(self, value):
        """Add a child

        If current node is not a group, raise an error

        Given `value` must be an AvailableActionNode, otherwise raise an error

        If `value` is already a child of current group, does nothing and return False
        """
        if not self.__isGroup:
            raise EInvalidStatus("Current AvailableActionNode is not a group")
        elif not isinstance(value, AvailableActionNode):
            raise EInvalidType("Given `value` must be a <AvailableActionNode>")

        if value not in self.__childs:
            value.setParent(self)
            self.__childs.append(value)
            return True
        return False

    def removeChild(self, value):
        """Remove a child

        If current node is not a group, raise an error

        Given `value` must be an AvailableActionNode, otherwise raise an error

        If `value` is not a child of current group, does nothing and return False
        """
        if not self.__isGroup:
            raise EInvalidStatus("Current AvailableActionNode is not a group")
        elif not isinstance(value, AvailableActionNode):
            raise EInvalidType("Given `value` must be a <AvailableActionNode>")

        if value in self.__childs:
            self.__childs.pop(value)
            return True
        return False

    def childCount(self):
        """Return number of children the current node have"""
        return len(self.__childs)

    def row(self):
        """Return position is parent's children list"""
        returned = 0
        if self.__parent:
            returned = self.__parent.childRow(self)
            if returned < 0:
                # need to check if -1 can be used
                returned = 0
        return returned

    def childRow(self, node):
        """Return row number for given node

        If node is not found, return -1
        """
        try:
            return self.__childs.index(node)
        except Exception:
            return -1

    def columnCount(self):
        """Return number of column for item"""
        return 1

    def id(self):
        """Return current id"""
        return self.__id

    def label(self):
        """Return current label"""
        return self.__label

    def isGroup(self):
        """Return if current item is a group or not"""
        return self.__isGroup

    def icon(self):
        """Return current icon"""
        return self.__icon

    def parent(self):
        """Return current parent"""
        return self.__parent

    def setParent(self, parent):
        """Set current parent"""
        if parent is not None:
            if not isinstance(parent, AvailableActionNode):
                raise EInvalidType("Given `parent` must be a <AvailableActionNode>")
            elif not parent.isGroup():
                raise EInvalidType("Given `parent` must be a <AvailableActionNode> defined as a group")
        self.__parent = parent

    def isAvailable(self):
        """Return if action is available or not"""
        return self.__isAvailable

    def setAvailable(self, value):
        """Set if action is available or not"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be <bool>")
        elif not (self.__isGroup or self.__isSeparator):
            self.__isAvailable = value

    def isSeparator(self):
        """Return if action is a separator"""
        return self.__isSeparator


class AvailableActionModel(QAbstractItemModel):
    """A model to manage available actions list

    Available actions can be attached to root or within groups
    """
    COLNUM_LABEL = 0
    COLNUM_LAST = 0

    ROLE_NODE = Qt.UserRole + 1

    def __init__(self, rootNode, parent=None):
        """Initialise data model"""
        super(AvailableActionModel, self).__init__(parent)

        self.__rootItem = rootNode

    def __repr__(self):
        return f'<AvailableActionModel()>'

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column for index"""
        return AvailableActionModel.COLNUM_LAST+1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows for index"""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.__rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DecorationRole:
            return item.icon()
        elif role == Qt.DisplayRole:
            return item.label()
        elif role == AvailableActionModel.ROLE_NODE:
            return item

        return None

    def index(self, row, column, parent=None):
        """Provide indexes for views and delegates to use when accessing data

        If an invalid model index is specified as the parent, it is up to the model to return an index that corresponds to a top-level item in the model.
        """
        if not isinstance(parent, QModelIndex) or not self.hasIndex(row, column, parent):
            return QModelIndex()

        child = None
        if not parent.isValid():
            parentNode = self.__rootItem
        else:
            parentNode = parent.internalPointer()

        child = parentNode.child(row)

        if child:
            return self.createIndex(row, column, child)
        else:
            return QModelIndex()

    def parent(self, index):
        """return parent (QModelIndex) for given index"""
        if not index or not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        childParent = childItem.parent()

        if childParent is None or childParent == self.__rootItem:
            return QModelIndex()

        return self.createIndex(childParent.row(), 0, childParent)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return label for given data section"""
        return None

    def reset(self):
        """Reset model"""
        self.modelReset.emit()

    def getAvailableActionIndex(self, availableAction):
        """Return index for given `availableAction`"""
        def recursiveSearch(availableAction, parent):
            for row in range(self.rowCount(parent)):
                rowIndex = self.index(row, 0, parent)
                data = self.data(rowIndex, AvailableActionModel.ROLE_NODE)

                if data == availableAction:
                    return rowIndex
                elif data.isGroup():
                    rowIndex = recursiveSearch(availableAction, rowIndex)
                    if rowIndex is not None:
                        return rowIndex

            return None

        return recursiveSearch(availableAction, QModelIndex())

    def availableActionUpdated(self, availableAction):
        """Given `node` has been updated"""
        index = self.getAvailableActionIndex(availableAction)
        if index is not None:
            self.dataChanged.emit(index, index)


class AvailableActionTvDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to return properly row height"""

    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(AvailableActionTvDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """Paint list item"""
        self.initStyleOption(option, index)
        painter.save()

        availableAction = index.data(AvailableActionModel.ROLE_NODE)

        color = None
        isSelected = False

        if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
            colorText = option.palette.color(QPalette.HighlightedText)
            isSelected = True
            if self.parent().hasFocus():
                color = option.palette.color(QPalette.Active, QPalette.Highlight)
            else:
                color = option.palette.color(QPalette.Inactive, QPalette.Highlight)

            painter.setBrush(QBrush(color))
        else:
            colorText = option.palette.color(QPalette.Text)
            if (option.features & QStyleOptionViewItem.Alternate):
                color = option.palette.color(QPalette.AlternateBase)
            else:
                color = option.palette.color(QPalette.Base)

        # draw background
        painter.fillRect(option.rect, color)

        painter.setRenderHint(QPainter.Antialiasing)

        # draw icon
        if not availableAction.icon() is None:
            iconMode = QIcon.Normal

            if (option.state & QStyle.State_Enabled) != QStyle.State_Enabled:
                iconMode = QIcon.Disabled

            painter.drawPixmap(option.rect.topLeft(), availableAction.icon().pixmap(option.rect.height(), mode=iconMode))

        # draw text
        x = option.rect.left() + option.rect.height() + 5
        painter.drawText(x, option.rect.top(), option.rect.width() - x, option.rect.height(), Qt.AlignLeft, availableAction.label())

        if not availableAction.isAvailable():
            # selected item
            color.setAlphaF(0.5)
            painter.fillRect(option.rect, color)
        painter.restore()


class WToolbarConfiguration(QWidget):
    """A widget to manage toolbar configuration"""

    def __init__(self, parent=None):
        super(WToolbarConfiguration, self).__init__(parent)

        uiFileName = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wtoolbarconfiguration.ui')

        loadXmlUi(uiFileName, self)

        self.__toolbars = {}
        self.__currentToolbar = None

        # -- toolbars --
        self.cbToolbarList.currentIndexChanged.connect(self.__toolbarSelected)

        self.tbToolbarAdd.clicked.connect(self.__addToolbar)
        self.tbToolbarEdit.clicked.connect(self.__editToolbar)
        self.tbToolbarDelete.clicked.connect(self.__deleteToolbar)

        self.cbToolbarStyle.addItem(i18n("Icon only"), Qt.ToolButtonIconOnly)
        self.cbToolbarStyle.addItem(i18n("Text only"), Qt.ToolButtonTextOnly)
        self.cbToolbarStyle.addItem(i18n("Text beside icon"), Qt.ToolButtonTextBesideIcon)
        self.cbToolbarStyle.addItem(i18n("Text under icon"), Qt.ToolButtonTextUnderIcon)
        self.cbToolbarStyle.addItem(i18n("System"), Qt.ToolButtonFollowStyle)
        self.cbToolbarStyle.setCurrentIndex(Qt.ToolButtonFollowStyle)
        self.cbToolbarStyle.currentIndexChanged.connect(self.__toolbarStyleChanged)

        # -- available actions --
        self.__availableActionsInUpdate = False

        # root node
        self.__availableActions = AvailableActionNode(hashlib.sha1(b'rootNode').hexdigest(), '', True)
        self.__modelAvailableActions = AvailableActionModel(self.__availableActions)
        self.__proxyModelAvailableActions = QSortFilterProxyModel(self)
        self.__proxyModelAvailableActions.setSourceModel(self.__modelAvailableActions)
        self.__proxyModelAvailableActions.setFilterKeyColumn(AvailableActionModel.COLNUM_LABEL)
        self.__proxyModelAvailableActions.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModelAvailableActions.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModelAvailableActions.setRecursiveFilteringEnabled(True)

        self.__tvAvailableActionsDelegate = AvailableActionTvDelegate(self.tvAvailableActions)
        self.tvAvailableActions.setItemDelegate(self.__tvAvailableActionsDelegate)
        self.tvAvailableActions.setAutoScroll(False)
        self.tvAvailableActions.setUniformRowHeights(True)
        self.tvAvailableActions.setHeaderHidden(True)
        self.tvAvailableActions.setAllColumnsShowFocus(True)
        self.tvAvailableActions.setModel(self.__proxyModelAvailableActions)
        self.tvAvailableActions.setSortingEnabled(True)
        self.tvAvailableActions.sortByColumn(AvailableActionModel.COLNUM_LABEL, Qt.AscendingOrder)
        self.tvAvailableActions.selectionModel().selectionChanged.connect(self.__availableActionsSelectionChanged)
        self.tvAvailableActions.setDragDropMode(QAbstractItemView.InternalMove)
        self.tvAvailableActions.doubleClicked.connect(self.__availableActionsToCurrent)
        # self.tvAvailableActions.setIconSize(self.lvCurrentActions.iconSize())

        self.tbAvailableActionsExpandAll.clicked.connect(self.availableActionsExpandAll)
        self.tbAvailableActionsCollapseAll.clicked.connect(self.availableActionsCollapseAll)

        self.leAvailableActionsFilter.textChanged.connect(self.__availableActionsFilterChanged)
        replaceLineEditClearButton(self.leAvailableActionsFilter)

        # -- current --
        self.__modelCurrentActions = QStandardItemModel()
        self.lvCurrentActions.setModel(self.__modelCurrentActions)
        self.lvCurrentActions.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lvCurrentActions.setDragDropMode(QAbstractItemView.InternalMove)
        self.lvCurrentActions.setUniformItemSizes(True)
        self.lvCurrentActions.selectionModel().selectionChanged.connect(self.__currentActionsSelectionChanged)
        self.lvCurrentActions.doubleClicked.connect(self.__currentActionsToAvailable)

        # -- general --
        self.tbAvailableActionsToCurrent.clicked.connect(self.__availableActionsToCurrent)
        self.tbCurrentActionsToAvailable.clicked.connect(self.__currentActionsToAvailable)
        self.__updateToolbarUi()
        self.__availableActionsSelectionChanged()
        self.__currentActionsSelectionChanged()

    def __addToolbar(self):
        """Add toolbar from UI"""
        newToolbar = WDialogStrInput.display(i18n("Toolbar management"), i18n("Add a new toolbar"), i18n("Toolbar label"), "", "", 1)
        if newToolbar is None:
            return

        # toolbar Id is a uuid
        self.addToolbar(QUuid.createUuid().toString(), newToolbar)

    def __editToolbar(self):
        """Rename toolbar from UI"""
        # get current label
        currentToolbarId = self.cbToolbarList.currentData()
        currentLabel = self.getToolbar(currentToolbarId).label()

        newLabel = WDialogStrInput.display(i18n("Toolbar management"), i18n("Rename toolbar"), i18n("Toolbar label"), currentLabel)
        if newLabel is None:
            return

        # toolbar Id is a uuid
        self.renameToolbar(currentToolbarId, newLabel)

    def __deleteToolbar(self):
        """Delete toolbar from UI"""
        # get current label
        currentToolbarId = self.cbToolbarList.currentData()
        currentLabel = self.getToolbar(currentToolbarId).label()

        deleteLabel = WDialogBooleanInput.display(i18n("Toolbar management"), i18n(f"Delete toolbar <i>{currentLabel}</i>?"), False)
        if deleteLabel is True:
            # toolbar Id is a uuid
            self.removeToolbar(currentToolbarId)

    def __toolbarStyleChanged(self):
        """Change style for toolbar"""
        if self.cbToolbarList.currentIndex() > -1:
            self.setToolbarStyle(self.cbToolbarList.currentData(), self.cbToolbarStyle.currentIndex())

    def __updateToolbarUi(self):
        """Update add/edit/delete buttons status according to current state"""
        self.cbToolbarList.model().sort(0)

        enabled = len(self.__toolbars) > 0
        self.tbToolbarEdit.setEnabled(enabled)
        self.tbToolbarDelete.setEnabled(enabled)
        self.wActions.setEnabled(enabled)

    def __updateAvailableActionsView(self):
        """Update available actions tree view (after an update)"""
        if self.__availableActionsInUpdate is False:
            self.__modelAvailableActions.reset()

    def __updateCurrentActionsView(self):
        """Update available actions tree view (after an update)"""
        if self.__currentToolbar is not None:
            self.__toolbars[self.__currentToolbar].clear()

            for index in range(self.__modelCurrentActions.rowCount()):
                item = self.__modelCurrentActions.item(index)
                self.__toolbars[self.__currentToolbar].addAction(item.data())

                availableActionIndex = self.__modelAvailableActions.getAvailableActionIndex(item.data())
                availableAction = self.__modelAvailableActions.data(availableActionIndex, AvailableActionModel.ROLE_NODE)

                availableAction.setAvailable(True)
                self.__modelAvailableActions.availableActionUpdated(availableAction)

            self.__modelCurrentActions.clear()

        if self.cbToolbarList.currentIndex() == -1:
            self.cbToolbarStyle.setCurrentIndex(Qt.ToolButtonFollowStyle)
            self.__currentToolbar = None
        else:
            self.__currentToolbar = self.cbToolbarList.currentData()

        if self.__currentToolbar is not None:
            self.cbToolbarStyle.setCurrentIndex(self.__toolbars[self.__currentToolbar].style())

            for action in self.__toolbars[self.__currentToolbar].actions():
                availableActionIndex = self.__modelAvailableActions.getAvailableActionIndex(action)
                availableAction = self.__modelAvailableActions.data(availableActionIndex, AvailableActionModel.ROLE_NODE)
                self.__addAvailableActionsToCurrent(availableAction)

    def __availableActionsFilterChanged(self, text):
        """Filter value for available actions has been modified, update filter"""
        self.__proxyModelAvailableActions.setFilterFixedString(text)

    def __availableActionsSelectionChanged(self, selected=None, deselected=None):
        """Selection for available actions has been modified"""
        nbSelectedValid = 0
        for selectedIndex in self.tvAvailableActions.selectionModel().selectedRows():
            node = selectedIndex.data(AvailableActionModel.ROLE_NODE)
            if node.isAvailable() and not node.isGroup():
                nbSelectedValid += 1

        self.tbAvailableActionsToCurrent.setEnabled(nbSelectedValid > 0)

    def __currentActionsSelectionChanged(self, selected=None, deselected=None):
        """Selection for current actions has been modified"""
        haveSelection = len(self.lvCurrentActions.selectionModel().selectedRows()) > 0
        self.tbCurrentActionsToAvailable.setEnabled(haveSelection)

    def __addAvailableActionsToCurrent(self, availableAction):
        """Add given `availableAction` to current toolbar"""
        if availableAction.isAvailable() and not availableAction.isGroup():
            # move to current
            availableAction.setAvailable(False)
            self.__modelAvailableActions.availableActionUpdated(availableAction)

            item = QStandardItem(availableAction.icon(), availableAction.label())
            item.setData(availableAction)
            item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)
            self.__modelCurrentActions.appendRow(item)

    def __removeCurrentAction(self, currentAction):
        """Add given `availableAction` to current toolbar"""
        availableActionIndex = self.__modelAvailableActions.getAvailableActionIndex(currentAction)
        availableAction = self.__modelAvailableActions.data(availableActionIndex, AvailableActionModel.ROLE_NODE)

        availableAction.setAvailable(True)
        self.__modelAvailableActions.availableActionUpdated(availableAction)

        for index in range(self.__modelCurrentActions.rowCount()):
            item = self.__modelCurrentActions.item(index)
            if item.data() == currentAction:
                self.__modelCurrentActions.removeRow(index)
                break

    def __availableActionsToCurrent(self):
        """Add selected available actions to current toolbar"""
        for selectedIndex in self.tvAvailableActions.selectionModel().selectedRows():
            self.__addAvailableActionsToCurrent(selectedIndex.data(AvailableActionModel.ROLE_NODE))

    def __currentActionsToAvailable(self):
        """Remove selected current actions from current toolbar"""
        for currentAction in [self.__modelCurrentActions.itemFromIndex(selectedIndex).data() for selectedIndex in self.lvCurrentActions.selectionModel().selectedRows()]:
            self.__removeCurrentAction(currentAction)

    @pyqtSlot('int')
    def __toolbarSelected(self, index):
        """A toolbar has been selected"""
        self.__updateCurrentActionsView()
        self.lvCurrentActions.setEnabled(index > -1)

    def __updateToolbar(self, toolbar, actions):
        """Update toolbar with given actions"""
        pass

    def getToolbars(self):
        """Return list of toolbar id"""
        return list(self.__toolbars.keys())

    def addToolbar(self, toolbarId, label):
        """Add a toolbar

        Given `toolbarId` is a <str> and must be unique (if already exist, does nothing and return None)
        Given `label` is a <str>

        Return a ToolbarConfiguration object
        """
        if not isinstance(toolbarId, str):
            raise EInvalidType("Given `toolbarId` must be <str>")
        elif not isinstance(label, str):
            raise EInvalidType("Given `label` must be <str>")

        if toolbarId in self.__toolbars:
            return False

        self.__toolbars[toolbarId] = ToolbarConfiguration(toolbarId, label)
        self.cbToolbarList.addItem(label, toolbarId)
        self.cbToolbarList.setCurrentIndex(self.cbToolbarList.count()-1)
        self.__updateToolbarUi()
        return self.__toolbars[toolbarId]

    def removeToolbar(self, toolbarId):
        """Remove a toolbar designed by given `toolbarId`

        If no toolbar is found, does nothing and return False
        """
        if not isinstance(toolbarId, str):
            raise EInvalidType("Given `toolbarId` must be <str>")

        if toolbarId not in self.__toolbars:
            return False

        for index in range(self.cbToolbarList.count()):
            if self.cbToolbarList.itemData(index) == toolbarId:
                self.cbToolbarList.removeItem(index)
                break

        self.__toolbars.pop(toolbarId)

        self.__updateToolbarUi()
        return True

    def renameToolbar(self, toolbarId, label):
        """Rename toolbar designed by given `toolbarId` with given `label`

        If no toolbar is found, does nothing and return False
        """
        if not isinstance(toolbarId, str):
            raise EInvalidType("Given `toolbarId` must be <str>")

        if toolbarId not in self.__toolbars:
            return False

        self.__toolbars[toolbarId].setLabel(label)
        for index in range(self.cbToolbarList.count()):
            if self.cbToolbarList.itemData(index) == toolbarId:
                self.cbToolbarList.setItemText(index, label)
                self.__updateToolbarUi()
                break
        return True

    def setToolbarStyle(self, toolbarId, style):
        """Change toolbar style designed by given `toolbarId` with given `style`

        If no toolbar is found, does nothing and return False
        """
        if not isinstance(toolbarId, str):
            raise EInvalidType("Given `toolbarId` must be <str>")

        if toolbarId not in self.__toolbars:
            return False

        self.__toolbars[toolbarId].setStyle(style)
        return True

    def getToolbar(self, toolbarId):
        """Return a toolbar definition for given `toolbarId`

        If no toolbar is found, raise an exception
        """
        if toolbarId not in self.__toolbars:
            raise EInvalidValue("Given `toolbarId` doesn't exist")

        return self.__toolbars[toolbarId]

    def beginAvailableActionUpdate(self):
        """Start mass update of available actions"""
        self.__availableActionsInUpdate = True

    def endAvailableActionUpdate(self):
        """Stop mass update of available actions"""
        self.__availableActionsInUpdate = False
        self.__updateAvailableActionsView()

    def addAvailableAction(self, action, groupId=None):
        """Add an action in available actions

        Given `action` is a <QAction>
        If `action` already exists (if already exist, does nothing and return False)

        If given, `groupId` is a <str>
        If `groupId` doesn't exist, action is added to root
        """
        if not isinstance(action, QAction):
            raise EInvalidType("Given `action` must be <QAction>")
        elif not (isinstance(groupId, str) or groupId is None):
            raise EInvalidType("Given `groupId` when provided must be <str>")

        data = action.data()
        if not isinstance(data, str):
            data = ''
        else:
            data = f"{data} "

        availableAction = AvailableActionNode(action.objectName(), data+re.sub(r'\&(?!\&)', '', action.text()), False, action.icon())

        if groupId is None:
            if self.__availableActions.addChild(availableAction):
                self.__updateAvailableActionsView()
                return True
        else:
            row = self.__availableActions.childRow(AvailableActionNode(groupId, '', True))
            if row > -1:
                parentGroup = self.__availableActions.child(row)
                if parentGroup.addChild(availableAction):
                    self.__updateAvailableActionsView()
                    return True
        return False

    def availableActionFromId(self, actionId):
        """Return available action from given Id

        If not found return None
        """
        def recursiveSearch(item, actionId):
            if item.isGroup():
                for child in item.childs():
                    found = recursiveSearch(child, actionId)
                    if found:
                        return found
            elif item.id() == actionId:
                return item

            return None

        for item in self.__availableActions.childs():
            found = recursiveSearch(item, actionId)
            if found:
                return found

        return None

    def removeAvailableAction(self, action):
        """Remove an action from available actions

        If no `toolbarId` is found, raise an exception

        Given `action` is a <QAction>

        If not found, does nothing and return False
        """
        if not isinstance(action, QAction):
            raise EInvalidType("Given `action` must be <QAction>")

        availableAction = AvailableActionNode(hashlib.sha1(action.encode()).hexdigest(), action, False)

        if groupId is None:
            if self.__availableActions.removeChild(availableAction):
                self.__updateAvailableActionsView()
                return True
        else:
            row = self.__availableActions.childRow(AvailableActionNode(groupId, '', True))
            if row > -1:
                parentGroup = self.__availableActions.child(row)
                if parentGroup.removeChild(availableAction):
                    self.__updateAvailableActionsView()
                    return True
        return False

    def addAvailableActionSeparator(self):
        """Add a separator in available actions

        A separator is always available
        """
        self.__availableActions.addChild(AvailableActionNode(hashlib.sha1(b"--menuSeparator--").hexdigest(),
                                                             i18n("--- Separator ---"),
                                                             False,
                                                             buildIcon('pktk:separator_vertical'),
                                                             True))

    def addAvailableActionGroup(self, groupId, label):
        """Add a group for available action

        If groupId already exists, does nothing and return False
        """
        if not isinstance(groupId, str):
            raise EInvalidType("Given `groupId` must be <str>")

        if self.__availableActions.addChild(AvailableActionNode(groupId, label, True)):
            self.__updateAvailableActionsView()
            return True
        return False

    def removeAvailableActionGroup(self, groupId):
        """Remove a group

        All available action for group are removed too

        If not found, does nothing and return False"""
        if not isinstance(groupId, str):
            raise EInvalidType("Given `groupId` must be <str>")

        if self.__availableActions.removeChild(AvailableActionNode(groupId, '', True)):
            self.__updateAvailableActionsView()
            return True
        return False

    def availableActionsExpandAll(self):
        """Expand available actions groups"""
        self.tvAvailableActions.expandAll()

    def availableActionsCollapseAll(self):
        """Collapse available actions groups"""
        self.tvAvailableActions.collapseAll()

    def initialiseAvailableActionsFromMenubar(self, menubar):
        """Initialise available action list from given menubar"""
        def recursiveMenuActions(menu, groupId):
            if len(menu.actions()) > 0:
                for action in menu.actions():
                    if not action.isSeparator():
                        if action.menu():
                            if len(action.menu().actions()) > 0:
                                recursiveMenuActions(action.menu(), groupId)
                        elif action.objectName() != '':
                            self.addAvailableAction(action, groupId)

        if not isinstance(menubar, QMenuBar):
            raise EInvalidType("Given `menubar` must be a <QMenuBar>")
        for menu in menubar.children():
            if isinstance(menu, QMenu):
                if len(menu.actions()) > 0:
                    self.addAvailableActionGroup(menu.objectName(), re.sub(r'\&(?!\&)', '', menu.title()))
                    recursiveMenuActions(menu, menu.objectName())

    def toolbarsExport(self):
        """Export toolbars configuration"""
        self.__updateCurrentActionsView()
        returned = []
        for toolbarId in self.__toolbars:
            returned.append(self.__toolbars[toolbarId].export())
        return returned

    def toolbarsImport(self, configuration):
        """Import toolbars configuration"""
        if not isinstance(configuration, list):
            raise EInvalidType("Given `configuration` must be <list>")

        for config in configuration:
            toolbar = ToolbarConfiguration.importToolbar(config, self)
            self.__toolbars[toolbar.id()] = toolbar
            self.cbToolbarList.addItem(toolbar.label(), toolbar.id())

        if len(self.__toolbars) > 0:
            self.cbToolbarList.setCurrentIndex(0)
        self.__updateToolbarUi()
