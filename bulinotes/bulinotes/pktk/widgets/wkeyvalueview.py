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


class GenericKeyValueNode:
    """A node for GenericKeyValueModel

    Built from a given dictionary data
    """

    KEY = 0
    VALUE = 1

    def __init__(self, data=None, parent=None):
        """Initialise nodes

        Given `data`can be:
        - a GenericKeyValueNode
        - a dict

        Given `parent` can be None (root) or a GenericKeyValueNode

        """
        # parent is a GenericKeyValueNode
        if not parent is None and not isinstance(parent, GenericKeyValueNode):
            raise EInvalidType("Given `parent` must be a <GenericKeyValueNode>")

        self.__parent=parent

        # initialise default values
        self.__data=(None,None)

        # Initialise node childs
        self.__childs=[]

        if isinstance(data, dict):
            for key in data:
                self.__addKeyValue(key, data[key])
        elif isinstance(data, tuple):
            self.__data=data

    def __addKeyValue(self, keyPath, value):
        """Add a key/value pair

        Build tree if needed, or to add as child of path in tree
        """
        if "/" in keyPath:
            # need to build path tree
            path, key=keyPath.rsplit("/", 1)
            directory=self.__childFromPath(path)
            directory.addChild(GenericKeyValueNode((key, value), directory))
        else:
            self.addChild(GenericKeyValueNode((keyPath, value), self))

    def __childFromPath(self, fullPath):
        """Return node from given path

        If path doesn't exist, build it
        """

        # testA/testB/tesC

        if "/" in fullPath:
            path, key=fullPath.split("/", 1)

            foundNode=self.__childFromPath(path)
            if foundNode:
                # exists, continue to search
                return foundNode.__childFromPath(key)
        else:
            for item in self.__childs:
                if item.data(GenericKeyValueNode.KEY)==fullPath:
                    return item

            item=GenericKeyValueNode((fullPath, None), self)
            self.addChild(item)
            return item

        return None

    def childs(self):
        """Return list of children"""
        # need to return a clone?
        return self.__childs

    def child(self, row):
        """Return child at given position"""
        if row<0 or row>=len(self.__childs):
            return None
        return self.__childs[row]

    def addChild(self, childNode):
        """Add a new child """
        if not isinstance(childNode, GenericKeyValueNode):
            raise EInvalidType("Given `childNode` must be a <GenericKeyValueNode>")

        self.__childs.append(childNode)

    def childCount(self):
        """Return number of children the current node have"""
        return len(self.__childs)

    def row(self):
        """Return position is parent's children list"""
        returned=0
        if self.__parent:
            returned=self.__parent.childRow(self)
            if returned<0:
                # need to check if -1 can be used
                returned=0
        return returned

    def childRow(self, node):
        """Return row number for given node

        If node is not found, return -1
        """
        try:
            return self.__childs.index(node)
        except:
            return -1

    def columnCount(self):
        """Return number of column for item"""
        return len(self.__data)

    def data(self, key=None):
        """Return data for node

        Content is managed from model
        """
        if not key is None:
            if key in (GenericKeyValueNode.KEY,GenericKeyValueNode.VALUE):
                return self.__data[key]
            else:
                return None
        else:
            return self.__data

    def parent(self):
        """Return current parent"""
        return self.__parent

    def setData(self, value):
        """Set node data

        Warning: there's not control about data!!
        """
        self.__data=(self.__data[0], value)


class GenericKeyValueModel(QAbstractItemModel):
    """A model to display key/value with tree"""

    COLNUM_KEY =   0
    COLNUM_VALUE = 1

    COLNUM_LAST = 1

    HEADERS = ['Property', 'Value']

    def __init__(self, parent=None):
        """Initialise data model"""
        super(GenericKeyValueModel, self).__init__(parent)

        self.__rootItem=GenericKeyValueNode()

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column for index"""
        return GenericKeyValueModel.COLNUM_LAST+1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows for index"""
        if parent.column()>0:
            return 0

        if not parent.isValid():
            parentItem=self.__rootItem
        else:
            parentItem=parent.internalPointer()

        return parentItem.childCount()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        if not index.isValid():
            return None

        item=index.internalPointer()

        if role==Qt.DisplayRole:
            if index.column()==GenericKeyValueModel.COLNUM_KEY:
                return item.data(GenericKeyValueNode.KEY)
            elif index.column()==GenericKeyValueModel.COLNUM_VALUE:
                return item.data(GenericKeyValueNode.VALUE)

        return None

    def index(self, row, column, parent=None):
        """Provide indexes for views and delegates to use when accessing data

        If an invalid model index is specified as the parent, it is up to the model to return an index that corresponds to a top-level item in the model.
        """
        if not isinstance(parent, QModelIndex) or not self.hasIndex(row, column, parent):
            return QModelIndex()

        child=None
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

        childItem=index.internalPointer()
        childParent=childItem.parent()

        if childParent is None or childParent==self.__rootItem:
            return QModelIndex()

        return self.createIndex(childParent.row(), 0, childParent)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return label for given data section"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return GenericKeyValueModel.HEADERS[section]
        return None

    def setData(self, data):
        """Add data to model

        Data are added as dictionary key/value
        If key contains "/", then a tree is built
            {"a/b/c": 'value'}
            => a
               +- b
                  +- c      value
        """
        if isinstance(data, dict):
            self.__data=data
            self.__rootItem=GenericKeyValueNode(self.__data)
        else:
            self.__rootItem=GenericKeyValueNode()
        self.modelReset.emit()


class WGenericKeyValueView(QTreeView):
    """A treeview to visualize key/values list"""

    def __init__(self, parent=None):
        super(WGenericKeyValueView, self).__init__(parent)

        self.__model=GenericKeyValueModel(self)

        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__model)
        self.__proxyModel.setFilterKeyColumn(GenericKeyValueModel.COLNUM_KEY)

        self.setModel(self.__proxyModel)

        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(GenericKeyValueModel.COLNUM_KEY, QHeaderView.Interactive)
        header.setSectionResizeMode(GenericKeyValueModel.COLNUM_VALUE, QHeaderView.Interactive)

    def setData(self, data, expandAll=True):
        """Set data for treeview

        Data are added as dictionary key/value
        If key contains "/", then a tree is built
            {"a/b/c": 'value'}
            => a
               +- b
                  +- c      value
        """
        self.__model.setData(data)
        if expandAll:
            self.expandAll()
        self.fitContent()

    def fitContent(self):
        """Fit columns to content"""
        for column in range(GenericKeyValueModel.COLNUM_LAST+1):
            self.resizeColumnToContents(column)
