#-----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2021 - Grum999
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
# A Krita plugin designed to manage notes
# -----------------------------------------------------------------------------
import re

from pktk import *

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from pktk.modules.utils import (checkerBoardBrush, warningAreaBrush, stripHtml)
from pktk.modules.iconsizes import IconSizes
from pktk.modules.edialog import EDialog
from pktk.widgets.wtextedit import (WTextEdit, WTextEditBtBarOption)
from pktk.widgets.wdocnodesview import DocNodesModel

from .bnlinkedlayer import BNLinkedLayer


class BNLinkedLayersModel(QAbstractTableModel):
    """A model provided for linkedLayers"""
    updateWidth = Signal()

    ROLE_ID = Qt.UserRole + 1
    ROLE_LINKEDLAYER = Qt.UserRole + 2
    ROLE_CSIZE = Qt.UserRole + 3
    ROLE_FOUND = Qt.UserRole + 4

    HEADERS = ['', '', 'Linked layer', 'Comment', '', '', '', '', '', '']
    COLNUM_THUMB = 0
    COLNUM_ICON_TYPE = 1
    COLNUM_NAME = 2
    COLNUM_COMMENT = 3

    COLNUM_ICON_VISIBLE = 4
    COLNUM_ICON_ANIMATED = 5
    COLNUM_ICON_PINNED = 6
    COLNUM_ICON_LOCK = 7
    COLNUM_ICON_INHERITALPHA = 8
    COLNUM_ICON_ALPHALOCK = 9

    COLNUM_LAST = 9

    ICON_SIZE = 16

    def __init__(self, linkedLayers, parent=None):
        """Initialise list"""
        super(BNLinkedLayersModel, self).__init__(parent)
        self.__document=None
        self.__linkedLayers=linkedLayers
        self.__linkedLayers.updated.connect(self.__dataUpdated)
        self.__linkedLayers.updateReset.connect(self.__dataUpdateReset)
        self.__linkedLayers.updateAdded.connect(self.__dataUpdatedAdd)
        self.__linkedLayers.updateRemoved.connect(self.__dataUpdateRemove)
        self.__items=self.__linkedLayers.idList()

    def __repr__(self):
        return f'<BNLinkedLayersModel()>'

    def __idRow(self, id):
        """Return row number for a given id; return -1 if not found"""
        try:
            return self.__items.index(id)
        except Exception as e:
            return -1

    def __dataUpdateReset(self):
        """Data has entirely been changed (reset/reload)"""
        self.__items=self.__linkedLayers.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdatedAdd(self, items):
        # if nb items is the same, just update... ?
        print('TODO: need to update only for added items')
        self.__items=self.__linkedLayers.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdateRemove(self, items):
        # if nb items is the same, just update... ?
        print('TODO: need to update only for removed items')
        self.__items=self.__linkedLayers.idList()
        self.modelReset.emit()

    def __dataUpdated(self, item, property):
        indexS=self.createIndex(self.__idRow(item.id()), 0)
        indexE=self.createIndex(self.__idRow(item.id()), BNLinkedLayersModel.COLNUM_LAST)
        self.dataChanged.emit(indexS, indexE, [Qt.DisplayRole])

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column"""
        return BNLinkedLayersModel.COLNUM_LAST+1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows"""
        return self.__linkedLayers.length()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        column = index.column()
        row=index.row()

        if role == Qt.DecorationRole:
            # can return icons only if document is provided to model
            document=Krita.instance().activeDocument()
            if not document:
                return None

            item=document.nodeByUniqueID(self.__items[row])
            if item is None:
                if index.column()==BNLinkedLayersModel.COLNUM_ICON_TYPE:
                    return QIcon(':/pktk/images/normal/warning')
                else:
                    return None

            if index.column()==BNLinkedLayersModel.COLNUM_ICON_VISIBLE:
                if item.visible():
                    return QIcon(':/pktk/images/normal/visibility_on')
                else:
                    return QIcon(':/pktk/images/disabled/visibility_off')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_TYPE:
                return item.icon()
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_PINNED:
                if item.isPinnedToTimeline():
                    return QIcon(':/pktk/images/normal/pinned')
                else:
                    return QIcon(':/pktk/images/disabled/pinned')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_ANIMATED:
                # ideally:
                #   - no animation: return None
                #   - animated: return Krita.instance().icon('onionOff', QIcon.Disabled)
                #   - animated + onion skin ON: return Krita.instance().icon('onionOn')
                # But currently can't determinate if onion skin is active or not
                if item.animated():
                    return QIcon(':/pktk/images/normal/animation')
                else:
                    return QIcon(':/pktk/images/disabled/animation')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_LOCK:
                if item.locked():
                    return Krita.instance().icon('layer-locked')
                else:
                    return Krita.instance().icon('layer-unlocked')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_INHERITALPHA:
                if item.inheritAlpha():
                    return Krita.instance().icon('transparency-disabled')
                else:
                    return Krita.instance().icon('transparency-enabled')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_ALPHALOCK:
                if item.type()=='grouplayer':
                    if item.passThroughMode():
                        return Krita.instance().icon('passthrough-enabled')
                    else:
                        return Krita.instance().icon('passthrough-disabled')
                elif item.alphaLocked():
                    return Krita.instance().icon('transparency-locked')
                else:
                    return Krita.instance().icon('transparency-unlocked')
        elif role == Qt.ToolTipRole:
            # can return icons only if document is provided to model
            document=Krita.instance().activeDocument()
            if not document:
                return None

            item=document.nodeByUniqueID(self.__items[row])
            if item is None:
                return i18n('Layer not found in document!')

            if index.column()==BNLinkedLayersModel.COLNUM_ICON_VISIBLE:
                if item.visible():
                    return i18n('Layer is visible')
                else:
                    return i18n('Layer is not visible')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_PINNED:
                if item.isPinnedToTimeline():
                    return i18n('Layer is pinned to timeline')
                else:
                    return i18n('Layer is not pinned to timeline')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_ANIMATED:
                # ideally:
                #   - no animation: return None
                #   - animated: return Krita.instance().icon('onionOff', QIcon.Disabled)
                #   - animated + onion skin ON: return Krita.instance().icon('onionOn')
                # But currently can't determinate if onion skin is active or not
                if item.animated():
                    return i18n('Layer is animated')
                else:
                    return i18n('Layer is not animated')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_LOCK:
                if item.locked():
                    return i18n('Layer is locked')
                else:
                    return i18n('Layer is not locked')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_INHERITALPHA:
                if item.inheritAlpha():
                    return i18n('Layer inherit alpha channel')
                else:
                    return i18n('Layer doesn''t inherit alpha channel')
            elif index.column()==BNLinkedLayersModel.COLNUM_ICON_ALPHALOCK:
                if item.type()=='grouplayer':
                    if item.passThroughMode():
                        return i18n('Passthrough mode is enabled')
                    else:
                        return i18n('Passthrough mode is disabled')
                elif item.alphaLocked():
                    return i18n('Alpha channel is locked')
                else:
                    return i18n('Alpha channel is unlocked')
        elif role == Qt.DisplayRole:
            id=self.__items[row]
            item = self.__linkedLayers.get(id)

            if item:
                if column==BNLinkedLayersModel.COLNUM_NAME:
                    return item.name()
                elif column==BNLinkedLayersModel.COLNUM_COMMENT:
                    return item.comments()
        elif role == BNLinkedLayersModel.ROLE_ID:
            return self.__items[row]
        elif role == BNLinkedLayersModel.ROLE_LINKEDLAYER:
            id=self.__items[row]
            return self.__linkedLayers.get(id)
        elif role == BNLinkedLayersModel.ROLE_FOUND:
            document=Krita.instance().activeDocument()
            if not document:
                return False

            item=document.nodeByUniqueID(self.__items[row])
            return (not item is None)


        #elif role == Qt.SizeHintRole:
        #    if column==BNLinkedLayersModel.COLNUM_THUMB:
        #        return
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and section>0:
            return BNLinkedLayersModel.HEADERS[section]
        return None

    def linkedLayers(self):
        """Expose BNLinkedLayers object"""
        return self.__linkedLayers


