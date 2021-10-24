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

from bulinotes.pktk import *

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal,
        QTimer
    )

from .bnnotes import (
                BNNote,
                BNNotes
            )

from bulinotes.pktk.modules.timeutils import tsToStr
from bulinotes.pktk.widgets.wstandardcolorselector import (
        WStandardColorSelector,
        WMenuStandardColorSelector
    )



class BNNotesModel(QAbstractTableModel):
    """A model provided by BNNotes"""
    COLNUM_COLOR = 0
    COLNUM_TITLE = 1
    COLNUM_FONTS = 2
    COLNUM_LOCKED = 3
    COLNUM_VIEW = 4
    COLNUM_PINNED = 5
    COLNUM_LAST = 5

    ROLE_ID = Qt.UserRole + 1
    ROLE_NOTE = Qt.UserRole + 2

    ICON_WIDTH = 24
    ICON_SIZE = QSize(24, 24)

    HEADERS = ['', 'Title', '', '', '', '']

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
        self.__notes.updateMoved.connect(self.__dataUpdateMove)
        self.__items=self.__notes.idList(True)
        self.__iconSize=BNNotesModel.ICON_SIZE
        self.__icons=[self.__buildColorIcon(colorIndex) for colorIndex in range(WStandardColorSelector.NB_COLORS)]
        self.__isFreezed=False


    def __unfreeze(self):
        self.__isFreezed=False

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
        self.modelAboutToBeReset.emit()
        self.__items=self.__notes.idList(True)
        self.modelReset.emit()

    def __dataUpdateMove(self):
        """Item order has been modified"""
        self.modelAboutToBeReset.emit()
        self.__items=self.__notes.idList(True)
        self.modelReset.emit()

    def __dataUpdatedAdd(self, items):
        self.modelAboutToBeReset.emit()
        self.__items=self.__notes.idList(True)
        self.modelReset.emit()

    def __dataUpdateRemove(self, items):
        self.modelAboutToBeReset.emit()
        self.__items=self.__notes.idList(True)
        self.modelReset.emit()

    def __dataUpdated(self, item, property):
        index=None
        if property=='colorIndex':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_COLOR)
        elif property=='opened':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_VIEW)
        elif property=='closed':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_VIEW)
            # --- this is tricky thing...
            # when a postit lost focuse, it's closed automatically
            # but if in QTreeView user click on VIEW icon to hide postit:
            #  1) Post-it lost focus and is closed
            #  2) When click is taken in account, note is already close and then
            #     it's considered that post-it have to be opened...
            # Timer will set a "freeze" status
            # And in QTreeView, if trying to process VIEW icon, if model is currently in "freeze" then do nothing
            self.__isFreezed=True
            QTimer.singleShot(125, self.__unfreeze)
        elif property=='pinned':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_PINNED)
        elif property=='locked':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_LOCKED)
        elif property=='title':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_TITLE)
        elif property=='fonts':
            index=self.createIndex(self.__idRow(item.id()), BNNotesModel.COLNUM_FONTS)

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
                elif column==BNNotesModel.COLNUM_VIEW:
                    id=self.__items[row]
                    item = self.__notes.get(id)
                    if item.windowPostIt():
                        return QIcon(':/pktk/images/normal/note_view')
                    else:
                        return QIcon(':/pktk/images/disabled/note_view')
                elif column==BNNotesModel.COLNUM_PINNED:
                    id=self.__items[row]
                    item = self.__notes.get(id)
                    if item.pinned():
                        return QIcon(':/pktk/images/normal/pinned')
                    else:
                        return QIcon(':/pktk/images/disabled/pinned')
                elif column==BNNotesModel.COLNUM_LOCKED:
                    id=self.__items[row]
                    item = self.__notes.get(id)

                    if item.locked():
                        return QIcon(':/pktk/images/normal/lock_locked')
                    else:
                        return QIcon(':/pktk/images/disabled/lock_unlocked')
                elif column==BNNotesModel.COLNUM_FONTS:
                    id=self.__items[row]
                    item = self.__notes.get(id)

                    if item.hasEmbeddedFonts():
                        return QIcon(':/pktk/images/normal/text_f')
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
                toolTip=[]

                itemDescription=item.description()
                if itemDescription!='':
                    toolTip.append(f"<p>{itemDescription}</p>")

                if item.hasEmbeddedFonts():
                    text=i18n(f"Embedded fonts: {item.embeddedFonts().length()}")
                    toolTip.append(f"<p>{text}</p>")

                if len(toolTip)>0:
                    toolTip.append('<hr>')

                toolTip.append("<p>")
                toolTip.append(i18n(f"Created: {tsToStr(item.timestampCreated())}"))
                if item.timestampCreated()!=item.timestampUpdated():
                    toolTip.append("<br>")
                    toolTip.append(i18n(f"Updated: {tsToStr(item.timestampUpdated())}"))
                toolTip.append("</p>")
                return "".join(toolTip)
        elif role == BNNotesModel.ROLE_ID:
            return self.__items[row]
        elif role == BNNotesModel.ROLE_NOTE:
            id=self.__items[row]
            return self.__notes.get(id)
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

    def isFreezed(self):
        """Return True if freezed"""
        return self.__isFreezed


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

        self.__selectedItems=[]

    def __itemClicked(self, index):
        """A cell has been clicked, check if it's a persistent column"""
        if index.column()==BNNotesModel.COLNUM_VIEW:
            item=index.data(BNNotesModel.ROLE_NOTE)
            if item:
                if item.windowPostIt():
                    item.closeWindowPostIt()
                elif not self.__model.isFreezed():
                    item.openWindowPostIt(True)
        elif index.column()==BNNotesModel.COLNUM_PINNED:
            item=index.data(BNNotesModel.ROLE_NOTE)
            if item:
                item.setPinned(not item.pinned())
                if item.pinned():
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


        self.__actionView = QAction(QIcon(':/images/noteView'), i18n('View note'), self)
        self.__actionView.triggered.connect(self.__viewNotes)
        self.__actionAdd = QAction(QIcon(':/images/noteAdd'), i18n('Add note'), self)
        self.__actionAdd.triggered.connect(self.__parent.btAddNote.click)
        self.__actionEdit = QAction(QIcon(':/images/noteEdit'), i18n('Edit note'), self)
        self.__actionEdit.triggered.connect(self.__parent.btEditNote.click)
        self.__actionDelete = QAction(QIcon(':/images/noteDelete'), i18n('Delete note'), self)
        self.__actionDelete.triggered.connect(self.__parent.btRemoveNote.click)

        self.__contextMenu.addAction(self.__actionColorIndex)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionCopy)
        self.__contextMenu.addAction(self.__actionCut)
        self.__contextMenu.addAction(self.__actionPaste)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionView)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionAdd)
        self.__contextMenu.addAction(self.__actionEdit)
        self.__contextMenu.addAction(self.__actionDelete)

    def __actionSetNoteColorIndex(self, value):
        """Set color index for selected notes"""
        for note in self.selectedItems():
            note.setColorIndex(value)

    def __viewNotes(self):
        """View all selected notes"""
        notes=self.selectedItems()
        for note in notes:
            note.openWindowPostIt(len(notes)==1)

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

    def __beforeReset(self):
        """Model is about to be reseted, keep selection"""
        self.__selectedItems=[item.id() for item in self.selectedItems()]

    def __afterReset(self):
        """Model has been reseted, restore selection"""
        if len(self.__selectedItems)==0:
            return

        index=self.rootIndex()
        nbChild=self.__model.rowCount(index)

        if nbChild>0:
            model=self.model()
            if isinstance(model, QSortFilterProxyModel):
                # Need to use 'mapFromSource()' due to model() is using a proxy
                index=self.model().mapFromSource(index)
            else:
                index=index

            newSelection=QItemSelection()
            for row in range(nbChild):
                item=self.__model.index(row, 0, index)
                id=item.data(BNNotesModel.ROLE_ID)
                if id in self.__selectedItems:
                    newSelection.merge(QItemSelection(item, item), QItemSelectionModel.SelectCurrent|QItemSelectionModel.Rows)
            self.selectionModel().select(newSelection, QItemSelectionModel.SelectCurrent|QItemSelectionModel.Rows)

        self.__selectedItems=[]

    def setNotes(self, notes):
        """Initialise treeview header & model"""
        self.__model = BNNotesModel(notes)

        self.__proxyModel = QSortFilterProxyModel(self)
        self.__proxyModel.setSourceModel(self.__model)

        self.setModel(self.__proxyModel)

        self.__model.modelAboutToBeReset.connect(self.__beforeReset)
        self.__model.modelReset.connect(self.__afterReset)

        # set colums size rules
        header = self.header()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(BNNotesModel.ICON_WIDTH)
        header.setSectionResizeMode(BNNotesModel.COLNUM_COLOR, QHeaderView.Fixed)
        header.setSectionResizeMode(BNNotesModel.COLNUM_TITLE, QHeaderView.Stretch)
        header.setSectionResizeMode(BNNotesModel.COLNUM_LOCKED, QHeaderView.Fixed)
        header.setSectionResizeMode(BNNotesModel.COLNUM_VIEW, QHeaderView.Fixed)
        header.setSectionResizeMode(BNNotesModel.COLNUM_PINNED, QHeaderView.Fixed)

        header.resizeSection(BNNotesModel.COLNUM_FONTS, BNNotesModel.ICON_WIDTH+2)
        header.resizeSection(BNNotesModel.COLNUM_COLOR, BNNotesModel.ICON_WIDTH+2)
        header.resizeSection(BNNotesModel.COLNUM_LOCKED, BNNotesModel.ICON_WIDTH+2)
        header.resizeSection(BNNotesModel.COLNUM_VIEW, BNNotesModel.ICON_WIDTH+2)
        header.resizeSection(BNNotesModel.COLNUM_PINNED, BNNotesModel.ICON_WIDTH+2)

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

        self.__actionView.setEnabled(nbSelectedItems>0)
        self.__actionAdd.setEnabled(self.__parent.btAddNote.isEnabled())
        self.__actionEdit.setEnabled(self.__parent.btEditNote.isEnabled())
        self.__actionDelete.setEnabled(self.__parent.btRemoveNote.isEnabled())

        self.__contextMenu.exec_(event.globalPos())

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
