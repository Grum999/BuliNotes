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
import re

from krita import (
                Document,
                Node
            )

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from pktk.modules.utils import (buildIcon, checkerBoardBrush)
from pktk.modules.ekrita import EKritaNode
from pktk.modules.iconsizes import IconSizes
from pktk.widgets.wstandardcolorselector import WStandardColorSelector


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

    COLNUM_ICON_VISIBLE = 0
    COLNUM_THUMB = 1
    COLNUM_ICON_TYPE = 2
    COLNUM_NAME = 3
    COLNUM_ICON_ANIMATED = 4
    COLNUM_ICON_PINNED = 5
    COLNUM_ICON_LOCK = 6
    COLNUM_ICON_INHERITALPHA = 7
    COLNUM_ICON_ALPHALOCK = 8

    COLNUM_LAST = 8

    ROLE_NODE_ID = Qt.UserRole + 1
    ROLE_NODE_THUMB = Qt.UserRole + 2
    ROLE_NODE_COLORINDEX = Qt.UserRole + 3
    ROLE_NODE_COLLAPSED = Qt.UserRole + 4

    ICON_SIZE=16
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
        self.__cachedThumb={}

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
        if role==DocNodesModel.ROLE_NODE_ID:
            return kraDocNodeUuid.uuid()

        item=self.__document.nodeByUniqueID(kraDocNodeUuid.uuid())
        if item is None:
            return None

        if role == Qt.DecorationRole:
            if index.column()==DocNodesModel.COLNUM_ICON_VISIBLE:
                if item.visible():
                    return QIcon(':/pktk/images/normal/visibility_on')
                else:
                    return QIcon(':/pktk/images/disabled/visibility_off')
            elif index.column()==DocNodesModel.COLNUM_ICON_TYPE:
                return item.icon()
            elif index.column()==DocNodesModel.COLNUM_ICON_PINNED:
                if item.isPinnedToTimeline():
                    return QIcon(':/pktk/images/normal/pinned')
                else:
                    return QIcon(':/pktk/images/disabled/pinned')
            elif index.column()==DocNodesModel.COLNUM_ICON_ANIMATED:
                # ideally:
                #   - no animation: return None
                #   - animated: return Krita.instance().icon('onionOff', QIcon.Disabled)
                #   - animated + onion skin ON: return Krita.instance().icon('onionOn')
                # But currently can't determinate if onion skin is active or not
                if item.animated():
                    return QIcon(':/pktk/images/normal/animation')
                else:
                    return QIcon(':/pktk/images/disabled/animation')
            elif index.column()==DocNodesModel.COLNUM_ICON_LOCK:
                if item.locked():
                    return Krita.instance().icon('layer-locked')
                else:
                    return Krita.instance().icon('layer-unlocked')
            elif index.column()==DocNodesModel.COLNUM_ICON_INHERITALPHA:
                if item.inheritAlpha():
                    return Krita.instance().icon('transparency-disabled')
                else:
                    return Krita.instance().icon('transparency-enabled')
            elif index.column()==DocNodesModel.COLNUM_ICON_ALPHALOCK:
                if item.type()=='grouplayer':
                    if item.passThroughMode():
                        return Krita.instance().icon('passthrough-enabled')
                    else:
                        return Krita.instance().icon('passthrough-disabled')
                elif item.alphaLocked():
                    return Krita.instance().icon('transparency-locked')
                else:
                    return Krita.instance().icon('transparency-unlocked')
        elif role==Qt.DisplayRole:
            if index.column()==DocNodesModel.COLNUM_NAME:
                return item.name()
        elif role==DocNodesModel.ROLE_NODE_THUMB:
            # returned thumbnail doesn't respect ratio...
            #return QPixmap.fromImage(item.thumbnail(DocNodesModel.THUMB_SIZE, DocNodesModel.THUMB_SIZE))
            uid=item.uniqueId()
            if not uid in self.__cachedThumb:
                pixmap=EKritaNode.toQPixmap(item)
                if pixmap:
                    if pixmap.isNull():
                        self.__cachedThumb[uid]=None
                    else:
                        # store in cache a pixmap of 256x256 pixel, should never need higher thumbnail size
                        self.__cachedThumb[uid]=pixmap.scaled(QSize(256,256), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    self.__cachedThumb[uid]=None
            return self.__cachedThumb[uid]
        elif role==DocNodesModel.ROLE_NODE_COLORINDEX:
            return item.colorLabel()
        elif role==DocNodesModel.ROLE_NODE_COLLAPSED:
            return item.collapsed()
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
        self.__cachedThumb={}


class WDocNodesView(QTreeView):
    """A simple widget to display list of layers in given document"""
    thumbSizeIndexChanged = Signal(int, QSize)

    SCROLLTO_FIRST=0
    SCROLLTO_LAST=1

    def __init__(self, parent=None):
        super(WDocNodesView, self).__init__(parent)

        self.__document=None
        self.__model=None

        self.setAutoScroll(False)
        self.setUniformRowHeights(True)
        self.setIconSize(QSize(DocNodesModel.ICON_SIZE,DocNodesModel.ICON_SIZE))

        self.setHeaderHidden(True)
        self.setAllColumnsShowFocus(True)

        self.__delegate=WDocNodesModelDelegate(self)
        self.setItemDelegate(self.__delegate)

        header=self.header()
        header.sectionResized.connect(self.__sectionResized)

        self.__thumbSize = IconSizes([24, 32, 64, 96, 128, 192])
        self.setThumbSizeIndex(2)

    def setDocument(self, document=None):
        """Set document for nodes treeview"""
        if isinstance(document, Document):
            self.__document=document
            self.__model=DocNodesModel(self.__document)

            self.setModel(self.__model)
            header = self.header()
            header.setMinimumSectionSize(DocNodesModel.ICON_SIZE)
            header.setStretchLastSection(False)
            header.setSectionResizeMode(DocNodesModel.COLNUM_THUMB, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_VISIBLE, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_TYPE, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_PINNED, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_ANIMATED, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_LOCK, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_INHERITALPHA, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_ICON_ALPHALOCK, QHeaderView.Fixed)
            header.setSectionResizeMode(DocNodesModel.COLNUM_NAME, QHeaderView.Stretch)

            header.resizeSection(DocNodesModel.COLNUM_THUMB, DocNodesModel.THUMB_SIZE)
            header.resizeSection(DocNodesModel.COLNUM_ICON_TYPE, DocNodesModel.ICON_SIZE+2)
            header.resizeSection(DocNodesModel.COLNUM_ICON_PINNED, DocNodesModel.ICON_SIZE+2)
            header.resizeSection(DocNodesModel.COLNUM_ICON_ANIMATED, DocNodesModel.ICON_SIZE+2)
            header.resizeSection(DocNodesModel.COLNUM_ICON_LOCK, DocNodesModel.ICON_SIZE+2)
            header.resizeSection(DocNodesModel.COLNUM_ICON_INHERITALPHA, DocNodesModel.ICON_SIZE+2)
            header.resizeSection(DocNodesModel.COLNUM_ICON_ALPHALOCK, DocNodesModel.ICON_SIZE+2)
        else:
            self.__document=None
            self.__model=None
            self.setModel(self.__model)

    def selectedItems(self):
        """Return a list of selected linkedLayers items"""
        returned=[]
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(DocNodesModel.COLNUM_NAME):
                layerId=item.data(DocNodesModel.ROLE_NODE_ID)
                if not layerId is None:
                    returned.append(layerId)
        return returned

    def nbSelectedItems(self):
        """Return number of selected items"""
        return len(self.selectedItems())

    def expandTo(self, item):
        """Expand tree to given item"""
        while item != self.rootIndex():
            item=item.parent()
            self.expand(item)

    def applyDocumentExpandCollapse(self):
        """When called, will expand/collapse items to match current document's layer expand/collapse state"""
        def processNode(item):
            nbChild=self.__model.rowCount(item)

            if nbChild>0:
                model=self.model()
                if isinstance(model, QSortFilterProxyModel):
                    index=self.model().mapFromSource(item)
                else:
                    index=item

                # Need to use 'mapFromSource()' due to model() is using a proxy
                self.setExpanded(index, not item.data(DocNodesModel.ROLE_NODE_COLLAPSED))

                for row in range(nbChild):
                    childItem=self.__model.index(row, 0, item)
                    if self.__model.rowCount(childItem)>0:
                        processNode(childItem)

        if self.__model is None:
            return

        processNode(self.rootIndex())

    def selectItems(self, items, scrollTo=None):
        """Select items in treeview, expand and scroll if needed

        Given `items` can be:
        - A <Node> or a <QUuid>
        - A <list> of <Node> or <QUuid>

        If no item is found, current selection is cleared
        """
        def selectItem(itemToSelect, rootIndex):
            found=[]

            if isinstance(itemToSelect, Node):
                itemToSelect=QUuid(itemToSelect.uniqueId())

            if isinstance(itemToSelect, QUuid):
                for rowNumber in range(self.model().rowCount(rootIndex)):
                    childIndex = self.model().index(rowNumber, 0, rootIndex)
                    if itemToSelect==self.model().data(childIndex, DocNodesModel.ROLE_NODE_ID):
                        found.append(childIndex)
                    if self.model().rowCount(childIndex)>0:
                        found+=selectItem(itemToSelect, childIndex)

            return found

        # clear selection before trying to apply selection...
        self.selectionModel().clear()
        found=[]
        if isinstance(items, list) or isinstance(items, tuple):
            for item in items:
                found+=selectItem(item, self.rootIndex())
        else:
            found=selectItem(items, self.rootIndex())

        if len(found)>0:
            scrolled=False
            if scrollTo is None:
                scrollTo=WDocNodesView.SCROLLTO_FIRST

            model=self.model()
            for itemFound in found:
                self.selectionModel().select(itemFound, QItemSelectionModel.SelectCurrent|QItemSelectionModel.Rows)
                self.expandTo(itemFound)
                if scrollTo==WDocNodesView.SCROLLTO_FIRST and not scrolled:
                    scrolled=True
                    self.scrollTo(itemFound, QAbstractItemView.EnsureVisible)

            if scrollTo==WDocNodesView.SCROLLTO_LAST and not scrolled:
                self.scrollTo(found[-1], QAbstractItemView.EnsureVisible)

    def __sectionResized(self, index, oldSize, newSize):
        """When section is resized, update rows height"""
        self.__delegate.setThumbSize(self.__thumbSize.value())

    def wheelEvent(self, event):
        """Manage zoom level through mouse wheel"""
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                # Zoom in
                sizeChanged = self.__thumbSize.next()
            else:
                # zoom out
                sizeChanged = self.__thumbSize.prev()

            if sizeChanged:
                self.setThumbSizeIndex()
        else:
            super(WDocNodesView, self).wheelEvent(event)

    def thumbSizeIndex(self):
        """Return current icon size index"""
        return self.__thumbSize.index()

    def setThumbSizeIndex(self, index=None):
        """Set icon size from index value"""
        if index is None or self.__thumbSize.setIndex(index):
            # new size defined
            header = self.header()
            header.resizeSection(DocNodesModel.COLNUM_THUMB, self.__thumbSize.value())
            self.thumbSizeIndexChanged.emit(self.__thumbSize.index(), self.__thumbSize.value(True))


class WDocNodesViewTBar(QWidget):

    def __init__(self, parent=None):
        super(WDocNodesViewTBar, self).__init__(parent)
        self.__nodesView=None
        self.__filter=''

        self.__layout=QHBoxLayout(self)
        self.__proxyModel=None

        self.__btExpandAll=QToolButton(self)
        self.__btCollapseAll=QToolButton(self)
        self.__leFilter=QLineEdit(self)

        self.__layout.addWidget(self.__btExpandAll)
        self.__layout.addWidget(self.__btCollapseAll)
        self.__layout.addWidget(self.__leFilter)

        self.__buildUi()

    def __buildUi(self):
        """Build toolbat ui"""
        self.__btExpandAll.setAutoRaise(True)
        self.__btCollapseAll.setAutoRaise(True)
        self.__leFilter.setClearButtonEnabled(True)

        self.__btExpandAll.setIcon(buildIcon('pktk:list_tree_expand'))
        self.__btCollapseAll.setIcon(buildIcon('pktk:list_tree_collapse'))

        self.__leFilter.textEdited.connect(self.__setFilter)
        self.__btExpandAll.clicked.connect(self.expandAll)
        self.__btCollapseAll.clicked.connect(self.collapseAll)

        self.__btExpandAll.setToolTip(i18n('Expand all'))
        self.__btCollapseAll.setToolTip(i18n('Collapse all'))
        self.__leFilter.setToolTip(i18n('Filter by layer name\nStart filter with "re:"" or "re/i:"" for regular expression filter'))

        self.__layout.setContentsMargins(0,0,0,0)

        self.__leFilter.findChild(QToolButton).setIcon(QIcon(":/pktk/images/normal/edit_text_clear"))
        self.setLayout(self.__layout)

    def __setFilter(self, filter=''):
        """Set current filter to apply"""
        if filter == self.__filter:
            # filter unchanged, do nothing
            return

        if not isinstance(filter, str):
            raise EInvalidType('Given `filter` must be a <str>')

        self.__filter = filter

        if reFilter:=re.search('^re:(.*)', self.__filter):
            self.__proxyModel.setFilterCaseSensitivity(Qt.CaseSensitive)
            self.__proxyModel.setFilterRegExp(reFilter.groups()[0])
        elif reFilter:=re.search('^re\/i:(.*)', self.__filter):
            self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.__proxyModel.setFilterRegExp(reFilter.groups()[0])
        else:
            self.__proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.__proxyModel.setFilterWildcard(self.__filter)

    def expandAll(self):
        """Expand all nodes"""
        if self.__nodesView:
            self.__nodesView.expandAll()

    def collapseAll(self):
        """Expand all nodes"""
        if self.__nodesView:
            self.__nodesView.collapseAll()

    def setFilter(self, filter=''):
        """Set current filter to apply"""
        if filter == self.__filter:
            # filter unchanged, do nothing
            return

        if not isinstance(filter, str):
            raise EInvalidType('Given `filter` must be a <str>')

        self.__leFilter.setText(filter)
        self.__setFilter(filter)

    def filter(self):
        """Return current applied filter"""
        return self.__filter

    def setNodesView(self, nodesView):
        """Set node view to be linked with tool bar"""
        if nodesView is None:
            if not self.__nodesView is None:
                # unlink

                # restore model
                self.__nodesView.setModel(self.__proxyModel.sourceModel())
                self.__nodesView=None
                self.__proxyModel=None
        elif isinstance(nodesView, WDocNodesView):
            # link
            self.setNodesView(None)
            self.__nodesView=nodesView

            self.__proxyModel = QSortFilterProxyModel(self)
            self.__proxyModel.setSourceModel(self.__nodesView.model())
            self.__proxyModel.setFilterKeyColumn(DocNodesModel.COLNUM_NAME)
            self.__proxyModel.setRecursiveFilteringEnabled(True)

            self.__nodesView.setModel(self.__proxyModel)

    def nodesView(self):
        """Return current linked node view"""
        return self.__nodesView


class WDocNodesModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(WDocNodesModelDelegate, self).__init__(parent)
        self.__thumbSize=QSize(64, 64)

    def setThumbSize(self, value):
        self.__thumbSize=QSize(value, value)
        self.sizeHintChanged.emit(self.parent().model().createIndex(0, DocNodesModel.COLNUM_THUMB))

    def paint(self, painter, option, index):
        """Paint list item"""
        colorIndex=index.data(DocNodesModel.ROLE_NODE_COLORINDEX)
        if colorIndex and colorIndex>0:
            color=WStandardColorSelector.getColor(colorIndex)
            color.setAlphaF(0.20)
            painter.fillRect(option.rect, QBrush(color))

        if index.column() == DocNodesModel.COLNUM_THUMB:
            image=index.data(DocNodesModel.ROLE_NODE_THUMB)

            if image:
                image=image.scaled(option.rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.save()
                if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                    painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))

                topLeft=QPoint(option.rect.left()+(option.rect.width() - image.width())//2, option.rect.top()+(option.rect.height() - image.height())//2)


                painter.fillRect(QRect(topLeft, image.size()), checkerBoardBrush())
                painter.drawPixmap(topLeft, image)
                painter.restore()
                return
        QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        """Calculate size for items"""
        if index.column() == DocNodesModel.COLNUM_THUMB:
            return self.__thumbSize

        return QStyledItemDelegate.sizeHint(self, option, index)


class WDocNodesViewDialog(QDialog):
    """A simple dialog bow to display and select nodes"""

    def __init__(self, document, parent=None):
        super(WDocNodesViewDialog, self).__init__(parent)

        self.setSizeGripEnabled(True)
        self.setModal(True)
        self.resize(800, 600)

        self.__tvNodes = WDocNodesView(self)
        self.__tvNodes.setDocument(document)
        self.__tvNodes.selectionModel().selectionChanged.connect(self.__selectionChanged)

        dbbxOkCancel = QDialogButtonBox(self)
        dbbxOkCancel.setOrientation(Qt.Horizontal)
        dbbxOkCancel.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dbbxOkCancel.accepted.connect(self.accept)
        dbbxOkCancel.rejected.connect(self.reject)

        self.__tbar=WDocNodesViewTBar()
        self.__tbar.setNodesView(self.__tvNodes)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__tbar)
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

    def showEvent(self, event):
        self.__tvNodes.setFocus()

    def applyDocumentExpandCollapse(self):
        """Expand nodes as it's currently defined in document layer stack"""
        self.__tvNodes.applyDocumentExpandCollapse()

    @staticmethod
    def show(title, document, collapseAsDoc=True):
        """Open a dialog box to edit text"""
        dlgBox = WDocNodesViewDialog(document)
        dlgBox.setWindowTitle(title)

        if collapseAsDoc:
            dlgBox.applyDocumentExpandCollapse()

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.selectedNodeId()
        else:
            return None
