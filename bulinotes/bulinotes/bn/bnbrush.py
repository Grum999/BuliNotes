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

import struct

from krita import View
from hashlib import blake2b

from pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from pktk.modules.utils import (stripHtml, qImageToPngQByteArray)
from pktk.modules.bytesrw import BytesRW


class BNBrush(QObject):
    """A brush definition"""
    updated=Signal(QObject, str)

    def __init__(self, brush=None):
        super(BNBrush, self).__init__(None)
        self.__name=''
        self.__size=0
        self.__flow=0
        self.__opacity=0
        self.__blendingMode=''
        self.__image=None
        self.__comments=''
        self.__fileName=''

        self.__uuid=QUuid.createUuid().toString()
        self.__fingerPrint=''
        self.__emitUpdated=0

        self.__brushNfoFull=''
        self.__brushNfoShort=''

        if isinstance(brush, BNBrush):
            self.importData(brush.exportData())


    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated==0:
            self.__brushNfoFull=(f'<b>{self.__name.replace("_", " ")}</b>'
                                 f'<small><i><table>'
                                 f' <tr><td align="left"><b>Blending&nbsp;mode:</b></td><td align="right">{self.__blendingMode}</td></tr>'
                                 f' <tr><td align="left"><b>Size:</b></td>         <td align="right">{self.__size:0.2f}px</td></tr>'
                                 f' <tr><td align="left"><b>Opacity:</b></td>      <td align="right">{100*self.__opacity:0.2f}%</td></tr>'
                                 f' <tr><td align="left"><b>Flow:</b></td>         <td align="right">{100*self.__flow:0.2f}%</td></tr>'
                                 f'</table></i></small>'
                            )

            self.__brushNfoShort=(f'<b>{self.__name.replace("_", " ")}</b>'
                                  f'<small><br><i>{self.__size:0.2f}px - {self.__blendingMode}</i></small>'
                                )

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


    def fromBrush(self, view=None):
        """Set brush properties from given view

        If no view is provided, use current active view
        """
        if view is None:
            view = Krita.instance().activeWindow().activeView()
            if view is None:
                return False
        elif not isinstance(view, View):
            return False

        self.beginUpdate()

        brush=view.currentBrushPreset()

        self.__name=brush.name()
        self.__size=view.brushSize()
        self.__flow=view.paintingFlow()
        self.__opacity=view.paintingOpacity()
        self.__blendingMode=view.currentBlendingMode()
        self.__image=brush.image()

        self.endUpdate()


        return True

    def toBrush(self, view=None):
        """Set brush properties to given view

        If no view is provided, use current active view
        """
        if view is None:
            view = Krita.instance().activeWindow().activeView()
            if view is None:
                return False
        elif not isinstance(view, View):
            return False

        allBrushesPreset = Krita.instance().resources("preset")
        if not self.__name:
            return False


        view.setCurrentBrushPreset(allBrushesPreset[self.__name])

        view.setBrushSize(self.__size)
        view.setPaintingFlow(self.__flow)
        view.setPaintingOpacity(self.__opacity)
        view.setCurrentBlendingMode(self.__blendingMode)

    def exportData(self):
        """Export brush definition as bytes()

        export format

        size    | format          | description
        (bytes) |                 |
        --------+-----------------+------------------------------
        1       | bytes           | Format version=0x01
        N+2     | PStr2           | Brush name
        8       | Float8          | Brush size (>0)
        8       | Float8          | Brush flow (0.00-100.00)
        8       | Float8          | Brush opacity (0.00-100.00)
        N+2     | PStr2           | Blending mode
        N+2     | PStr2           | Ressource file name
        N+2     | PStr2           | Comments
        8       | UInt8           | Image data size (in bytes)
        N       | bytes           | Image data (PNG)
                |                 |
        """
        dataWrite=BytesRW()
        dataWrite.writeUShort(0x01)
        dataWrite.writePStr2(self.__name)
        dataWrite.writeFloat8(self.__size)
        dataWrite.writeFloat8(self.__flow)
        dataWrite.writeFloat8(self.__opacity)
        dataWrite.writePStr2(self.__blendingMode)
        dataWrite.writePStr2(self.__fileName)
        dataWrite.writePStr2(self.__comments)

        if self.__image is None:
            dataWrite.writeUInt8(0)
        else:
            data=bytes(qImageToPngQByteArray(self.__image))
            dataWrite.writeUInt8(len(data))
            dataWrite.write(data)

        returned=dataWrite.getvalue()
        dataWrite.close()

        return returned

    def importData(self, value):
        """Import definition from bytes()"""
        if not isinstance(value, (bytes, QByteArray)):
            return False

        self.beginUpdate()

        dataRead=BytesRW(value)
        dataRead.readUShort()

        self.__name=dataRead.readPStr2()
        self.__size=dataRead.readFloat8()
        self.__flow=dataRead.readFloat8()
        self.__opacity=dataRead.readFloat8()
        self.__blendingMode=dataRead.readPStr2()
        self.__fileName=dataRead.readPStr2()
        self.__comments=dataRead.readPStr2()

        dataLength=dataRead.readUInt8()
        if dataLength>0:
            self.__image=QImage.fromData(QByteArray(dataRead.read(dataLength)))
        else:
            self.__image=None

        dataRead.close()

        self.endUpdate()


    def name(self):
        """Return brush name"""
        return self.__name

    def setName(self, value):
        """Set name"""
        if value!=self.__name:
            self.__name=value
            self.__fingerPrint=''
            self.__updated('name')

    def size(self):
        """Return brush size"""
        return self.__size

    def setSize(self, value):
        """Set size"""
        if isinstance(value, (int, float)) and value>0 and self.__size!=value:
            self.__size=value
            self.__fingerPrint=''
            self.__updated('size')

    def flow(self):
        """Return brush flow"""
        return self.__flow

    def setFlow(self, value):
        """Set flow"""
        if isinstance(value, (int, float)) and value>=0 and value<=0 and self.__flow!=value:
            self.__flow=value
            self.__fingerPrint=''
            self.__updated('flow')

    def opacity(self):
        """Return brush opacity"""
        return self.__opacity

    def setOpacity(self, value):
        """Set opacity"""
        if isinstance(value, (int, float)) and value>=0 and value<=0 and self.__opacity!=value:
            self.__opacity=value
            self.__fingerPrint=''
            self.__updated('opacity')

    def blendingMode(self):
        """Return blending mode"""
        return self.__blendingMode

    def setBlendingMode(self, value):
        """Set blending mode"""
        if value!=self.__blendingMode:
            self.__blendingMode=value
            self.__fingerPrint=''
            self.__updated('blendingMode')

    def comments(self):
        """Return current comment for brush"""
        return self.__comments

    def setComments(self, value):
        """Set current comment for brush"""
        if value!=self.__comments:
            if stripHtml(value).strip()!='':
                self.__comments=value
            else:
                self.__comments=''
            self.__updated('comments')

    def image(self):
        """Return brush image"""
        return self.__image

    def setImage(self, image):
        """Set brush image"""
        if isinstance(image, QImage) and self.__image!=image:
            self.__image=image
            self.__updated('image')

    def id(self):
        """Return unique id"""
        return self.__uuid

    def fingerPrint(self):
        """Return uuid for brush"""
        if self.__fingerPrint=='':
            hash = blake2b()

            hash.update(self.__name.encode())
            hash.update(struct.pack('!d', self.__size))
            hash.update(struct.pack('!d', self.__flow))
            hash.update(struct.pack('!d', self.__opacity))
            hash.update(self.__blendingMode.encode())
            hash.update(self.__fileName.encode())
            self.__fingerPrint=hash.hexdigest()

        return self.__fingerPrint

    def information(self, full=True):
        """Return synthetised brush information (HTML)"""
        if full:
            return self.__brushNfoFull
        else:
            return self.__brushNfoShort

