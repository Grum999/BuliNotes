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
import os.path

from bulinotes.pktk import *
from krita import (Node, Document)

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from bulinotes.pktk.modules.fontdb import (Font, FontDatabase)
from bulinotes.pktk.modules.strutils import stripHtml
from bulinotes.pktk.modules.bytesrw import BytesRW
from bulinotes.pktk.modules.ekrita import EKritaNode


class BNEmbeddedFont(QObject):
    """An embedded font definition"""
    updated=Signal(QObject, str)

    def __init__(self, source=None):
        super(BNEmbeddedFont, self).__init__(None)
        self.__name=''
        self.__fontList=[]

        self.__emitUpdated=0

        if isinstance(source, BNEmbeddedFont):
            # import from another embedded font object
            self.importData(source.exportData())
        elif isinstance(source, str):
            # import from font name
            self.__name=source
            self.__fontList=FontDatabase.font(self.__name)

    def __repr__(self):
        return f"<BNEmbeddedFont({self.__name}, {len(self.__fontList)}, {self.__fontList})>"

    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated==0:
            self.updated.emit(self, property)

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

    def exportData(self):
        """Export embedded font definition as bytes()

        export format

        size    | format          | description
        (bytes) |                 |
        --------+-----------------+------------------------------
        1       | bytes           | Format version=0x01
        N+2     | PStr2           | embedded font Name
        4       | UInt4           | number of embedded font files
                |                 |
                |                 | -- for each embedded font file --
        N+2     | PStr2           | font file name (without path)
        8       | UInt8           | font file size (in bytes)
        N       | bytes           | font file data
                |                 |
        """
        dataWrite=BytesRW()
        dataWrite.writeUShort(0x01)
        dataWrite.writePStr2(self.__name)

        if len(self.__fontList) is None:
            dataWrite.writeUInt4(0)
        else:
            dataWrite.writeUInt4(len(self.__fontList))

            for font in self.__fontList:
                fileContent=font.getFileContent()

                if fileContent!=b'':
                    dataWrite.writePStr2(os.path.basename(font.fileName()))
                    dataWrite.writeUInt8(len(fileContent))
                    dataWrite.write(fileContent)

        returned=dataWrite.getvalue()
        dataWrite.close()

        return returned

    def importData(self, value):
        """Import definition from bytes()"""
        if not isinstance(value, (bytes, QByteArray)):
            return False

        self.__fontList=[]

        self.beginUpdate()

        dataRead=BytesRW(value)
        dataRead.readUShort()

        self.__name=dataRead.readPStr2()

        nbFontFiles=dataRead.readUInt4()

        for fontFileNumber in range(nbFontFiles):
            fileName=dataRead.readPStr2()
            fileSize=dataRead.readUInt8()
            fileContent=dataRead.read(fileSize)

            self.__fontList.append(Font(fileName, fileContent))

        dataRead.close()

        self.endUpdate()

    def name(self):
        """Return embedded font name"""
        return self.__name

    def id(self):
        """Return embedded font id (name)"""
        return self.__name

    def fonts(self):
        """Return list of Font objects"""
        return self.__fontList

    def exportAsText(self):
        """Return synthetised embedded font information (Text)"""
        returned=[]
        returned.append(f'{self.__name}')
        #returned.append(stripHtml(''))

        return "\n".join(returned)



