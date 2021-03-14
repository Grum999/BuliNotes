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

import krita
from krita import (
                Scratchpad,
                View,
                ManagedColor,
                Resource,
                PresetChooser
            )

from pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from pktk.modules.utils import (
                        secToStrTime,
                        tsToStr,
                        qImageToPngQByteArray,
                        BCTimer
                    )
from pktk.modules.edialog import EDialog
from pktk.modules.bytesrw import BytesRW
from pktk.widgets.wstandardcolorselector import WStandardColorSelector
from pktk.widgets.wmenuitem import WMenuBrushesPresetSelector
from pktk.widgets.wcolorselector import WMenuColorPicker
from pktk.widgets.wtextedit import WTextEditDialog

from .bnbrush import (BNBrush, BNBrushes)
from .bnwbrushes import BNBrushesModel
from .bnnote_postit import BNNotePostIt

class BNNote(QObject):
    """A note"""
    updated=Signal(QObject, str)

    CONTENT_TEXT=0x01
    CONTENT_SCRATCHPAD=0x02
    CONTENT_BRUSHES=0x03
    #CONTENT_TASKS=0x04
    __CONTENT_LAST=0x03

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
        self.__windowPostItBrushIconSizeIndex=1

        self.__scratchpadBrushName='b)_Basic-5_Size'
        self.__scratchpadBrushSize=5
        self.__scratchpadBrushColor=QColor(Qt.black)
        self.__scratchpadImage=None

        self.__brushes=BNBrushes()
        self.__brushes.updated.connect(self.__updatedBrushes)
        self.__brushes.updateReset.connect(self.__updatedBrushes)
        self.__brushes.updateAdded.connect(self.__updatedBrushes)
        self.__brushes.updateRemoved.connect(self.__updatedBrushes)

        self.__selectedType=BNNote.CONTENT_TEXT

        self.__emitUpdated=0
        self.beginUpdate()

        # if a BNNotePostIt is opened, keep window reference
        self.__windowPostIt=None

        self.__setId(id)
        self.setTitle(title)
        self.setDescription(description)

        self.endUpdate()

    def __repr__(self):
        return f'<BNNote({self.__id}, {self.__title}, {self.__pinned}, {self.__locked}, {self.__windowPostItCompact})>'

    def __updatedBrushes(self, property=None):
        """Brushes have been udpated"""
        self.__updated('brushes')

    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated==0:
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

    def windowPostItBrushIconSizeIndex(self):
        """Return current size index for post-it brushes icon list"""
        return self.__windowPostItBrushIconSizeIndex

    def setWindowPostItBrushIconSizeIndex(self, index):
        """Set window note compact"""
        if isinstance(index, int) and index>=0 and index<=4:
            self.__windowPostItBrushIconSizeIndex=index
            self.__updated('brushIconSizeIndex')

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

    def scratchpadBrushName(self):
        """Return last brush name used on scratchpad"""
        return self.__scratchpadBrushName

    def setScratchpadBrushName(self, value):
        """Set last brush name used on scratchpad"""
        self.__scratchpadBrushName=value
        self.__updated('scratchpadBrushName')

    def scratchpadBrushSize(self):
        """Return last brush size used on scratchpad"""
        return self.__scratchpadBrushSize

    def setScratchpadBrushSize(self, value):
        """Set last brush size used on scratchpad"""
        if isinstance(value, int):
            self.__scratchpadBrushSize=max(1, min(value, 200))
            self.__updated('scratchpadBrushSize')

    def scratchpadBrushColor(self):
        """Return last brush color used on scratchpad"""
        return self.__scratchpadBrushColor

    def setScratchpadBrushColor(self, value):
        """Set last brush color used on scratchpad"""
        if isinstance(value, QColor):
            self.__scratchpadBrushColor=value
            self.__updated('scratchpadBrushColor')
        elif isinstance(value, int):
            self.__scratchpadBrushColor=QColor(value)
            self.__updated('scratchpadBrushColor')

    def scratchpadImage(self):
        """Return scratchpad content as QImage or None if there's no scratchpad drawing"""
        return self.__scratchpadImage

    def setScratchpadImage(self, value):
        """Set last brush color used on scratchpad"""
        if value is None:
            self.__scratchpadImage=None
            self.__updated('scratchpadImage')
        elif isinstance(value, QImage):
            ptr = value.bits()
            ptr.setsize(value.byteCount())
            ptrBytes=bytes(ptr)
            if len(ptrBytes.lstrip(b'\xFF'))==0:
                # empty scratchpad (all content is white)
                # rstrip (or lstrip) the bytes object is the fastest way
                # I found to check if there's a non-white pixel in image
                self.__scratchpadImage=None
            else:
                self.__scratchpadImage=value

    def hasText(self):
        """Return True if note has text content"""
        return (self.__text.strip()!='')

    def hasScratchpad(self):
        """Return True if note has scratchpad content"""
        return (not self.__scratchpadImage is None)

    def hasBrushes(self):
        """Return True if note has brushes content"""
        return self.__brushes.length()>0

    def selectedType(self):
        """Return current selected type"""
        return self.__selectedType

    def setSelectedType(self, value):
        """Set current selected types"""
        if isinstance(value, int) and value>=1 and value<=BNNote.__CONTENT_LAST:
            self.__selectedType=value
            self.__updated('selectedType')

    def brushes(self):
        """Return brush list"""
        return self.__brushes

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
        > All blocks are optional; if a block is not available, default value
        > have to be applied on import
        > Unknown block number are ignored


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

        *** Block type [0x0002 - Timestamp created]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 8       | double          | Timestamp at which note has
                     |         |                 | been created


        *** Block type [0x0003 - Timestamp updated]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 8       | double          | Timestamp for last modification
                     |         |                 | made on note


        *** Block type [0x0010 - Title]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Note title


        *** Block type [0x0011 - Description]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Note description


        *** Block type [0x0012 - Color index]

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


        *** Block type [0x0020 - Pinned]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: not pinned
                     |         |                 | 1: pinned

        *** Block type [0x0021 - Locked]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: unlocked
                     |         |                 | 1: locked

        *** Block type [0x0022 - Position]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 2       | uint            | position number


        *** Block type [0x0030 - Window geometry]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 2       | int             | window X position
            2        | 2       | int             | window Y position
            4        | 2       | uint            | window width
            8        | 2       | uint            | window height


        *** Block type [0x0031 - Window compact]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0: not compact
                     |         |                 | 1: compact


        *** Block type [0x0032 - Selected type]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | Current selected type
                     |         |                 | Text=0x01
                     |         |                 | Scratchpad=0x02
                     |         |                 | Brushes=0x03
                     |         |                 |


        *** Block type [0x0033 - Window brushes icon size index]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | 0x00: 32px
                     |         |                 | 0x01: 64px
                     |         |                 | 0x02: 96px
                     |         |                 | 0x03: 128px
                     |         |                 | 0x04: 192px
                     |         |                 |


        *** Block type [0x0100 - Content text]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | Note text content


        *** Block type [0x0200 - Scratchpad:BrushName]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | UTF8 String     | last brush name that has been
                     |         |                 | used on scratchpad
                     |         |                 | (resource 'preset')


        *** Block type [0x0201 - Scratchpad:BrushSize]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 1       | ushort          | last brush size in pixels
                     |         |                 | that has been used on scratchpad
                     |         |                 | available range is 1 - 200


        *** Block type [0x0202 - Scratchpad:BrushColor]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | 4       | uint            | last brush color stored as ARGB
                     |         |                 | values
                     |         |                 |


        *** Block type [0x0203 - Scratchpad:Data]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | bytes           | scratchpad content stored as
                     |         |                 | PNG file data
                     |         |                 |


        *** Block type [0x0300 - brush]

            position | size    | format          | description
                     | (bytes) |                 |
            ---------+---------+-----------------+------------------------------
            0        | N       | bytes           | An exported brush definition
                     |         |                 | note: 0 to N brushes definition
                     |         |                 | can be defined
                     |         |                 |
                     |         |                 |




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
            elif fct=='bytes':
                buffer.write(data)
            elif fct=='ushort-list':
                for value in data:
                    buffer.writeUShort(value)

            dataWrite.writeUInt4(4+buffer.tell())
            dataWrite.write(buffer.getvalue())
            buffer.close()

        writeBlock(0x0001, 'str', self.__id)
        writeBlock(0x0002, 'float8', self.__timestampCreated)
        writeBlock(0x0003, 'float8', self.__timestampUpdated)

        writeBlock(0x0010, 'str', self.__title)
        writeBlock(0x0011, 'str', self.__description)
        writeBlock(0x0012, 'ushort', self.__colorIndex)

        writeBlock(0x0020, 'bool', self.__pinned)
        writeBlock(0x0021, 'bool', self.__locked)
        writeBlock(0x0022, 'uint4', self.__position)

        writeBlock(0x0030, 'qrect', self.__windowPostItGeometry)
        writeBlock(0x0031, 'bool', self.__windowPostItCompact)
        writeBlock(0x0032, 'ushort', self.__selectedType)
        writeBlock(0x0033, 'ushort', self.__windowPostItBrushIconSizeIndex)

        writeBlock(0x0100, 'str', self.__text)

        writeBlock(0x0200, 'str', self.__scratchpadBrushName)
        writeBlock(0x0201, 'ushort', self.__scratchpadBrushSize)
        writeBlock(0x0202, 'uint4', self.__scratchpadBrushColor.rgba())
        if not self.__scratchpadImage is None:
            writeBlock(0x0203, 'bytes', bytes(qImageToPngQByteArray(self.__scratchpadImage)))

        for brush in self.__brushes.idList():
            writeBlock(0x0300, 'bytes', self.__brushes.get(brush).exportData())

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

        self.beginUpdate()
        locked=False
        self.setLocked(False)
        timestampUpdated=None

        #self.__brushes.beginUpdate()
        self.__brushes.clear()

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
                self.setTimestampCreated(dataRead.readFloat8())
            elif blockType==0x0003:
                #self.setTimestampUpdated(dataRead.readFloat8())
                # ==> keep value in memory and set it at the end, otherwise will
                #     be changed when other properties are loaded
                timestampUpdated=dataRead.readFloat8()
            elif blockType==0x0010:
                self.setTitle(dataRead.readStr(blockContentSize))
            elif blockType==0x0011:
                self.setDescription(dataRead.readStr(blockContentSize))
            elif blockType==0x0012:
                self.setColorIndex(dataRead.readUShort())
            elif blockType==0x0020:
                self.setPinned(dataRead.readBool())
            elif blockType==0x0021:
                #self.setLocked(dataRead.readBool())
                # ==> keep value in memory and set it at the end, otherwise it
                #     will be impossible to update other values :-)
                locked=dataRead.readBool()
            elif blockType==0x0022:
                self.setPosition(dataRead.readUInt4())
            elif blockType==0x0030:
                self.setWindowPostItGeometry(QRect(dataRead.readInt4(),
                                             dataRead.readInt4(),
                                             dataRead.readUInt4(),
                                             dataRead.readUInt4()))
            elif blockType==0x0031:
                self.setWindowPostItCompact(dataRead.readBool())
            elif blockType==0x0032:
                self.setSelectedType(dataRead.readUShort())
            elif blockType==0x0033:
                self.setWindowPostItBrushIconSizeIndex(dataRead.readUShort())
            elif blockType==0x0100:
                self.setText(dataRead.readStr(blockContentSize))
            elif blockType==0x0200:
                self.setScratchpadBrushName(dataRead.readStr(blockContentSize))
            elif blockType==0x0201:
                self.setScratchpadBrushSize(dataRead.readUShort())
            elif blockType==0x0202:
                self.setScratchpadBrushColor(dataRead.readUInt4())
            elif blockType==0x0203:
                self.setScratchpadImage(QImage.fromData(QByteArray(dataRead.read(blockContentSize))))
            elif blockType==0x0300:
                brush=BNBrush()
                brush.importData(dataRead.read(blockContentSize))
                self.__brushes.add(brush)

        dataRead.close()
        #self.__brushes.endUpdate()

        # must be done at the end..
        # - get real timestamp update saved in data
        if not timestampUpdated is None:
            self.setTimestampUpdated(timestampUpdated)
        # - lock at the end (otherwise risk to not update values)
        self.setLocked(locked)

        self.endUpdate()
        self.__updated('import')

        return True

    def beginUpdate(self):
        """Start updating note massivelly and then do note emit update"""
        self.__emitUpdated+=1

    def endUpdate(self):
        """Start updating note massivelly and then do note emit update"""
        self.__emitUpdated-=1
        if self.__emitUpdated<0:
            self.__emitUpdated=0
        elif self.__emitUpdated==0:
            self.__updated('*')