class BNBrushes(QObject):
    """Collection of brushes"""
    updated = Signal(BNBrush, str)
    updateReset = Signal()
    updateAdded = Signal(list)
    updateRemoved = Signal(list)

    def __init__(self, brushes=None):
        """Initialize object"""
        super(BNBrushes, self).__init__(None)

        # store everything in a dictionary
        # key = id
        # value = BNNotes
        self.__brushes = {}

        self.__temporaryDisabled=True

        # list of added hash
        self.__updateAdd=[]
        self.__updateRemove=[]

        if isinstance(brushes, BNBrushes):
            for brushId in brushes.idList():
                self.add(BNBrush(brushes.get(brushId)))

        self.__temporaryDisabled=False

    def __repr__(self):
        return f"<BNBrushes()>"

    def __itemUpdated(self, item, property):
        """A brush have been updated"""
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

    def length(self):
        """Return number of notes"""
        return len(self.__brushes)

    def idList(self):
        """Return list of id; no sort"""
        return list(self.__brushes.keys())

    def get(self, id):
        """Return brush from id, or None if nothing is found"""
        if id in self.__brushes:
            return self.__brushes[id]
        return None

    def getFromFingerPrint(self, fp):
        """Return brush from fingerPrint, or None if nothing is found"""
        for key in list(self.__brushes.keys()):
            if self.__brushes[key].fingerPrint()==fp:
                return self.__brushes[key]
        return None

    def exists(self, item):
        """Return True if item is already in brushes, otherwise False"""
        if isinstance(item, str):
            return (item in self.__brushes)
        elif isinstance(item, BNBrush):
            return (item.id() in self.__brushes)
        return False

    def clear(self):
        """Clear all brushes"""
        state=self.__temporaryDisabled

        self.__temporaryDisabled=True
        for key in list(self.__brushes.keys()):
            self.remove(self.__brushes[key])
        self.__temporaryDisabled=state
        if not self.__temporaryDisabled:
            self.__emitUpdateReset()

    def add(self, item):
        """Add Brush to list"""
        if isinstance(item, BNBrush):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__brushes[item.id()]=item
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Remove Brush from list"""
        removedBrush=None

        if isinstance(item, list) and len(item)>0:
            self.__temporaryDisabled=True
            for brush in item:
                self.remove(brush)
            self.__temporaryDisabled=False
            self.__emitUpdateRemoved()
            return True

        if isinstance(item, str) and item in self.__brushes:
            removedBrush=self.__brushes.pop(item, None)
        elif isinstance(item, BNBrush):
            removedBrush=self.__brushes.pop(item.id(), None)

        if not removedBrush is None:
            removedBrush.updated.disconnect(self.__itemUpdated)
            self.__updateRemove.append(removedBrush.id())
            self.__emitUpdateRemoved()
            return True
        return False

    def update(self, item):
        """Update brush"""
        if isinstance(item, BNBrush):
            if self.exists(item.id()):
                self.__notes[item.id()]=item
                self.__itemUpdated(item, '*')
            return True
        return False

    def copyFrom(self, brushes):
        """Copy brushes from another brushes"""
        if isinstance(brushes, BNBrushes):
            self.__temporaryDisabled=True
            self.clear()
            for brushId in brushes.idList():
                self.add(BNBrush(brushes.get(brushId)))
        self.__temporaryDisabled=False
        self.__emitUpdateReset()
