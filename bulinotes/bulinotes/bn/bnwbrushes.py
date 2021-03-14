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

from pktk.modules.iconsizes import IconSizes

from .bnbrush import BNBrush


class BNBrushesModel(QAbstractTableModel):
    """A model provided for brushes"""
    updateWidth = Signal()

    ROLE_ID = Qt.UserRole + 1
    ROLE_BRUSH = Qt.UserRole + 2
    ROLE_CSIZE = Qt.UserRole + 3

    HEADERS = ['Icon', 'Brush', 'Description']
    COLNUM_ICON = 0
    COLNUM_BRUSH = 1
    COLNUM_COMMENT = 2
    COLNUM_LAST = 2

    def __init__(self, note, parent=None):
        """Initialise list"""
        super(BNBrushesModel, self).__init__(parent)
        self.__note=note
        self.__brushes=self.__note.brushes()
        self.__brushes.updated.connect(self.__dataUpdated)
        self.__brushes.updateReset.connect(self.__dataUpdateReset)
        self.__brushes.updateAdded.connect(self.__dataUpdatedAdd)
        self.__brushes.updateRemoved.connect(self.__dataUpdateRemove)
        self.__items=self.__brushes.idList()

    def __repr__(self):
        return f'<BNBrushesModel()>'

    def __idRow(self, id):
        """Return row number for a given id; return -1 if not found"""
        try:
            return self.__items.index(id)
        except Exception as e:
            return -1

    def __dataUpdateReset(self):
        """Data has entirely been changed (reset/reload)"""
        self.__items=self.__brushes.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdatedAdd(self, items):
        # if nb items is the same, just update... ?
        #self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.__note.length()-1, BNBrushesModel.COLNUM_LAST) )
        print('TODO: need to update only for added items')
        self.__items=self.__brushes.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdateRemove(self, items):
        # if nb items is the same, just update... ?
        #self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.__note.length()-1, BNBrushesModel.COLNUM_LAST) )
        print('TODO: need to update only for removed items')
        self.__items=self.__brushes.idList()
        self.modelReset.emit()

    def __dataUpdated(self, item, property):
        indexS=self.createIndex(self.__idRow(item.id()), 0)
        indexE=self.createIndex(self.__idRow(item.id()), BNBrushesModel.COLNUM_LAST)
        self.dataChanged.emit(indexS, indexE, [Qt.DisplayRole])

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column"""
        return BNBrushesModel.COLNUM_LAST+1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows"""
        return self.__brushes.length()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        column = index.column()
        row=index.row()

        if role == Qt.DecorationRole:
            id=self.__items[row]
            item = self.__brushes.get(id)

            if item:
                if column==BNBrushesModel.COLNUM_ICON:
                    # QIcon
                    return QIcon(QPixmap.fromImage(item.image()))
        elif role == Qt.DisplayRole:
            id=self.__items[row]
            item = self.__brushes.get(id)

            if item:
                if column==BNBrushesModel.COLNUM_BRUSH:
                    return item.name()
                elif column==BNBrushesModel.COLNUM_COMMENT:
                    return item.comments()
        elif role == BNBrushesModel.ROLE_ID:
            return self.__items[row]
        elif role == BNBrushesModel.ROLE_BRUSH:
            id=self.__items[row]
            return self.__brushes.get(id)
        #elif role == Qt.SizeHintRole:
        #    if column==BNBrushesModel.COLNUM_ICON:
        #        return
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and section>0:
            return BNBrushesModel.HEADERS[section]
        return None


    def note(self):
        """Expose BNNotes object"""
        return self.__note


class BNWBrushes(QTreeView):
    """Tree view brushes (editing mode)"""
    focused = Signal()
    keyPressed = Signal(int)
    iconSizeIndexChanged = Signal(int, QSize)

    __COLNUM_FULLNFO_MINSIZE = 7

    def __init__(self, parent=None):
        super(BNWBrushes, self).__init__(parent)
        self.setAutoScroll(False)

        self.__parent=parent
        self.__model = None
        self.__proxyModel = None
        self.__fontSize=self.font().pointSizeF()
        if self.__fontSize==-1:
            self.__fontSize=-self.font().pixelSize()

        self.__isCompact=False

        self.__iconSize = IconSizes([32, 64, 96, 128, 192])
        self.setIconSizeIndex(3)

        self.__contextMenu=QMenu()
        self.__initMenu()

        self.__delegate=BNBrushesModelDelegate(self)
        self.setItemDelegate(self.__delegate)

        header=self.header()
        header.sectionResized.connect(self.__sectionResized)

    def __initMenu(self):
        """Initialise context menu"""
        pass

    def __resizeColumns(self):
        """Resize columns"""
        self.resizeColumnToContents(BNBrushesModel.COLNUM_ICON)
        self.resizeColumnToContents(BNBrushesModel.COLNUM_BRUSH)

    def __sectionResized(self, index, oldSize, newSize):
        """When section is resized, update rows height"""
        if index==BNBrushesModel.COLNUM_COMMENT and not self.isColumnHidden(BNBrushesModel.COLNUM_COMMENT):
            # update height only if comment section is resized
            self.__delegate.setCSize(newSize)
            for rowNumber in range(self.__model.rowCount()):
                # need to recalculate height for all rows
                self.__delegate.sizeHintChanged.emit(self.__model.createIndex(rowNumber, index))

    def setColumnHidden(self, column, hide):
        """Reimplement column hidden"""
        super(BNWBrushes, self).setColumnHidden(column, hide)
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
            super(BNWBrushes, self).wheelEvent(event)

    def iconSizeIndex(self):
        """Return current icon size index"""
        return self.__iconSize.index()

    def setIconSizeIndex(self, index=None):
        """Set icon size from index value"""
        if index is None or self.__iconSize.setIndex(index):
            # new size defined
            self.setIconSize(self.__iconSize.value(True))

            header = self.header()
            header.resizeSection(BNBrushesModel.COLNUM_ICON, self.__iconSize.value())
            self.iconSizeIndexChanged.emit(self.__iconSize.index(), self.__iconSize.value(True))

    def setNote(self, note):
        """Initialise treeview header & model"""
        self.__model = BNBrushesModel(note)

        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__model)

        self.setModel(self.__proxyModel)

        # set colums size rules
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(BNBrushesModel.COLNUM_ICON, QHeaderView.Fixed)
        header.setSectionResizeMode(BNBrushesModel.COLNUM_BRUSH, QHeaderView.Fixed)
        header.setSectionResizeMode(BNBrushesModel.COLNUM_COMMENT, QHeaderView.Stretch)

        self.__resizeColumns()

        self.__model.updateWidth.connect(self.__resizeColumns)

    def selectedItems(self):
        """Return a list of selected brushes items"""
        returned=[]
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(BNBrushesModel.COLNUM_BRUSH):
                brush=item.data(BNBrushesModel.ROLE_BRUSH)
                if not brush is None:
                    returned.append(brush)
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


class BNBrushesModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(BNBrushesModelDelegate, self).__init__(parent)
        self.__csize=0
        self.__isCompact=False

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __getTextInformation(self, brush):
        """Return text for information"""
        if self.__csize>0:
            return brush.information()
        else:
            text=brush.comments()
            if text=='':
                text=brush.information(False)

            if self.__isCompact:
                text=re.sub(r"font-size\s*:\s*(\d+)pt;", self.__applyCompactFactor, text)

            return text

    def setCSize(self, value):
        """Force size for comments column"""
        self.__csize=value

    def setCompact(self, value):
        """Set compact mode"""
        if isinstance(value, bool) and value!=self.__isCompact:
            self.__isCompact=value

    def paint(self, painter, option, index):
        """Paint list item"""
        if index.column() == BNBrushesModel.COLNUM_BRUSH:
            # render brush information
            self.initStyleOption(option, index)

            brush=index.data(BNBrushesModel.ROLE_BRUSH)
            rectTxt = QRect(option.rect.left() + 1, option.rect.top()+4, option.rect.width()-4, option.rect.height()-1)

            painter.save()

            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
                painter.setPen(QPen(option.palette.color(QPalette.HighlightedText)))
            else:
                painter.setPen(QPen(option.palette.color(QPalette.Text)))

            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setHtml(self.__getTextInformation(brush))
            textDocument.setPageSize(QSizeF(rectTxt.size()))
            textDocument.setDefaultFont(option.font)

            painter.translate(QPointF(rectTxt.topLeft()))
            textDocument.drawContents(painter, QRectF(QPointF(0,0), QSizeF(rectTxt.size()) ))

            #painter.drawText(rectTxt, Qt.AlignLeft|Qt.AlignTop, brush.name())

            painter.restore()
            return
        elif index.column() == BNBrushesModel.COLNUM_COMMENT:
            # render comment
            self.initStyleOption(option, index)

            brush=index.data(BNBrushesModel.ROLE_BRUSH)
            rectTxt = QRect(option.rect.left(), option.rect.top(), option.rect.width(), option.rect.height())

            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setHtml(brush.comments())
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
        elif index.column() == BNBrushesModel.COLNUM_ICON:
            # render icon in top-left position of cell
            painter.save()
            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))

            painter.drawPixmap(option.rect.topLeft(), index.data(Qt.DecorationRole).pixmap(option.decorationSize))
            painter.restore()
            return

        QStyledItemDelegate.paint(self, painter, option, index)


    def sizeHint(self, option, index):
        """Calculate size for items"""
        size = QStyledItemDelegate.sizeHint(self, option, index)

        if index.column() == BNBrushesModel.COLNUM_ICON:
            return option.decorationSize
        elif index.column() == BNBrushesModel.COLNUM_BRUSH:
            brush=index.data(BNBrushesModel.ROLE_BRUSH)
            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setDefaultFont(option.font)
            textDocument.setHtml(self.__getTextInformation(brush))
            textDocument.setPageSize(QSizeF(4096, 1000)) # set 1000px size height arbitrary
            textDocument.setPageSize(QSizeF(textDocument.idealWidth(), 1000)) # set 1000px size height arbitrary
            size=textDocument.size().toSize()+QSize(8, 8)
        elif index.column() == BNBrushesModel.COLNUM_COMMENT:
            # size for comments cell (width is forced, calculate height of rich text)
            brush=index.data(BNBrushesModel.ROLE_BRUSH)
            textDocument=QTextDocument()
            textDocument.setDocumentMargin(1)
            textDocument.setDefaultFont(option.font)
            textDocument.setHtml(brush.comments())
            textDocument.setPageSize(QSizeF(self.__csize, 1000)) # set 1000px size height arbitrary
            size=QSize(self.__csize, textDocument.size().toSize().height())

        return size
