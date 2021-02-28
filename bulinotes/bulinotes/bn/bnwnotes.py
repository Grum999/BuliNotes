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
import time

from pktk import *

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from .bnnotes import (
                BNNote,
                BNNotes,
                BNNotePostIt
            )

from pktk.modules.utils import tsToStr
from pktk.widgets.wstandardcolorselector import (
        WStandardColorSelector,
        WMenuStandardColorSelector
    )



class BNNotesModel(QAbstractTableModel):
    """A model provided by BNNotes"""
    updateWidth = Signal()

    COLNUM_COLOR = 0
    COLNUM_TITLE = 1
    COLNUM_LOCKED = 2
    COLNUM_PINNED = 3
    COLNUM_LAST = 3

    ROLE_ID = Qt.UserRole + 1
    ROLE_NOTE = Qt.UserRole + 2

    __ICON_WIDTH = 24
    ICON_SIZE = QSize(24, 24)

    HEADERS = ['', 'Title', '', '']

    def __init__(self, notes, parent=None):
        """Initialise list"""
        super(BNNotesModel, self).__init__(parent)
        if not isinstance(notes, BNNotes):
            raise EInvalidType('Given `notes` must be a <BNNotes>')
        self.__notes=notes
        self.__notes.updated.connect(self.__dataUpdated)
        self.__notes.updateReset.connect(self.__dataUpdateReset)
        self.__notes.updateAdded.connect(self.__dataUpdatedAdd)
        self.__notes.updateRemoved.connect(self.__dataUpdateRemove)
        self.__items=self.__notes.idList()
        self.__iconSize=BNNotesModel.ICON_SIZE
        self.__icons=[self.__buildColorIcon(colorIndex) for colorIndex in range(WStandardColorSelector.NB_COLORS)]

    def __repr__(self):
        return f'<BNNotesModel()>'

    def __buildColorIcon(self, colorIndex):
        if colorIndex==WStandardColorSelector.COLOR_NONE:
            return None
        pixmap=QPixmap(BNNotesModel.ICON_SIZE)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.transparent)
        painter.setBrush(QBrush(WStandardColorSelector.getColor(colorIndex).darker(125)))
        painter.drawEllipse(QRect(QPoint(2,2), BNNotesModel.ICON_SIZE - QSize(3,3)))
        painter.end()
        return QIcon(pixmap)

    def __idRow(self, id):
        """Return row number for a given id; return -1 if not found"""
        try:
            return self.__items.index(id)
        except Exception as e:
            return -1

    def __dataUpdateReset(self):
        """Data has entirely been changed (reset/reload)"""
        self.__items=self.__notes.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdatedAdd(self, items):
        # if nb items is the same, just update... ?
        #self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.__notes.length()-1, BNNotesModel.COLNUM_LAST) )
        print('TODO: need to update only for added items')
        self.__items=self.__notes.idList()
        self.modelReset.emit()
        self.updateWidth.emit()

    def __dataUpdateRemove(self, items):
        # if nb items is the same, just update... ?
        #self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.__notes.length()-1, BNNotesModel.COLNUM_LAST) )
        print('TODO: need to update only for removed items')
        self.__items=self.__notes.idList()
        self.modelReset.emit()

    def __dataUpdated(self, item, property):
        index=None
        if property=='colorIndex':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_COLOR)
        elif property=='pinned':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_PINNED)
        elif property=='locked':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_LOCKED)
        elif property=='title':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_TITLE)

        if not index is None:
            self.dataChanged.emit(index, index, [Qt.DecorationRole])
        elif property=='*':
            indexS=self.createIndex(self.__idRow(item.id()), 0)
            indexE=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_LAST)
            self.dataChanged.emit(indexS, indexE, [Qt.DecorationRole])

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column"""
        return BNNotesModel.COLNUM_LAST+1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows"""
        return self.__notes.length()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        column = index.column()
        row=index.row()

        if role == Qt.DecorationRole:
            id=self.__items[row]
            item = self.__notes.get(id)

            if item:
                if column==BNNotesModel.COLNUM_COLOR:
                    id=self.__items[row]
                    item = self.__notes.get(id)
                    return self.__icons[item.colorIndex()]
                elif column==BNNotesModel.COLNUM_PINNED:
                    id=self.__items[row]
                    item = self.__notes.get(id)
                    if item.pinned():
                        return QIcon(':/images/pinned')
                    else:
                        return QIcon(':/images_d/pinned')
                elif column==BNNotesModel.COLNUM_LOCKED:
                    id=self.__items[row]
                    item = self.__notes.get(id)

                    if item.locked():
                        return QIcon(':/images/locked')
                    else:
                        return QIcon(':/images_d/unlocked')
        elif role == Qt.DisplayRole:
            id=self.__items[row]
            item = self.__notes.get(id)
            if item:
                if column==BNNotesModel.COLNUM_TITLE:
                    return item.title()
        elif role == Qt.ToolTipRole:
            id=self.__items[row]
            item = self.__notes.get(id)
            if item:
                tooltip=''
                description=f"<p>{item.description()}</p>"

                if description!='':
                    tooltip=description+"<hr/>"

                tooltip+=f"<p>Created: {tsToStr(item.timestampCreated())}"
                if item.timestampCreated()!=item.timestampUpdated():
                    tooltip+=f"<br>Updated: {tsToStr(item.timestampUpdated())}"
                tooltip+="</p>"


                return tooltip
        elif role == BNNotesModel.ROLE_ID:
            return self.__items[row]
        elif role == BNNotesModel.ROLE_NOTE:
            id=self.__items[row]
            return self.__notes.get(id)
        elif role == Qt.SizeHintRole:
            if column in [BNNotesModel.COLNUM_LOCKED, BNNotesModel.COLNUM_PINNED]:
                return BNNotesModel.__ICON_WIDTH
        return None

    def roleNames(self):
        return {
            BNNotesModel.ROLE_ID: b'id'
        }

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return ''
        return None

    def setIconSize(self, value):
        self.__iconSize=QSize(value, value)

    def notes(self):
        """Expose BNNotes object"""
        return self.__notes


class BNNotesModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(BNNotesModelDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """Paint list item"""
        if index.column() == BNNotesModel.COLNUM_COLOR:
            icon=index.data(Qt.DecorationRole)

            if icon:
                painter.save()
                if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                    painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))

                painter.drawPixmap(option.rect.topLeft(), index.data(Qt.DecorationRole).pixmap(BNNotesModel.ICON_SIZE))
                painter.restore()
                return
        QStyledItemDelegate.paint(self, painter, option, index)



class BNWNotes(QTreeView):
    """Tree view notes"""
    focused = Signal()
    keyPressed = Signal(int)

    __COLNUM_FULLNFO_MINSIZE = 7

    def __init__(self, parent=None):
        super(BNWNotes, self).__init__(parent)
        self.__parent=parent
        self.__model = None
        self.__proxyModel = None
        self.clicked.connect(self.__itemClicked)
        self.setAutoScroll(False)

        self.__contextMenu=QMenu()
        self.__initMenu()

        delegate=BNNotesModelDelegate(self)
        self.setItemDelegateForColumn(BNNotesModel.COLNUM_COLOR, delegate)

    def __itemClicked(self, index):
        """A cell has been clicked, check if it's a persistent column"""
        if index.column()==BNNotesModel.COLNUM_PINNED:
            item=index.data(BNNotesModel.ROLE_NOTE)
            if item:
                if item.pinned():
                    item.closeWindowPostIt()
                else:
                    item.openWindowPostIt()
        elif index.column()==BNNotesModel.COLNUM_LOCKED:
            item=index.data(BNNotesModel.ROLE_NOTE)
            if item:
                item.setLocked(not item.locked())

    def __initMenu(self):
        """Initialise context menu"""
        self.__actionColorIndex = WMenuStandardColorSelector()
        self.__actionColorIndex.colorSelector().colorUpdated.connect(self.__actionSetNoteColorIndex)

        self.__actionCopy = QAction(QIcon(':/images/copy'), i18n('Copy'), self)
        self.__actionCopy.triggered.connect(self.__actionCopyNote)
        self.__actionCut = QAction(QIcon(':/images/cut'), i18n('Cut'), self)
        self.__actionCut.triggered.connect(self.__actionCutNote)
        self.__actionPaste = QAction(QIcon(':/images/paste'), i18n('Paste'), self)
        self.__actionPaste.triggered.connect(self.__actionPasteNote)


        self.__actionAdd = QAction(QIcon(':/images/add_comment'), i18n('Add note'), self)
        self.__actionAdd.triggered.connect(self.__parent.btAddNote.click)
        self.__actionEdit = QAction(QIcon(':/images/edit_comment'), i18n('Edit note'), self)
        self.__actionEdit.triggered.connect(self.__parent.btEditNote.click)
        self.__actionDelete = QAction(QIcon(':/images/delete_comment'), i18n('Delete note'), self)
        self.__actionDelete.triggered.connect(self.__parent.btRemoveNote.click)

        self.__contextMenu.addAction(self.__actionColorIndex)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionCopy)
        self.__contextMenu.addAction(self.__actionCut)
        self.__contextMenu.addAction(self.__actionPaste)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionAdd)
        self.__contextMenu.addAction(self.__actionEdit)
        self.__contextMenu.addAction(self.__actionDelete)

    def __actionSetNoteColorIndex(self, value):
        for note in self.selectedItems():
            note.setColorIndex(value)

    def __actionCopyNote(self):
        """Copy selected notes to clipboardCut

        If nothing is selected, do nothing
        """
        self.__model.notes().clipboardCopy(self.selectedItems())

    def __actionCutNote(self):
        """Cut selected notes to clipboardCut

        If nothing is selected, do nothing
        """
        self.__model.notes().clipboardCut(self.selectedItems())

    def __actionPasteNote(self):
        """Paste notes from clipboard (if any)"""
        self.__model.notes().clipboardPaste()

    def __resizeColumns(self):
        """Resize columns"""
        self.resizeColumnToContents(BNNotesModel.COLNUM_COLOR)
        self.resizeColumnToContents(BNNotesModel.COLNUM_TITLE)
        self.resizeColumnToContents(BNNotesModel.COLNUM_LOCKED)
        self.resizeColumnToContents(BNNotesModel.COLNUM_PINNED)

    def setNotes(self, notes):
        """Initialise treeview header & model"""
        self.__model = BNNotesModel(notes)

        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__model)

        self.setModel(self.__proxyModel)

        # set colums size rules
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(BNNotesModel.COLNUM_COLOR, QHeaderView.Fixed)
        header.setSectionResizeMode(BNNotesModel.COLNUM_TITLE, QHeaderView.Stretch)
        header.setSectionResizeMode(BNNotesModel.COLNUM_LOCKED, QHeaderView.Fixed)
        header.setSectionResizeMode(BNNotesModel.COLNUM_PINNED, QHeaderView.Fixed)

        self.__resizeColumns()

        #delegate=BCClipboardDelegate(self)
        #self.setItemDelegateForColumn(BNNotesModel.COLNUM_SRC, delegate)
        #self.setItemDelegateForColumn(BNNotesModel.COLNUM_FULLNFO, delegate)
        #self.setItemDelegateForColumn(BNNotesModel.COLNUM_PERSISTENT, delegate)

        self.__model.updateWidth.connect(self.__resizeColumns)

    def contextMenuEvent(self, event):
        """Display context menu, updated according to current options"""
        selectedItems=self.selectedItems()
        nbSelectedItems=len(selectedItems)

        if nbSelectedItems>0:
            self.__actionColorIndex.setVisible(True)
            if nbSelectedItems==1:
                self.__actionColorIndex.colorSelector().setColorIndex(selectedItems[0].colorIndex())
            else:
                self.__actionColorIndex.colorSelector().setColorIndex(None)

        self.__actionCopy.setEnabled(nbSelectedItems>0)
        self.__actionCut.setEnabled(nbSelectedItems>0)
        self.__actionPaste.setEnabled(self.__model.notes().clipboardPastable())

        self.__actionAdd.setEnabled(self.__parent.btAddNote.isEnabled())
        self.__actionEdit.setEnabled(self.__parent.btEditNote.isEnabled())
        self.__actionDelete.setEnabled(self.__parent.btRemoveNote.isEnabled())


        self.__contextMenu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        super(BNWNotes, self).keyPressEvent(event)
        self.keyPressed.emit(event.key())

    def focusInEvent(self, event):
        super(BNWNotes, self).focusInEvent(event)
        self.focused.emit()

    def selectedItems(self):
        """Return a list of selected notes items"""
        returned=[]
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(BNNotesModel.COLNUM_TITLE):
                note=item.data(BNNotesModel.ROLE_NOTE)
                if not note is None:
                    returned.append(note)
            returned.sort(key=lambda note: note.position())

        return returned

    def invertSelection(self):
        """Invert current selection"""
        first = self.__proxyModel.index(0, 0)
        last = self.__proxyModel.index(self.__proxyModel.rowCount() - 1, BNNotesModel.COLNUM_LAST)

        self.selectionModel().select(QItemSelection(first, last), QItemSelectionModel.Toggle)