class BNWLinkedLayers(QTreeView):
    """Tree view linkedLayers (editing mode)"""
    iconSizeIndexChanged = Signal(int, QSize)

    def __init__(self, parent=None):
        super(BNWLinkedLayers, self).__init__(parent)
        self.setAutoScroll(False)
        self.setAlternatingRowColors(True)

        self.__parent=parent
        self.__model = None
        self.__fontSize=self.font().pointSizeF()
        if self.__fontSize==-1:
            self.__fontSize=-self.font().pixelSize()

        self.__isCompact=False
        self.__proxyModel = None

        self.setIconSize(QSize(BNLinkedLayersModel.ICON_SIZE,BNLinkedLayersModel.ICON_SIZE))

        self.__delegate=BNLinkedLayersModelDelegate(self)
        self.setItemDelegate(self.__delegate)

        self.__iconSize = IconSizes([24, 32, 64, 96, 128, 192])
        self.setIconSizeIndex(4)

        self.__contextMenu=QMenu()
        self.__initMenu()


        header=self.header()
        header.sectionResized.connect(self.__sectionResized)
        self.resizeColumns()

    def __initMenu(self):
        """Initialise context menu"""
        pass

    def resizeColumns(self):
        """Resize columns"""
        self.resizeColumnToContents(BNLinkedLayersModel.COLNUM_THUMB)
        self.resizeColumnToContents(BNLinkedLayersModel.COLNUM_NAME)

    def __sectionResized(self, index, oldSize, newSize):
        """When section is resized, update rows height"""
        if index==BNLinkedLayersModel.COLNUM_COMMENT and not self.isColumnHidden(BNLinkedLayersModel.COLNUM_COMMENT):
            # update height only if comment section is resized
            self.__delegate.setCSize(newSize)
            for rowNumber in range(self.__model.rowCount()):
                # need to recalculate height for all rows
                self.__delegate.sizeHintChanged.emit(self.__model.createIndex(rowNumber, index))
        elif index==BNLinkedLayersModel.COLNUM_NAME and self.isColumnHidden(BNLinkedLayersModel.COLNUM_COMMENT):
            self.__delegate.setNSize(newSize)
            for rowNumber in range(self.__model.rowCount()):
                # need to recalculate height for all rows
                self.__delegate.sizeHintChanged.emit(self.__model.createIndex(rowNumber, index))

    def setColumnHidden(self, column, hide):
        """Reimplement column hidden"""
        super(BNWLinkedLayers, self).setColumnHidden(column, hide)
        self.__delegate.setCSize(0)

    def wheelEvent(self, event):
        """Mange zoom level through mouse wheel"""
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                # Zoom in
                sizeChanged = self.__iconSize.next()
            else:
                # zoom out
                sizeChanged = self.__iconSize.prev()

            if sizeChanged:
                self.setIconSizeIndex()
        else:
            super(BNWLinkedLayers, self).wheelEvent(event)

    def iconSizeIndex(self):
        """Return current icon size index"""
        return self.__iconSize.index()

    def setIconSizeIndex(self, index=None):
        """Set icon size from index value"""
        if index is None or self.__iconSize.setIndex(index):
            # new size defined
            self.__delegate.setTSize(self.__iconSize.value())

            header = self.header()
            header.resizeSection(BNLinkedLayersModel.COLNUM_THUMB, self.__iconSize.value())
            self.iconSizeIndexChanged.emit(self.__iconSize.index(), self.__iconSize.value(True))

    def setLinkedLayers(self, linkedLayers):
        """Initialise treeview header & model"""
        self.__model = BNLinkedLayersModel(linkedLayers)

        # needed to allow sorting from header click
        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__model)

        self.setModel(self.__proxyModel)

        # set colums size rules
        header = self.header()
        header.setMinimumSectionSize(BNLinkedLayersModel.ICON_SIZE)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_THUMB, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_TYPE, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_NAME, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_COMMENT, QHeaderView.Stretch)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_VISIBLE, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_ANIMATED, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_PINNED, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_LOCK, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_INHERITALPHA, QHeaderView.Fixed)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_ICON_ALPHALOCK, QHeaderView.Fixed)

        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_TYPE, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_VISIBLE, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_PINNED, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_ANIMATED, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_LOCK, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_INHERITALPHA, BNLinkedLayersModel.ICON_SIZE+2)
        header.resizeSection(BNLinkedLayersModel.COLNUM_ICON_ALPHALOCK, BNLinkedLayersModel.ICON_SIZE+2)

        self.resizeColumns()
        self.__model.updateWidth.connect(self.resizeColumns)

    def selectedItems(self):
        """Return a list of selected linkedLayers items"""
        returned=[]
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(BNLinkedLayersModel.COLNUM_NAME):
                linkedLayer=item.data(BNLinkedLayersModel.ROLE_LINKEDLAYER)
                if not linkedLayer is None:
                    returned.append(linkedLayer)
        return returned

    def nbSelectedItems(self):
        """Return number of selected items"""
        return len(self.selectedItems())

    def isCompact(self):
        """Is compact mode activated"""
        return self.__isCompact

    def setCompact(self, value):
        """Set compact mode"""
        if isinstance(value, bool) and value!=self.__isCompact:
            self.__isCompact=value
            self.__delegate.setCompact(value)
            font=self.font()
            if value:
                if self.__fontSize<0:
                    font.setPixelSize(abs(self.__fontSize)*0.8)
                else:
                    font.setPointSizeF(abs(self.__fontSize)*0.8)
            else:
                if self.__fontSize<0:
                    font.setPixelSize(abs(self.__fontSize))
                else:
                    font.setPointSizeF(abs(self.__fontSize))
            self.setFont(font)
            self.update()


class BNLinkedLayersModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(BNLinkedLayersModelDelegate, self).__init__(parent)
        self.__csize=0
        self.__nsize=0
        self.__tsize=QSize()
        self.__isCompact=False

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __getTextDocument(self, linkedLayer):
        """Return text for information"""
        textDocument=QTextDocument()

        if self.__csize>0:
            textDocument.setHtml(linkedLayer.name())
        else:
            text=linkedLayer.comments()
            if stripHtml(text)=='':
                textDocument.setHtml(linkedLayer.name())
            else:
                textDocument.setHtml(text)
                cursor=QTextCursor(textDocument)
                cursor.insertHtml(f"<span>{linkedLayer.name()}</span><br>")

        if self.__isCompact:
            text=textDocument.toHtml()
            text=re.sub(r"font-size\s*:\s*(\d+)pt;", self.__applyCompactFactor, text)
            textDocument.setHtml(text)

        return textDocument

    def setCSize(self, value):
        """Force size for comments column"""
        self.__csize=value
        self.__nsize=0

    def setNSize(self, value):
        """Force size for comments column"""
        self.__nsize=value
        self.__csize=0

    def setTSize(self, value):
        """Force size for comments column"""
        self.__tsize=QSize(value, value)

    def setCompact(self, value):
        """Set compact mode"""
        if isinstance(value, bool) and value!=self.__isCompact:
            self.__isCompact=value

    def paint(self, painter, option, index):
        """Paint list item"""
        layerFound=index.data(BNLinkedLayersModel.ROLE_FOUND)
        if not layerFound:
            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                option.state&=~QStyle.State_Selected
            painter.fillRect(option.rect, warningAreaBrush())

        if index.column() == BNLinkedLayersModel.COLNUM_NAME:
            # render linkedLayer information
            self.initStyleOption(option, index)

            linkedLayer=index.data(BNLinkedLayersModel.ROLE_LINKEDLAYER)
            rectTxt = QRect(option.rect.left() + 1, option.rect.top(), option.rect.width()-4, option.rect.height()-1)

            painter.save()

            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
                painter.setPen(QPen(option.palette.color(QPalette.HighlightedText)))
            else:
                painter.setPen(QPen(option.palette.color(QPalette.Text)))

            textDocument=self.__getTextDocument(linkedLayer)
            textDocument.setDocumentMargin(1)
            textDocument.setDefaultFont(option.font)
            textDocument.setDefaultStyleSheet("td { white-space: nowrap; }");
            textDocument.setPageSize(QSizeF(rectTxt.size()))

            painter.translate(QPointF(rectTxt.topLeft()))
            textDocument.drawContents(painter, QRectF(QPointF(0,0), QSizeF(rectTxt.size()) ))

            painter.restore()
            return
        elif index.column() == BNLinkedLayersModel.COLNUM_COMMENT:
            # render comment
            self.initStyleOption(option, index)

            linkedLayer=index.data(BNLinkedLayersModel.ROLE_LINKEDLAYER)
            rectTxt = QRect(option.rect.left(), option.rect.top(), option.rect.width(), option.rect.height())

            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setHtml(linkedLayer.comments())
            textDocument.setPageSize(QSizeF(rectTxt.size()))
            textDocument.setDefaultFont(option.font)

            painter.save()

            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
                painter.setPen(QPen(option.palette.color(QPalette.HighlightedText)))
            else:
                painter.setPen(QPen(option.palette.color(QPalette.Text)))

            painter.translate(QPointF(rectTxt.topLeft()))
            textDocument.drawContents(painter, QRectF(QPointF(0,0), QSizeF(rectTxt.size()) ))

            painter.restore()
            return
        elif index.column() == BNLinkedLayersModel.COLNUM_THUMB:
            image=index.data(BNLinkedLayersModel.ROLE_LINKEDLAYER).thumbnail()
            if image is None:
                return

            pixmap=QPixmap.fromImage(image.scaled(QSize(option.rect.width(), option.rect.width()),Qt.KeepAspectRatio, Qt.SmoothTransformation))

            painter.save()
            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))

            #topLeft=QPoint(option.rect.left()+(option.rect.width() - pixmap.width())//2, option.rect.top()+(option.rect.height() - pixmap.height())//2)
            topLeft=QPoint(option.rect.left()+(option.rect.width() - pixmap.width())//2, option.rect.top())

            painter.fillRect(QRect(topLeft, pixmap.size()), checkerBoardBrush())
            painter.drawPixmap(topLeft, pixmap)
            painter.restore()
            return
        else:
            option.decorationAlignment=Qt.AlignLeft|Qt.AlignTop


        QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        """Calculate size for items"""
        size = QStyledItemDelegate.sizeHint(self, option, index)

        if index.column() == BNLinkedLayersModel.COLNUM_THUMB:
            return self.__tsize
        elif index.column() == BNLinkedLayersModel.COLNUM_NAME:
            self.initStyleOption(option, index)

            linkedLayer=index.data(BNLinkedLayersModel.ROLE_LINKEDLAYER)
            textDocument=self.__getTextDocument(linkedLayer)
            textDocument.setDocumentMargin(1)
            textDocument.setDefaultFont(option.font)
            textDocument.setDefaultStyleSheet("td { white-space: nowrap; }");
            textDocument.setPageSize(QSizeF(4096, 1000)) # set 1000px size height arbitrary
            if self.__nsize>0:
                textDocument.setPageSize(QSizeF(self.__nsize, 1000)) # set 1000px size height arbitrary
            else:
                textDocument.setPageSize(QSizeF(textDocument.idealWidth(), 1000)) # set 1000px size height arbitrary
            size=textDocument.size().toSize()+QSize(8, 8)
        elif index.column() == BNLinkedLayersModel.COLNUM_COMMENT:
            # size for comments cell (width is forced, calculate height of rich text)
            linkedLayer=index.data(BNLinkedLayersModel.ROLE_LINKEDLAYER)
            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setDefaultFont(option.font)
            textDocument.setHtml(linkedLayer.comments())
            textDocument.setPageSize(QSizeF(self.__csize, 1000)) # set 1000px size height arbitrary
            size=QSize(self.__csize, textDocument.size().toSize().height())

        return size


class BNLinkedLayerEditor(EDialog):

    @staticmethod
    def edit(linkedLayer=None, title=None):
        """Open a dialog box to edit linked layer"""
        dlgBox = BNLinkedLayerEditor(linkedLayer, title)

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.linkedLayer()
        else:
            return None

    def __init__(self, linkedLayer=None, name="Buli Notes", parent=None):
        super(BNLinkedLayerEditor, self).__init__(os.path.join(os.path.dirname(__file__), 'resources', 'bnlinkedlayereditor.ui'), parent)

        self.__name=name
        self.setWindowTitle(f"{name}::Linked layer")
        self.setSizeGripEnabled(True)

        self.__selectedUuid=None

        if not isinstance(linkedLayer, BNLinkedLayer):
            self.__linkedLayer=BNLinkedLayer()
        else:
            self.__linkedLayer=BNLinkedLayer(linkedLayer)

        self.__document=Krita.instance().activeDocument()

        self.wDescription.setToolbarButtons(WTextEdit.DEFAULT_TOOLBAR|WTextEditBtBarOption.STYLE_STRIKETHROUGH|WTextEditBtBarOption.STYLE_COLOR_BG)
        self.wDescription.setHtml(self.__linkedLayer.comments())
        self.tvDocNodesView.setDocument(self.__document)

        self.wDocNodesViewTBar.setNodesView(self.tvDocNodesView)

        # do expand/collapse after toolbar is initialised (because of proxy model)
        self.tvDocNodesView.applyDocumentExpandCollapse()

        self.pbOk.clicked.connect(self.__accept)
        self.pbCancel.clicked.connect(self.__reject)

    def showEvent(self, event):
        self.tvDocNodesView.selectionModel().selectionChanged.connect(self.__linkedLayerSelectionChanged)
        self.tvDocNodesView.selectItems(self.__linkedLayer.id(), True)

    def __accept(self):
        """Accept modifications and return result"""
        self.__linkedLayer.beginUpdate()
        self.__linkedLayer.fromLayer(self.__selectedUuid)
        self.__linkedLayer.setComments(self.wDescription.toHtml())

        self.__linkedLayer.endUpdate()
        self.accept()

    def __reject(self):
        """reject modifications and return None"""
        self.reject()

    def __updateUi(self):
        """Check if content is valid"""
        self.pbOk.setEnabled(self.tvDocNodesView.nbSelectedItems()==1)

    def __linkedLayerSelectionChanged(self, selected, deselected):
        """Layer selection has been changed"""
        self.__updateUi()
        if selected.count()==0:
            self.__selectedUuid=None
        else:
            for index in selected.indexes():
                self.__selectedUuid=QUuid(index.data(DocNodesModel.ROLE_NODE_ID))
                return

    def linkedLayer(self):
        """Return current linked layer definition"""
        return self.__linkedLayer