class BNEmbeddedFonts(QObject):
    """Collection of embedded fonts"""
    updated = Signal(BNEmbeddedFont, str)
    updateReset = Signal()
    updateAdded = Signal(list)
    updateRemoved = Signal(list)

    def __init__(self, embeddedFonts=None):
        """Initialize object"""
        super(BNEmbeddedFonts, self).__init__(None)

        # store everything in a dictionary
        # key = id (font name)
        # value = BNEmbeddedFont
        self.__embeddedFonts = {}

        self.__inUpdate=1

        # list of added hash
        self.__updateAdd=[]
        self.__updateRemove=[]

        if isinstance(embeddedFonts, BNEmbeddedFonts):
            for embeddedFontId in embeddedFonts.idList():
                self.add(BNEmbeddedFont(embeddedFonts.get(embeddedFontId)))

        self.__inUpdate=0

    def __repr__(self):
        return f"<BNEmbeddedFonts({self.length()})>"

    def __itemUpdated(self, item, property):
        """A embedded font have been updated"""
        if self.__inUpdate==0:
            self.updated.emit(item, property)

    def __emitUpdateReset(self):
        """List have been cleared/loaded"""
        if self.__inUpdate==0:
            self.updateReset.emit()

    def __emitUpdateAdded(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items=self.__updateAdd.copy()
        self.__updateAdd=[]
        if self.__inUpdate==0:
            self.updateAdded.emit(items)

    def __emitUpdateRemoved(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items=self.__updateRemove.copy()
        self.__updateRemove=[]
        if self.__inUpdate==0:
            self.updateRemoved.emit(items)

    def length(self):
        """Return number of embedded fonts"""
        return len(self.__embeddedFonts)

    def idList(self):
        """Return list of id; no sort"""
        return list(self.__embeddedFonts.keys())

    def get(self, id):
        """Return embedded font from id (name), or None if nothing is found"""
        if id in self.__embeddedFonts:
            return self.__embeddedFonts[id]
        return None

    def exists(self, item):
        """Return True if item is already in embeddedFonts, otherwise False"""
        if isinstance(item, str):
            return (item in self.__embeddedFonts)
        elif isinstance(item, BNEmbeddedFont):
            return (item.id() in self.__embeddedFonts)
        return False

    def clear(self):
        """Clear all embeddedFonts"""
        self.beginUpdate()

        for key in list(self.__embeddedFonts.keys()):
            self.remove(self.__embeddedFonts[key])

        self.endUpdate()

    def add(self, item):
        """Add embedded font to list"""
        if isinstance(item, BNEmbeddedFont):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__embeddedFonts[item.id()]=item
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Remove embedded font from list"""
        removedEmbeddedFont=None

        if isinstance(item, list) and len(item)>0:
            self.beginUpdate()
            for embeddedFont in item:
                self.remove(embeddedFont)
            self.endUpdate()
            return True

        if isinstance(item, str) and item in self.__embeddedFonts:
            removedEmbeddedFont=self.__embeddedFonts.pop(item, None)
        elif isinstance(item, BNEmbeddedFont):
            removedEmbeddedFont=self.__embeddedFonts.pop(item.id(), None)

        if not removedEmbeddedFont is None:
            try:
                removedEmbeddedFont.updated.disconnect(self.__itemUpdated)
            except:
                # ignore case if there wasn't connection
                pass
            self.__updateRemove.append(removedEmbeddedFont.id())
            self.__emitUpdateRemoved()
            return True
        return False

    def update(self, item):
        """Update embedded font"""
        if isinstance(item, BNEmbeddedFont):
            if self.exists(item.id()):
                self.__embeddedFonts[item.id()]=item
                self.__itemUpdated(item, '*')
            return True
        return False

    def copyFrom(self, embeddedFonts):
        """Copy embeddedFonts from another embeddedFonts"""
        if isinstance(embeddedFonts, BNEmbeddedFonts):
            self.beginUpdate()
            self.clear()
            for embeddedFontId in embeddedFonts.idList():
                self.add(BNEmbeddedFont(embeddedFonts.get(embeddedFontId)))
        self.endUpdate()

    def beginUpdate(self):
        """Start to update model content, avoid to emit change signals"""
        self.__inUpdate+=1

    def endUpdate(self):
        """End to update model content, emit change signals"""
        self.__inUpdate-=1
        if self.__inUpdate<0:
            self.__inUpdate=0
        elif self.__inUpdate==0:
            self.__emitUpdateReset()