class BNNotes(QObject):
    """Collection of notes"""
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
        """Add Note to list"""
        if isinstance(item, BNNote):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__notes[item.id()]=item
            self.__setAnnotation(item)
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Remove Note from list"""
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

        if Krita.instance().activeWindow() is None:
            self.reject()
        elif Krita.instance().activeWindow().activeView() is None:
            self.reject()

        self.__name=name
        self.setWindowTitle(name)
        self.setSizeGripEnabled(True)

        if not isinstance(note, BNNote):
            self.__note=BNNote()
        else:
            self.__note=note


        self.__activeView=Krita.instance().activeWindow().activeView()
        self.__activeViewCurrentConfig={}
        self.__allBrushesPreset = Krita.instance().resources("preset")

        self.__scratchpadHandWritting=Scratchpad(self.__activeView, QColor(Qt.white), self)
        self.__scratchpadHandWritting.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.__scratchpadHandWritting.linkCanvasZoom(True)

        self.__currentUiBrush=BNBrush()
        self.__currentUiBrush.fromBrush()

        self.__scratchpadTestBrush=Scratchpad(self.__activeView, QColor(Qt.white), self)
        self.__scratchpadTestBrush.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__scratchpadTestBrush.linkCanvasZoom(False)
        self.__scratchpadTestBrush.setModeManually(False)
        #self.__scratchpadTestBrush.setMode('painting')
        self.wBrushScratchpad.layout().addWidget(self.__scratchpadTestBrush)

        self.__saveViewConfig()
        self.__buildUi()
        self.__initViewConfig()


    def __buildUi(self):
        """Build/Initialise dialog widgets"""
        self.leTitle.setText(self.__note.title())
        self.pteDescription.setPlainText(self.__note.description())
        self.wColorIndex.setColorIndex(self.__note.colorIndex())
        self.wteText.setHtml(self.__note.text())


        self.__actionSelectBrushScratchpadColor=WMenuColorPicker()
        self.__actionSelectBrushScratchpadColor.colorPicker().colorUpdated.connect(self.__actionBrushScratchpadSetColor)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorRGB(False)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorCMYK(False)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorHSV(True)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorHSL(False)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorAlpha(False)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionCompactUi(True)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionPreviewColor(True)
        self.__actionSelectBrushScratchpadColor.colorPicker().setOptionShowColorCombination(False)

        menuBrushScratchpadColor = QMenu(self.tbColor)
        menuBrushScratchpadColor.addAction(self.__actionSelectBrushScratchpadColor)

        self.tbBrushAdd.clicked.connect(self.__actionBrushAdd)
        self.tbBrushEdit.clicked.connect(self.__actionBrushEdit)
        self.tbBrushDelete.clicked.connect(self.__actionBrushDelete)
        self.tbBrushScratchpadClear.clicked.connect(self.__actionBrushScratchpadClear)
        self.tbBrushScratchpadColor.setMenu(menuBrushScratchpadColor)

        img=self.__note.scratchpadImage()
        if not img is None:
            self.__scratchpadHandWritting.loadScratchpadImage(img)

        currentTime=time.time()
        delayCreated=currentTime - self.__note.timestampCreated()
        delayUpdated=currentTime - self.__note.timestampUpdated()

        if delayCreated<1:
            self.lblTimestampLabel.setVisible(False)
            self.lblTimestamp.setVisible(False)
        else:
            self.lblTimestamp.setText(f'{tsToStr(self.__note.timestampCreated())} ({secToStrTime(delayCreated)} ago)\n{tsToStr(self.__note.timestampUpdated())} ({secToStrTime(delayUpdated)} ago)')

        self.btOk.clicked.connect(self.__accept)
        self.btCancel.clicked.connect(self.__reject)

        layout=self.tabScratchpad.layout()
        layout.setSpacing(0)
        layout.setContentsMargins(QMargins(6,6,6,6))
        layout.addWidget(self.__scratchpadHandWritting)

        layout=self.wToolBar.layout()
        layout.setSpacing(6)
        layout.setContentsMargins(QMargins(0,0,0,0))


        self.__actionSelectDefaultBrush=QAction(QIcon(QPixmap.fromImage(self.__allBrushesPreset['b)_Basic-5_Size'].image())), i18n('Default note brush'), self)
        self.__actionSelectDefaultBrush.triggered.connect(self.__actionScratchpadSetBrushDefault)
        self.__actionSelectCurrentBrush=QAction(QIcon(QPixmap.fromImage(self.__activeViewCurrentConfig['brushPreset'].image())), i18n(f"Current painting brush ({self.__activeViewCurrentConfig['brushPreset'].name()})"), self)
        self.__actionSelectCurrentBrush.triggered.connect(self.__actionScratchpadSetBrushCurrent)
        self.__actionSelectBrush=WMenuBrushesPresetSelector()
        self.__actionSelectBrush.presetChooser().presetClicked.connect(self.__actionScratchpadSetBrushPreset)
        self.__actionSelectColor=WMenuColorPicker()
        self.__actionSelectColor.colorPicker().colorUpdated.connect(self.__actionScratchpadSetColor)
        self.__actionSelectColor.colorPicker().setOptionShowColorRGB(False)
        self.__actionSelectColor.colorPicker().setOptionShowColorCMYK(False)
        self.__actionSelectColor.colorPicker().setOptionShowColorHSV(True)
        self.__actionSelectColor.colorPicker().setOptionShowColorHSL(False)
        self.__actionSelectColor.colorPicker().setOptionShowColorAlpha(False)
        self.__actionSelectColor.colorPicker().setOptionCompactUi(True)
        self.__actionSelectColor.colorPicker().setOptionPreviewColor(True)
        self.__actionSelectColor.colorPicker().setOptionShowColorCombination(False)


        menuBrush = QMenu(self.tbBrush)
        menuBrush.addAction(self.__actionSelectDefaultBrush)
        menuBrush.addAction(self.__actionSelectCurrentBrush)
        menuBrush.addAction(self.__actionSelectBrush)

        menuColor = QMenu(self.tbColor)
        menuColor.addAction(self.__actionSelectColor)


        self.tbClear.clicked.connect(self.__actionScratchpadClear)
        self.tbBrush.setMenu(menuBrush)
        self.tbColor.setMenu(menuColor)

        self.hsBrushSize.valueChanged.connect(self.__actionScratchpadSetBrushSize)
        self.hsZoom.valueChanged.connect(self.__actionScratchpadSetZoom)


        self.tvBrushes.doubleClicked.connect(self.__actionBrushEdit)
        self.tvBrushes.setNote(self.__note)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.currentChanged.connect(self.__tabChanged)

        self.__updateBrushUi()

    def showEvent(self, event):
        self.tvBrushes.selectionModel().selectionChanged.connect(self.__brushesSelectionChanged)

    def __tabChanged(self, index):
        """Current tab has been modified"""
        if index==1:
            # handwritten note
            self.__actionScratchpadSetBrushDefault()
        elif index==2:
            # brushes notes
            selectedBrushes=self.tvBrushes.selectedItems()
            if len(selectedBrushes)==1:
                selectedBrushes[0].toBrush()
            else:
                self.__currentUiBrush.toBrush()
            self.tvBrushes.resizeColumns()

    def __updateBrushUi(self):
        """Update brushes UI (enable/disable buttons...)"""
        nbSelectedBrush=self.tvBrushes.nbSelectedItems()
        self.tbBrushAdd.setEnabled(self.__note.brushes().getFromFingerPrint(self.__currentUiBrush.fingerPrint()) is None)
        self.tbBrushEdit.setEnabled(nbSelectedBrush==1)
        self.tbBrushDelete.setEnabled(nbSelectedBrush==1)

    def __brushesSelectionChanged(self, selected, deselected):
        """Selection in treeview has changed, update UI"""
        self.__updateBrushUi()
        selectedBrushes=self.tvBrushes.selectedItems()
        if len(selectedBrushes)==1:
            selectedBrushes[0].toBrush()

    def __saveViewConfig(self):
        """Save current view properties"""
        self.__activeViewCurrentConfig['brushSize']=self.__activeView.brushSize()
        self.__activeViewCurrentConfig['brushPreset']=self.__activeView.currentBrushPreset()

        self.__activeViewCurrentConfig['fgColor']=self.__activeView.foregroundColor()
        self.__activeViewCurrentConfig['bgColor']=self.__activeView.backgroundColor()

        self.__activeViewCurrentConfig['blendingMode']=self.__activeView.currentBlendingMode()
        #self.__activeViewCurrentConfig['gradient']=self.__activeView.currentGradient()
        #self.__activeViewCurrentConfig['pattern']=self.__activeView.currentPattern()

        self.__activeViewCurrentConfig['paintingOpacity']=self.__activeView.paintingOpacity()
        self.__activeViewCurrentConfig['paintingFlow']=self.__activeView.paintingFlow()

        # don't know why, but zoomLevel() and setZoomLevel() don't use same value
        # https://krita-artists.org/t/canvas-class-what-does-zoomlevel-returns-compared-to-setzoomlevel-manual-link-inside/15702/3?u=grum999
        # need to apply a factor to be sure to reapply the right zoom
        self.__activeViewCurrentConfig['zoom']=self.__activeView.canvas().zoomLevel()/(self.__activeView.document().resolution()*1/72)



    def __initViewConfig(self):
        """Initialise view for Scratchpad"""
        self.__actionSelectBrush.presetChooser().setCurrentPreset(self.__allBrushesPreset[self.__note.scratchpadBrushName()])
        self.__activeView.setCurrentBrushPreset(self.__allBrushesPreset[self.__note.scratchpadBrushName()])
        self.__activeView.setForeGroundColor(ManagedColor.fromQColor(self.__note.scratchpadBrushColor(), self.__activeView.canvas()))
        self.__activeView.setBrushSize(self.__note.scratchpadBrushSize())

        self.__actionSelectColor.colorPicker().setColor(self.__note.scratchpadBrushColor())
        self.hsBrushSize.setValue(self.__note.scratchpadBrushSize())



    def __restoreViewConfig(self):
        """Restore view properties"""
        self.__activeView.setCurrentBrushPreset(self.__activeViewCurrentConfig['brushPreset'])
        self.__activeView.setBrushSize(self.__activeViewCurrentConfig['brushSize'])

        self.__activeView.setForeGroundColor(self.__activeViewCurrentConfig['fgColor'])
        self.__activeView.setBackGroundColor(self.__activeViewCurrentConfig['bgColor'])

        self.__activeView.setCurrentBlendingMode(self.__activeViewCurrentConfig['blendingMode'])
        # crash on gradient?
        #self.__activeView.setCurrentGradient(self.__activeViewCurrentConfig['gradient'])
        #self.__activeView.setCurrentPattern(self.__activeViewCurrentConfig['pattern'])

        self.__activeView.setPaintingOpacity(self.__activeViewCurrentConfig['paintingOpacity'])
        self.__activeView.setPaintingFlow(self.__activeViewCurrentConfig['paintingFlow'])

        self.__activeView.canvas().setZoomLevel(self.__activeViewCurrentConfig['zoom'])



    def __accept(self):
        """Accept modifications and return result"""
        self.__note.beginUpdate()
        self.__note.setTitle(self.leTitle.text())
        self.__note.setDescription(self.pteDescription.toPlainText())
        self.__note.setColorIndex(self.wColorIndex.colorIndex())
        self.__note.setText(self.wteText.toHtml())

        self.__note.setScratchpadBrushName(self.__activeView.currentBrushPreset().name())
        self.__note.setScratchpadBrushSize(int(self.__activeView.brushSize()))
        self.__note.setScratchpadBrushColor(self.__activeView.foregroundColor().colorForCanvas(self.__activeView.canvas()))


        img=self.__scratchpadHandWritting.copyScratchpadImageData()
        self.__note.setScratchpadImage(self.__scratchpadHandWritting.copyScratchpadImageData())

        self.__restoreViewConfig()
        self.__note.endUpdate()
        self.accept()


    def __reject(self):
        """reject modifications and return None"""
        self.__restoreViewConfig()
        self.reject()


    def __actionScratchpadSetBrushPreset(self, resource):
        """Set current brush"""
        self.__activeView.setCurrentBrushPreset(resource)
        self.hsBrushSize.setValue(round(self.__activeView.brushSize()))


    def __actionScratchpadClear(self):
        """Clear Scratchpad content"""
        self.__scratchpadHandWritting.clear()


    def __actionScratchpadSetBrushSize(self, value):
        """Set brush size"""
        self.__activeView.setBrushSize(value)


    def __actionScratchpadSetBrushDefault(self):
        """Set brush size"""
        self.__activeView.setCurrentBrushPreset(self.__allBrushesPreset['b)_Basic-5_Size'])
        self.__activeView.setBrushSize(5.0)
        self.__activeView.setCurrentBlendingMode('normal')
        self.__activeView.setPaintingOpacity(1)
        self.__activeView.setPaintingFlow(1)
        self.hsBrushSize.setValue(5)


    def __actionScratchpadSetBrushCurrent(self):
        """Set brush size"""
        self.__activeView.setCurrentBrushPreset(self.__activeViewCurrentConfig['brushPreset'])
        self.__activeView.setBrushSize(self.__activeViewCurrentConfig['brushSize'])
        self.__activeView.setCurrentBlendingMode(self.__activeViewCurrentConfig['blendingMode'])
        self.__activeView.setPaintingOpacity(self.__activeViewCurrentConfig['paintingOpacity'])
        self.__activeView.setPaintingFlow(self.__activeViewCurrentConfig['paintingFlow'])
        self.hsBrushSize.setValue(round(self.__activeViewCurrentConfig['brushSize']))


    def __actionScratchpadSetColor(self, color):
        """Set brush color"""
        self.__activeView.setForeGroundColor(ManagedColor.fromQColor(color, self.__activeView.canvas()))


    def __actionScratchpadSetZoom(self, value):
        """Set zoom value on scratchpad"""
        self.__activeView.canvas().setZoomLevel(value/100.0)


    def __actionBrushScratchpadSetColor(self, color):
        """Set brush testing scrathcpad color"""
        self.__activeView.setForeGroundColor(ManagedColor.fromQColor(color, self.__activeView.canvas()))


    def __actionBrushAdd(self):
        """Add current brush definition to brushes list"""
        result=WTextEditDialog.edit(f"{self.__name}::Brush comment [{self.__currentUiBrush.name()}]", "")
        if not result is None:
            self.__currentUiBrush.setComments(result)
            self.__note.brushes().add(self.__currentUiBrush)
            self.__updateBrushUi()

    def __actionBrushEdit(self):
        """Edit comment for current selected brush"""
        selection=self.tvBrushes.selectedItems()
        if len(selection)==1:
            result=WTextEditDialog.edit(f"{self.__name}::Brush description [{selection[0].name()}]", selection[0].comments())
            if not result is None:
                selection[0].setComments(result)
                self.__updateBrushUi()

    def __actionBrushDelete(self):
        """Add current brush definition to brushes list"""
        selection=self.tvBrushes.selectedItems()
        if len(selection)>0:
            self.__note.brushes().remove(selection)
            self.__updateBrushUi()

    def __actionBrushScratchpadClear(self):
        """Clear Scratchpad content"""
        self.__scratchpadTestBrush.clear()


    def closeEvent(self, event):
        """Dialog is about to be closed..."""
        self.__restoreViewConfig()
        event.accept()


    def note(self):
        """Return current note"""
        return self.__note
