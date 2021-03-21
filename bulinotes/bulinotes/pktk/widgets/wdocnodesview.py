#-----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019 - Grum999
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
from krita import (
                Document,
                Node
            )

from PyQt5.Qt import *
from pktk.modules.utils import checkerBoardBrush
from pktk.modules.ekrita import EKritaNode


class DocNodeUuid:
    """Maintain document tree nodes with unique id


    Working directly with Nodes (from .childNodes) is not possible because each
    call to krita API return a new instance of Node and then, model try to access
    to nodes that doesn't exists anymore outside function on which call has been made,
    and generate crash with segment fault.

    To avoid this, work with a tree of Nodes QUuid()

    """

    def __init__(self, node, parent=None):
        """Initialise layer node"""
        # parent is a DocNodeUuid
        if not parent is None and not isinstance(parent, DocNodeUuid):
            raise EInvalidType("Given `parent` must be a <DocNodeUuid>")
        if not (isinstance(node, Node) or isinstance(node, Document)):
            raise EInvalidType("Given `node` must be a <Node> or a <Document>")

        self.__parent=parent

        if isinstance(node, Document):
            # Initialise node childs
            node=node.rootNode()

        # note: create a new instance of QUuid() otherwise value returned from
        #       node doesn't exist anymore and Krita crash with a segment fault
        self.__uuid=QUuid(node.uniqueId())


        # Initialise node childs
        nbChilds=len(node.childNodes())
        self.__childs=[None] * nbChilds
        nbChilds-=1
        for childNode in node.childNodes():
            self.__childs[nbChilds]=DocNodeUuid(childNode, self)
            nbChilds-=1

    def childs(self):
        """Return list of children"""
        return self.__childs

    def child(self, row):
        """Return child at given position"""
        if row<0 or row>=len(self.__childs):
            return None
        return self.__childs[row]

    def addChild(self, childNode):
        """Add a new child """
        if not isinstance(childNode, DocNodeUuid):
            raise EInvalidType("Given `childNode` must be a <DocNodeUuid>")

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

    def parent(self):
        """Return current parent"""
        return self.__parent


    def uuid(self):
        return self.__uuid


