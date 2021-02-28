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
import struct
import re



from pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from pktk.modules.utils import (
                        secToStrTime,
                        tsToStr,
                        BCTimer
                    )
from pktk.modules.edialog import EDialog
from pktk.modules.bytesrw import BytesRW
from pktk.widgets.wstandardcolorselector import WStandardColorSelector


class BNNote(QObject):
    """A note"""
    updated=Signal(QObject, str)


    def __init__(self, id=None, title=None, description=None):
        super(BNNote, self).__init__(None)
        self.__id=None
        self.__title=None
        self.__description=None
        self.__colorIndex=WStandardColorSelector.COLOR_NONE
        self.__pinned=False
        self.__locked=False
        self.__text=''
        self.__timestampCreated=time.time()
        self.__timestampUpdated=time.time()
        self.__position=0

        self.__windowPostItGeometry=None
        self.__windowPostItCompact=False

        self.__emitUpdated=False

        # if a BNNotePostIt is opened, keep window reference
        self.__windowPostIt=None

        self.__setId(id)
        self.setTitle(title)
        self.setDescription(description)

        self.__emitUpdated=True

    def __repr__(self):
        return f'<BNNote({self.__id}, {self.__title}, {self.__pinned}, {self.__locked}, {self.__windowPostItCompact})>'

    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated:
            self.updated.emit(self, property)

    def __setId(self, id):
        """Set id for note"""
        if id is None:
            self.__id=QUuid.createUuid().toString()
        else:
            self.__id=id

    def id(self):
        """Return note id"""
        return self.__id

    def title(self):
        """Return note title"""
        return self.__title

    def setTitle(self, title):
        """Set note title"""
        if title is None or isinstance(title, str):
            self.__title=title
            self.__timestampUpdated=time.time()
            self.__updated('title')

    def description(self):
        """Return note description"""
        return self.__description

    def setDescription(self, description):
        """Set note description"""
        if not self.__locked and (description is None or isinstance(description, str)):
            self.__description=description
            self.__timestampUpdated=time.time()
            self.__updated('description')

    def colorIndex(self):
        """Return note color index"""
        return self.__colorIndex

    def setColorIndex(self, colorIndex):
        """Set note title"""
        if isinstance(colorIndex, int) and colorIndex >= WStandardColorSelector.COLOR_NONE and  colorIndex <= WStandardColorSelector.COLOR_GRAY:
            self.__colorIndex=colorIndex
            self.__updated('colorIndex')

    def pinned(self):
        """Return note pin status"""
        return self.__pinned

    def setPinned(self, pinned):
        """Set note pin status (boolean value)"""
        if isinstance(pinned, bool):
            self.__pinned=pinned
            self.__updated('pinned')

    def locked(self):
        """Return note lock status"""
        return self.__locked

    def setLocked(self, locked):
        """Set note lock status (boolean value)"""
        if isinstance(locked, bool):
            self.__locked=locked
            self.__updated('locked')

    def text(self):
        """Return note lock status"""
        return self.__text

    def setText(self, text):
        """Set note text"""
        if not self.__locked and isinstance(text, str):
            self.__text=text
            self.__timestampUpdated=time.time()
            self.__updated('text')

    def timestampUpdated(self):
        """Return note timestamp"""
        return self.__timestampUpdated

    def setTimestampUpdated(self, timestamp):
        """Set note timestamp"""
        if not self.__locked and isinstance(timestamp, float):
            self.__timestampUpdated=timestamp
            self.__updated('timestamp')

    def timestampCreated(self):
        """Return note timestamp"""
        return self.__timestampCreated

    def setTimestampCreated(self, timestamp):
        """Set note timestamp"""
        if not self.__locked and isinstance(timestamp, float):
            self.__timestampCreated=timestamp
            self.__updated('timestamp')

    def position(self):
        """Return note position in list"""
        return self.__position

    def setPosition(self, position):
        """Set note position"""
        if not self.__locked and isinstance(position, int):
            self.__position=position
            self.__updated('position')

    def windowPostItGeometry(self):
        """Return note position in list"""
        return self.__windowPostItGeometry

    def setWindowPostItGeometry(self, geometry):
        """Set window note geometry"""
        if isinstance(geometry, QRect):
            self.__windowPostItGeometry=geometry
            self.__updated('geometry')

    def windowPostItCompact(self):
        """Return note compact mode active or not"""
        return self.__windowPostItCompact

    def setWindowPostItCompact(self, compact):
        """Set window note compact"""
        if isinstance(compact, bool):
            self.__windowPostItCompact=compact
            self.__updated('compact')

    def windowPostIt(self):
        """Return note compact mode active or not"""
        return self.__windowPostIt

    def setWindowPostIt(self, window):
        """Set window note compact"""
        if window is None or isinstance(window, BNNotePostIt):
            self.__windowPostIt=window

    def openWindowPostIt(self):
        if self.__windowPostIt is None:
            self.__windowPostIt=BNNotePostIt(self)
        if not self.__pinned:
            self.setPinned(True)

    def closeWindowPostIt(self):
        if not self.__windowPostIt is None:
            self.__windowPostIt.close()
        if self.__pinned:
            self.setPinned(False)


    def exportData(self, asQByteArray=True):
        """Export current note as internal format

        Export is made as a QByteArray:
        - allows to use it directly with document annotations
        - future usage will allow to store some binary data like images

        Internal format
        ---------------
        The internal format is simple:
        - first byte is format version (0x01)
        - next bytes are blocks


        > Values are stored in big-endian
        > If a block is not available in data, default value have to be applied
        > on import


        Blocks definition

        position | size    | description
                 | (bytes) |
        ---------+---------+----------------------------------------------------
        0        | 4       | total block size in bytes
        ---------+---------+----------------------------------------------------
        4        | 2       | block type
        ---------+---------+----------------------------------------------------
        6        | N       | block data


        According to block type, block data format is not the same


        *** Block type [0x0001 - note Id]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Unique Id


        *** Block type [0x0002 - Title]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Note title


        *** Block type [0x0003 - Description]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Note description


        *** Block type [0x0004 - Color index]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | Color index ()
                     |         |                 |  0: None
                     |         |                 |  1: Blue
                     |         |                 |  2: Green
                     |         |                 |  3: Yellow
                     |         |                 |  4: Orange
                     |         |                 |  5: Brown
                     |         |                 |  6: Red
                     |         |                 |  7: Purple
                     |         |                 |  8: Gray
                     |         |                 |


        *** Block type [0x0005 - Pinned]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: not pinned
                     |         |                 | 1: pinned

        *** Block type [0x0006 - Locked]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: unlocked
                     |         |                 | 1: locked

        *** Block type [0x0007 - Content text]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | UTF8 String     | Note text content


        *** Block type [0x0008 - Timestamp created]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 8       | double          | Timestamp at which note has
                     |         |                 | been created

        *** Block type [0x0009 - Timestamp updated]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 8       | double          | Timestamp for last modification
                     |         |                 | made on note


        *** Block type [0x000A - Position]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 2       | uint            | position number


        *** Block type [0x000B - Window geometry]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 2       | int             | window X position
            2        | 2       | int             | window Y position
            4        | 2       | uint            | window width
            8        | 2       | uint            | window height

        *** Block type [0x000C - Window compact]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: not compact
                     |         |                 | 1: compact

                     |         |                 |


        """
        # format version
        dataWrite=BytesRW()
        dataWrite.writeUShort(0x01)

        def writeBlock(blockType, fct, data):
            if data is None:
                return

            buffer=BytesRW()
            buffer.writeUInt2(blockType)

            if fct=='str':
                buffer.writeStr(data)
            elif fct=='ushort':
                buffer.writeUShort(data)
            elif fct=='bool':
                buffer.writeBool(data)
            elif fct=='float8':
                buffer.writeFloat8(data)
            elif fct=='uint4':
                buffer.writeUInt4(data)
            elif fct=='qrect':
                buffer.writeInt4(data.x())
                buffer.writeInt4(data.y())
                buffer.writeUInt4(data.width())
                buffer.writeUInt4(data.height())

            dataWrite.writeUInt4(4+buffer.tell())
            dataWrite.write(buffer.getvalue())
            buffer.close()


        writeBlock(0x0001, 'str', self.__id)
        writeBlock(0x0002, 'str', self.__title)
        writeBlock(0x0003, 'str', self.__description)
        writeBlock(0x0004, 'ushort', self.__colorIndex)
        writeBlock(0x0005, 'bool', self.__pinned)
        writeBlock(0x0006, 'bool', self.__locked)
        writeBlock(0x0007, 'str', self.__text)
        writeBlock(0x0008, 'float8', self.__timestampCreated)
        writeBlock(0x0009, 'float8', self.__timestampUpdated)
        writeBlock(0x000A, 'uint4', self.__position)
        writeBlock(0x000B, 'qrect', self.__windowPostItGeometry)
        writeBlock(0x000C, 'bool', self.__windowPostItCompact)

        if asQByteArray:
            return QByteArray(dataWrite.getvalue())
        else:
            return dataWrite.getvalue()

    def importData(self, data, importId=True):
        """Import current note from internal format (QByteArray)"""

        if not isinstance(data, (bytes, QByteArray)):
            return False

        dataRead=BytesRW(data)
        # skip version..
        dataRead.seek(1)

        self.__emitUpdated=False
        locked=False
        self.setLocked(False)
        timestampUpdated=None

        nextBlock=1

        while dataRead.tell()==nextBlock and (blockContentSize:=dataRead.readUInt4()):
            blockContentSize-=6
            # current position should be equal to nextblockPosition, otherwise quit
            nextBlock=dataRead.tell()+blockContentSize+2

            blockType=dataRead.readUInt2()
            if blockType is None:
                break

            if blockType==0x0001:
                newId=dataRead.readStr(blockContentSize)
                if importId:
                    self.__setId(newId)
            elif blockType==0x0002:
                self.setTitle(dataRead.readStr(blockContentSize))
            elif blockType==0x0003:
                self.setDescription(dataRead.readStr(blockContentSize))
            elif blockType==0x0004:
                self.setColorIndex(dataRead.readUShort())
            elif blockType==0x0005:
                self.setPinned(dataRead.readBool())
            elif blockType==0x0006:
                #self.setLocked(bytesUShort(block[1])==1)
                locked=dataRead.readBool()
            elif blockType==0x0007:
                self.setText(dataRead.readStr(blockContentSize))
            elif blockType==0x0008:
                self.setTimestampCreated(dataRead.readFloat8())
            elif blockType==0x0009:
                #self.setTimestampUpdated(bytesDouble(block[1]))
                timestampUpdated=dataRead.readFloat8()
            elif blockType==0x000A:
                self.setPosition(dataRead.readUInt4())
            elif blockType==0x000B:
                self.setWindowPostItGeometry(QRect(dataRead.readInt4(),
                                             dataRead.readInt4(),
                                             dataRead.readUInt4(),
                                             dataRead.readUInt4()))
            elif blockType==0x000C:
                self.setWindowPostItCompact(dataRead.readBool())

        dataRead.close()

        # must be done at the end..
        # - get real timestamp update saved in data
        if not timestampUpdated is None:
            self.setTimestampUpdated(timestampUpdated)
        # - lock at the end (otherwise risk to not update values)
        self.setLocked(locked)

        self.__emitUpdated=True
        self.__updated('import')

        return True