class DocNodesModel(QAbstractItemModel):
    """Model to use with WDocNodesView"""

    COLNUM_VISIBLE = 0
    COLNUM_THUMB = 1
    COLNUM_ICON = 2
    COLNUM_NAME = 3

    COLNUM_LAST = 3

    ROLE_NODE_ID = Qt.UserRole + 1
    ROLE_NODE_THUMB = Qt.UserRole + 2

    ICON_SIZE=24
    THUMB_SIZE=64


    def __init__(self, document, parent=None):
        """Initialise data model

        Given `nodes` can be:
        - A Krita document Node (rootNode)
        - A BCRepairKraFile
        """
        super(DocNodesModel, self).__init__(parent)

        self.__rootItem=None
        self.__document=None

        self.setDocument(document)


    def __repr__(self):
        return f'<DocNodesModel()>'

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column for index"""
        return DocNodesModel.COLNUM_LAST+1

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

        kraDocNodeUuid=index.internalPointer()
        item=self.__document.nodeByUniqueID(kraDocNodeUuid.uuid())

        if item is None:
            return None

        if role == Qt.DecorationRole:
            if index.column()==DocNodesModel.COLNUM_VISIBLE:
                if item.visible():
                    return QIcon.fromTheme("password-show-on")
                else:
                    return QIcon.fromTheme("password-show-off")
            elif index.column()==DocNodesModel.COLNUM_ICON:
                return item.icon()
        elif role==Qt.DisplayRole:
            if index.column()==DocNodesModel.COLNUM_NAME:
                return item.name()
        elif role==DocNodesModel.ROLE_NODE_ID:
            return kraDocNodeUuid.uuid()
        elif role==DocNodesModel.ROLE_NODE_THUMB:
            # returned thumbnail doesn't respect ratio...
            #return QPixmap.fromImage(item.thumbnail(DocNodesModel.THUMB_SIZE, DocNodesModel.THUMB_SIZE))
            pixmap=EKritaNode.toQPixmap(item)
            if pixmap:
                return pixmap.scaled(QSize(DocNodesModel.THUMB_SIZE, DocNodesModel.THUMB_SIZE), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif role == Qt.SizeHintRole and index.column()==DocNodesModel.COLNUM_THUMB:
            return QSize(DocNodesModel.THUMB_SIZE,DocNodesModel.THUMB_SIZE)

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
        return None

    def setDocument(self, document):
        """Add a document to model"""
        self.__document=document
        self.__rootItem=DocNodeUuid(document)
        self.modelReset.emit()


class WDocNodesView(QTreeView):
    """A simple widget to display list of layers in given document"""

    def __init__(self, document, parent=None):
        super(WDocNodesView, self).__init__(parent)

        self.__document=None
        self.__model=None
        self.setDocument(document)
        self.setAutoScroll(False)
        self.setUniformRowHeights(True)
        self.setIconSize(QSize(DocNodesModel.ICON_SIZE,DocNodesModel.ICON_SIZE))

        header = self.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(DocNodesModel.COLNUM_VISIBLE, QHeaderView.Fixed)
        header.setSectionResizeMode(DocNodesModel.COLNUM_THUMB, QHeaderView.Fixed)
        header.setSectionResizeMode(DocNodesModel.COLNUM_ICON, QHeaderView.Fixed)
        header.setSectionResizeMode(DocNodesModel.COLNUM_NAME, QHeaderView.Stretch)

        header.resizeSection(DocNodesModel.COLNUM_THUMB, DocNodesModel.THUMB_SIZE)
        header.resizeSection(DocNodesModel.COLNUM_ICON, DocNodesModel.ICON_SIZE)

        self.setHeaderHidden(True)

        delegate=WDocNodesModelDelegate(self)
        self.setItemDelegateForColumn(DocNodesModel.COLNUM_THUMB, delegate)


    def setDocument(self, document):
        """Set document for nodes treeview"""
        if isinstance(document, Document):
            self.__document=document
            self.__model=DocNodesModel(self.__document)
        else:
            self.__document=None
            self.__model=None
        self.setModel(self.__model)


class WDocNodesModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(WDocNodesModelDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """Paint list item"""
        if index.column() == DocNodesModel.COLNUM_THUMB:
            image=index.data(DocNodesModel.ROLE_NODE_THUMB)

            if image:
                painter.save()
                if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                    painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))

                topLeft=QPoint(option.rect.left()+(option.rect.width() - image.width())//2, option.rect.top()+(option.rect.height() - image.height())//2)

                painter.fillRect(QRect(topLeft, image.size()), checkerBoardBrush())
                painter.drawPixmap(topLeft, image)
                painter.restore()
                return
        QStyledItemDelegate.paint(self, painter, option, index)



class WDocNodesViewDialog(QDialog):
    """A simple dialog bow to display and select nodes"""

    def __init__(self, document, parent=None):
        super(WDocNodesViewDialog, self).__init__(parent)

        self.setSizeGripEnabled(True)
        self.setModal(True)
        self.resize(800, 600)

        self.__tvNodes = WDocNodesView(document, self)
        self.__tvNodes.selectionModel().selectionChanged.connect(self.__selectionChanged)

        dbbxOkCancel = QDialogButtonBox(self)
        dbbxOkCancel.setOrientation(Qt.Horizontal)
        dbbxOkCancel.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dbbxOkCancel.accepted.connect(self.accept)
        dbbxOkCancel.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__tvNodes)
        layout.addWidget(dbbxOkCancel)

        self.__selectedUuid=None

    def __selectionChanged(self, selected, deselected):
        if selected.count()==0:
            self.__selectedUuid=None
        else:
            for index in selected.indexes():
                self.__selectedUuid=QUuid(index.data(DocNodesModel.ROLE_NODE_ID))
                return

    def selectedNodeId(self):
        """Return selected node"""
        return self.__selectedUuid


    @staticmethod
    def show(title, document):
        """Open a dialog box to edit text"""
        dlgBox = WDocNodesViewDialog(document)
        dlgBox.setWindowTitle(title)

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.selectedNodeId()
        else:
            return None