class BNNotes(QObject):
    updated = Signal(BNNote, str)
    updateReset = Signal()
    updateAdded = Signal(list)
    updateRemoved = Signal(list)
    updateMoved = Signal(list)

    MIME_TYPE='application/x-kritaplugin-bulinotes'

    def __init__(self):
        """Initialize object"""
        super(BNNotes, self).__init__(None)

        # store everything in a dictionary
        # key = id
        # value = BNNotes
        self.__notes = {}

        self.__enabled=False
        self.__temporaryDisabled=False

        # list of added hash
        self.__updateAdd=[]
        self.__updateRemove=[]

        self.__document=None

    def __repr__(self):
        return f"<BNNotes()>"

    def __itemUpdated(self, item, property):
        """A note have been updated"""
        self.__setAnnotation(item)
        if not self.__temporaryDisabled:
            self.updated.emit(item, property)

    def __emitUpdateReset(self):
        """List have been cleared/loaded"""
        if not self.__temporaryDisabled:
            self.updateReset.emit()

    def __emitUpdateAdded(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items=self.__updateAdd.copy()
        self.__updateAdd=[]
        if not self.__temporaryDisabled:
            self.updateAdded.emit(items)

    def __emitUpdateRemoved(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items=self.__updateRemove.copy()
        self.__updateRemove=[]
        if not self.__temporaryDisabled:
            self.updateRemoved.emit(items)

    def __setAnnotation(self, note):
        """Set annotation for given note"""
        if self.__document:
            self.__document.setAnnotation(f'BuliNotes/Note({note.id()})', f'A note from plugin Buli Notes\n-----------------------------\n{note.description()}', note.exportData())

    def __delAnnotation(self, note):
        """Set annotation for given note"""
        if self.__document:
            self.__document.removeAnnotation(f'BuliNotes/Note({note.id()})')

    def length(self):
        """Return number of notes"""
        return len(self.__notes)

    def idList(self):
        """Return list of id; no sort"""
        return list(self.__notes.keys())

    def get(self, id):
        """Return note from id, or None if nothing is found"""
        if id in self.__notes:
            return self.__notes[id]
        return None

    def exists(self, item):
        """Return True if item is already in notes, otherwise False"""
        if isinstance(item, str):
            return (item in self.__notes)
        elif isinstance(item, BNNote):
            return (item.id() in self.__notes)
        return False

    def clear(self):
        """Clear all notes"""
        state=self.__temporaryDisabled

        self.__temporaryDisabled=True
        for key in list(self.__notes.keys()):
            self.remove(self.__notes[key])
        self.__temporaryDisabled=state
        if not self.__temporaryDisabled:
            self.__emitUpdateReset()

    def add(self, item):
        """Add BCClipboardItem to pool"""
        if isinstance(item, BNNote):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__notes[item.id()]=item
            self.__setAnnotation(item)
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Add BCClipboardItem to pool"""
        removedNote=None

        if isinstance(item, list) and len(item)>0:
            self.__temporaryDisabled=True
            for note in item:
                self.remove(note)
            self.__temporaryDisabled=False
            self.__emitUpdateRemoved()
            return True

        if isinstance(item, str) and item in self.__notes:
            removedNote=self.__notes.pop(item, None)
        elif isinstance(item, BNNote):
            removedNote=self.__notes.pop(item.id(), None)

        if not removedNote is None:
            self.__delAnnotation(removedNote)
            removedNote.updated.disconnect(self.__itemUpdated)
            if removedNote.pinned():
                removedNote.closeWindowPostIt()
            self.__updateRemove.append(removedNote.id())
            self.__emitUpdateRemoved()
            return True
        return False

    def update(self, item):
        """Update note"""
        if isinstance(item, BNNote):
            if self.exists(item.id()):
                self.__notes[item.id()]=item
                self.__setAnnotation(item)
                self.__itemUpdated(item, '*')
            return True
        return False

    def setDocument(self, document):
        """Set current document"""
        if document!=self.__document:
            self.__temporaryDisabled=True

            self.__document=document

            # when document is changed, need to reload all notes
            self.clear()

            if not self.__document is None:
                for annotation in self.__document.annotationTypes():
                    if re.match('BuliNotes/Note\([^\)]+\)', annotation):
                        note=BNNote()
                        note.importData(self.__document.annotation(annotation))
                        note.updated.connect(self.__itemUpdated)
                        self.__updateAdd.append(note.id())
                        self.__notes[note.id()]=note
                        if note.pinned():
                            note.openWindowPostIt()

            self.__temporaryDisabled=False
            self.__emitUpdateReset()

    def clipboardCopy(self, notes):
        """Copy selected notes to clipboard"""

        binaryList=[]
        htmlList=[]
        plainTextList=[]

        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, BNNote):
                    binaryList.append(note.exportData(False))
                    #htmlList.append(note.toHtml())
                    #plainTextList.append(note.toPlainText())

        if len(binaryList)>0:
            dataWrite=BytesRW()
            dataWrite.writeUInt2(len(binaryList))
            for data in binaryList:
                dataWrite.writeUInt4(len(data))
                dataWrite.write(data)

            mimeContent=QMimeData()
            mimeContent.setData(BNNotes.MIME_TYPE, QByteArray(dataWrite.getvalue()))

            clipboard = QGuiApplication.clipboard()
            clipboard.setMimeData(mimeContent)

            return True
        return False

    def clipboardCut(self, notes):
        """Copy selected notes to clipboard and remove them"""
        if self.clipboardCopy(notes):
            # remove items only if copied to clipooard
            self.remove(notes)

    def clipboardPaste(self, items=None):
        """Paste notes from clipboard, if any"""
        clipboardMimeContent = QGuiApplication.clipboard().mimeData(QClipboard.Clipboard)
        if clipboardMimeContent.hasFormat(BNNotes.MIME_TYPE):
            self.__temporaryDisabled=True
            data=bytes(clipboardMimeContent.data(BNNotes.MIME_TYPE))

            dataRead=BytesRW(data)
            nbNotes=dataRead.readUInt2()
            for noteNumber in range(nbNotes):
                dataLength=dataRead.readUInt4()
                dataNote=dataRead.read(dataLength)

                note=BNNote()
                if note.importData(dataNote, False):
                    self.add(note)
                    if note.pinned():
                        note.openWindowPostIt()

            self.__temporaryDisabled=False
            self.__emitUpdateReset()




    def clipboardPastable(self):
        """Return True if there's pastable notes in clipboard"""
        clipboardMimeContent = QGuiApplication.clipboard().mimeData(QClipboard.Clipboard)
        return clipboardMimeContent.hasFormat(BNNotes.MIME_TYPE)





class BNNoteEditor(EDialog):

    @staticmethod
    def edit(note):
        """Open a dialog box to edit note"""
        dlgBox = BNNoteEditor(note)

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.note()
        else:
            return None

    def __init__(self, note=None, name="Buli Notes", parent=None):
        super(BNNoteEditor, self).__init__(os.path.join(os.path.dirname(__file__), 'resources', 'bnnoteeditor.ui'), parent)

        self.setWindowTitle(name)

        if not isinstance(note, BNNote):
            self.__note=BNNote()
        else:
            self.__note=note

        self.__workingNote=BNNote()
        self.__workingNote.setTitle(self.__note.title())
        self.__workingNote.setDescription(self.__note.description())
        self.__workingNote.setColorIndex(self.__note.colorIndex())
        self.__workingNote.setText(self.__note.text())

        self.leTitle.setText(self.__note.title())
        self.pteDescription.setPlainText(self.__note.description())
        self.wColorIndex.setColorIndex(self.__note.colorIndex())
        self.wteText.setHtml(self.__note.text())

        currentTime=time.time()
        delayCreated=currentTime - note.timestampCreated()
        delayUpdated=currentTime - note.timestampUpdated()

        if delayCreated<1:
            self.lblTimestampLabel.setVisible(False)
            self.lblTimestamp.setVisible(False)
        else:
            self.lblTimestamp.setText(f'{tsToStr(note.timestampCreated())} ({secToStrTime(delayCreated)} ago)\n{tsToStr(note.timestampUpdated())} ({secToStrTime(delayUpdated)} ago)')

        self.btOk.clicked.connect(self.__accept)
        self.btCancel.clicked.connect(self.__reject)

        self.setSizeGripEnabled(True)


    def __accept(self):
        """Accept modifications and return result"""
        self.__note.setTitle(self.leTitle.text())
        self.__note.setDescription(self.pteDescription.toPlainText())
        self.__note.setColorIndex(self.wColorIndex.colorIndex())
        self.__note.setText(self.wteText.toHtml())

        self.accept()


    def __reject(self):
        """reject modifications and return None"""
        self.reject()


    def note(self):
        """Return current note"""
        return self.__note



class BNNotePostIt(QWidget):

    def __init__(self, note=None):
        super(BNNotePostIt, self).__init__(Krita.instance().activeWindow().qwindow())

        # os.path.join(os.path.dirname(__file__), 'resources', 'bnnoteeditor.ui')
        if not isinstance(note, BNNote):
            self.__note=BNNote()
        else:
            self.__note=note

        self.__note.updated.connect(self.__updatedNote)

        self.__globalPos = None
        self.__moving=False

        self.__factor=0.85

        self.__buildUi()

        self.show()

    def __buildUi(self):
        """Build window interface"""
        self.setAutoFillBackground(True)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

        self.__inInit=True

        if self.__note.windowPostItGeometry():
            self.setGeometry(self.__note.windowPostItGeometry())
        else:
            tmpFrameGeometry = self.frameGeometry()
            # center window on current screen
            #tmpFrameGeometry.moveCenter(QDesktopWidget().availableGeometry().center())
            # center window on Krita window
            tmpFrameGeometry.moveCenter(Krita.instance().activeWindow().qwindow().geometry().center())
            self.move(tmpFrameGeometry.topLeft())

        self.__layout=QVBoxLayout(self)
        self.__layout.setContentsMargins(0,0,0,0)
        self.__layout.setSpacing(1)

        self.__titleBar=BNNotePostItTitleBar(self, self.__note.windowPostItCompact())
        self.__titleBar.compactModeChanged.connect(self.__setCompact)

        self.__textEdit=BNNotePostItText(self)
        self.__sizeGrip=QSizeGrip(self.__textEdit)

        self.__layout.addWidget(self.__titleBar)
        self.__layout.addWidget(self.__textEdit)
        self.__layout.addWidget(self.__sizeGrip, 0, Qt.AlignBottom|Qt.AlignRight)

        self.setLayout(self.__layout)

        self.__updateUi()
        self.__inInit=False

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __updatedNote(self, note, property):
        if property in ['title', 'text', 'colorIndex']:
            self.__updateUi()

    def __setCompact(self, value):
        if not self.__inInit:
            self.__note.setWindowPostItCompact(value)
        if self.__note.windowPostItCompact():
            self.__textEdit.setHtml(re.sub(r"font-size\s*:\s*(\d+)pt;", self.__applyCompactFactor, self.__note.text()))
        else:
            self.__textEdit.setHtml(self.__note.text())
        self.__textEdit.setCompact(value)

    def __updateUi(self):
        """Update UI content according to note content"""
        self.__titleBar.setNote(self.__note)
        text=self.__note.text()
        if self.__note.windowPostItCompact():
            text=re.sub(r"font-size:\s*(\d+)pt;", self.__applyCompactFactor, text)

        self.__textEdit.setHtml(text)

    def eventFilter(self, source, event):
        if source==self.__textEdit and isinstance(event, QMouseEvent) and (event.modifiers() & Qt.ControlModifier):
            # block event, pass it to parent (allows to drag window to move it)
            return True
        return super(BNNotePostIt, self).eventFilter(source, event)

    def closeEvent(self, event):
        """About to close window"""
        self.__note.setWindowPostIt(None)
        self.__note.closeWindowPostIt()

    def mousePressEvent(self, event):
        """User press anywhere on note window, so enter on drag mode"""
        self.__globalPos=event.globalPos()
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """If in drag mode, move current note window"""
        if self.__globalPos and not self.__moving:
            self.__moving=True
            delta = QPoint(event.globalPos() - self.__globalPos)

            # -- the really dirty trick...
            # Don't really know why but without it, when moving window on my
            # secondary screen there's a really weird "shake" effect and
            # defined position sometime gets out of hand...
            #
            # having a 1ms timer is enough to fix the problem
            # suspecting something with too much event or something like that...
            BCTimer.sleep(1)
            # --

            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.__globalPos = event.globalPos()
            self.__moving=False

    def mouseReleaseEvent(self, event):
        """Exit drag mode"""
        self.__note.setWindowPostItGeometry(self.geometry())
        self.__globalPos=None
        self.setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event):
        """PostIt is resized"""
        self.__note.setWindowPostItGeometry(self.geometry())


class BNNotePostItText(QTextEdit):
    def __init__(self, parent):
        super(BNNotePostItText, self).__init__(parent)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setReadOnly(True)
        self.setWindowFlags(Qt.SubWindow)
        self.__parent=parent
        self.__moving=False
        self.__globalPos=None
        self.setCompact(False)

    def setCompact(self, value):
        if value:
            self.verticalScrollBar().setStyleSheet("""
QScrollBar:vertical {
     background-color: palette(base);
     width: 8px;
     margin: 0px;
     border: 1px transparent #000000;
 }

 QScrollBar::handle:vertical {
     background-color: palette(text);
     min-height: 8px;
     border-radius: 4px;
 }

 QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
     margin: 0px 0px 0px 0px;
     height: 0px;
 }
        """)
            self.horizontalScrollBar().setStyleSheet("""
QScrollBar:horizontal {
     background-color: palette(base);
     width: 8px;
     margin: 0px;
     border: 1px transparent #000000;
 }

 QScrollBar::handle:horizontal {
     background-color: palette(text);
     min-height: 8px;
     border-radius: 4px;
 }

 QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
     margin: 0px 0px 0px 0px;
     width: 0px;
 }
        """)
        else:
            self.verticalScrollBar().setStyleSheet("""
QScrollBar:vertical {
     background-color: palette(base);
     width: 14px;
     margin: 0px;
     border: 1px transparent #000000;
 }

 QScrollBar::handle:vertical {
     background-color: palette(text);
     min-height: 14px;
     border-radius: 7px;
 }

 QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
     margin: 0px 0px 0px 0px;
     height: 0px;
 }
        """)
            self.horizontalScrollBar().setStyleSheet("""
QScrollBar:horizontal {
     background-color: palette(base);
     width: 14px;
     margin: 0px;
     border: 1px transparent #000000;
 }

 QScrollBar::handle:horizontal {
     background-color: palette(text);
     min-height: 14px;
     border-radius: 7px;
 }

 QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
     margin: 0px 0px 0px 0px;
     width: 0px;
 }
        """)

    def mousePressEvent(self, event):
        """User press anywhere on note window, so enter on drag mode"""
        if event.modifiers() & Qt.ControlModifier:
            self.__globalPos=event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super(BNNotePostItText, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """If in drag mode, move current note window"""
        if self.__globalPos:
            if not self.__moving:
                self.__moving=True
                delta = QPoint(event.globalPos() - self.__globalPos)

                # -- the really dirty trick...
                # Don't really know why but without it, when moving window on my
                # secondary screen there's a really weird "shake" effect and
                # defined position sometime gets out of hand...
                #
                # having a 1ms timer is enough to fix the problem
                # suspecting something with too much event or something like that...
                BCTimer.sleep(1)
                # --

                self.__parent.move(self.__parent.x() + delta.x(), self.__parent.y() + delta.y())
                self.__globalPos = event.globalPos()
                self.__moving=False
        else:
            super(BNNotePostItText, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Exit drag mode"""
        if self.__globalPos:
            self.__globalPos=None
            self.setCursor(Qt.ArrowCursor)
        else:
            super(BNNotePostItText, self).mouseReleaseEvent(event)


class BNNotePostItTitleBar(QWidget):
    compactModeChanged=Signal(bool)

    def __init__(self, parent, compact=False):
        super(BNNotePostItTitleBar, self).__init__(parent)
        self.__parent=parent
        self.__layout=QHBoxLayout()
        self.__layout.setContentsMargins(1,1,1,1)
        self.__layout.setSpacing(1)

        self.__inInit=True

        self.__factor=0.95
        self.__height=0

        self.__lblTitle = QLabel("")
        self.__lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.__lblTitle.minimumSizeHint=self.minimumSizeHint

        self.__font = self.font()
        self.__originalFontSizePt=self.__font.pointSizeF()
        self.__originalFontSizePx=self.__font.pixelSize()

        self.__fntMetric=QFontMetrics(self.__font)

        self.__btClose = QToolButton()
        self.__btClose.clicked.connect(self.__parent.close)
        self.__btClose.setIcon(QIcon(':/white/close'))
        self.__btClose.setFocusPolicy(Qt.NoFocus)
        self.__btClose.setAutoRaise(True)
        self.__btClose.setStyleSheet("""
QToolButton {
    border-radius: 2px;
}
QToolButton:hover {
    border: none;
    background-color: rgba(255,255,255,50);
}
            """)

        self.__btCompact = QToolButton()
        self.__btCompact.clicked.connect(self.__setCompact)
        self.__btCompact.setIcon(QIcon(':/white/compact_on'))
        self.__btCompact.setFocusPolicy(Qt.NoFocus)
        self.__btCompact.setAutoRaise(True)
        self.__btCompact.setCheckable(True)
        self.__btCompact.setStyleSheet("""
QToolButton {
    border-radius: 2px;
}
QToolButton:hover {
    border: none;
    background-color: rgba(255,255,255,50);
}
            """)

        self.__title=''
        self.__color=None

        self.__setCompact(compact)


        self.__layout.addWidget(self.__lblTitle)
        self.__layout.addWidget(self.__btCompact)
        self.__layout.addWidget(self.__btClose)
        self.setLayout(self.__layout)
        self.__inInit=False

    def minimumSizeHint(self):
        return QSize(0, self.__height)

    def __setCompact(self, value):
        if value:
            self.__factor=0.65
            self.__btCompact.setChecked(True)
            self.__btCompact.setIcon(QIcon(':/white/compact_off'))
        else:
            self.__factor=0.95
            self.__btCompact.setChecked(False)
            self.__btCompact.setIcon(QIcon(':/white/compact_on'))

        if self.__originalFontSizePt>-1:
            self.__font.setPointSizeF(self.__originalFontSizePt*self.__factor)
        else:
            self.__font.setPixelSize(int(self.__originalFontSizePx*self.__factor))

        self.__fntMetric=QFontMetrics(self.__font)
        self.__height=self.__fntMetric.height()

        self.__lblTitle.setFont(self.__font)
        self.__btClose.setFixedSize(self.__height, self.__height)
        self.__btClose.setIconSize(QSize(self.__height-2,self.__height-2))
        self.__btCompact.setFixedSize(self.__height, self.__height)
        self.__btCompact.setIconSize(QSize(self.__height-2,self.__height-2))

        if not self.__inInit:
            self.compactModeChanged.emit(value)

    def __updateTitle(self):
        """Update title ellipsis"""
        self.__lblTitle.setText(self.__fntMetric.elidedText(self.__title, Qt.ElideRight, self.__lblTitle.width() - 2))

    def setNote(self, note):
        """Set title bar content"""
        colorIndex=note.colorIndex()
        if colorIndex==WStandardColorSelector.COLOR_NONE:
            self.setAutoFillBackground(False)
        else:
            palette=self.__lblTitle.palette()
            self.setAutoFillBackground(True)
            palette.setColor(QPalette.Window, WStandardColorSelector.getColor(colorIndex).darker(200))
            palette.setColor(QPalette.WindowText, Qt.white)
            self.setPalette(palette)

        self.__title=note.title()
        self.__setCompact(note.windowPostItCompact())
        self.__updateTitle()

    def resizeEvent(self, event):
        """Update title ellipsis when resized"""
        self.__updateTitle()
