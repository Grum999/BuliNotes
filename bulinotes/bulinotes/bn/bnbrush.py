# -----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2021-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin designed to manage notes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The bnbrush module provides classes used to manage brushes
#
# Main classes from this module
#
# - BNBrushes:
#       Collection of brushes
#
# - BNBrushPreset:
#       Static methods to access to brushes 'securely' (shouldn't fail to get
#       a brush)
#
# - BNBrush:
#       A brush definition (managed by BNBrushes collection)
#
# -----------------------------------------------------------------------------


import struct

from krita import (
        Krita,
        View,
        Resource
    )
from hashlib import blake2b

from bulinotes.pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from bulinotes.pktk.modules.imgutils import qImageToPngQByteArray
from bulinotes.pktk.modules.strutils import stripHtml
from bulinotes.pktk.modules.bytesrw import BytesRW


class BNBrushPreset:
    """Allows 'secured' access to brushes preset

    The main cases:
    - Default brush preset used for notes is not availables
    - Brush preset saved in a BuliNote is not available anymore

    In both case, we need to be able to manage properly acces to resources

    The BNBrushPreset class provides static methods to acces to brushes in 'secure' way

    There's a third case we won't manage (not a normal case, hope this will be fixed)
        https://krita-artists.org/t/second-beta-for-krita-5-0-help-in-testing-krita/30262/19?u=grum999
    """

    # define some brushes preset we can consider to be used as default
    __DEFAUL_BRUSH_NAMES = ['b) Basic-5 Size',
                            'b) Basic-1',
                            'c) Pencil-2',
                            'd) Ink-2 Fineliner',
                            'd) Ink-3 Gpen'
                            ]

    __brushes = None

    @staticmethod
    def initialise():
        """Initialise brushes names"""
        BNBrushPreset.__brushes = Krita.instance().resources("preset")

    @staticmethod
    def getName(name=None):
        """Return preset name from name

        Given `name` can be a <str> or a <Resource> (preset)

        If brush preset is found, return brush preset name
        Otherwise if can't be found in presets, return the default brush name
        """
        if BNBrushPreset.__brushes is None:
            BNBrushPreset.initialise()

        if isinstance(name, Resource):
            name = name.name()

        if name in BNBrushPreset.__brushes:
            # asked brush found, return it
            return name
        else:
            # asked brush not found, search for a default brush
            for brushName in BNBrushPreset.__DEFAUL_BRUSH_NAMES:
                if brushName in BNBrushPreset.__brushes:
                    # default brush found, return it
                    return brushName

            # default brush not found :-/
            # return current brush from view
            brushName = Krita.instance().activeWindow().activeView().currentBrushPreset().name()

            if brushName in BNBrushPreset.__brushes:
                # asked brush found, return it
                return brushName

            # weird..
            # but can happen!
            # https://krita-artists.org/t/second-beta-for-krita-5-0-help-in-testing-krita/30262/19?u=grum999

            if len(BNBrushPreset.__brushes) > 0:
                # return the first one...
                return BNBrushPreset.__brushes[list(BNBrushPreset.__brushes.keys())[0]].name()

            # this case should never occurs I hope!!
            raise EInvalidStatus(f'Something weird happened!\n'
                                 f'- Given brush name "{name}" was not found\n'
                                 f'- Current brush "{brushName}" returned by Krita doesn\'t exist\n'
                                 f'- Brush preset list returned by Krita is empty\n\nCan\'t do anything...')

    @staticmethod
    def getPreset(name=None):
        """Return preset for given name

        Given `name` can be a <str> or a <Resource> (preset)

        If brush preset is found, return brush preset
        Otherwise if can't be found in presets, return the default brush preset
        """
        return BNBrushPreset.__brushes[BNBrushPreset.getName(name)]

    @staticmethod
    def found(name):
        """Return if brush preset (from name) exists and can be used"""
        return BNBrushPreset.getName(name) == name


class BNBrush(QObject):
    """A brush definition"""
    updated = Signal(QObject, str)

    def __init__(self, brush=None):
        super(BNBrush, self).__init__(None)
        self.__name = ''
        self.__size = 0
        self.__flow = 0
        self.__opacity = 0
        self.__blendingMode = ''
        self.__image = None
        self.__comments = ''
        self.__fileName = ''

        self.__uuid = QUuid.createUuid().toString()
        self.__fingerPrint = ''
        self.__emitUpdated = 0

        self.__brushNfoFull = ''
        self.__brushNfoShort = ''

        if isinstance(brush, BNBrush):
            self.importData(brush.exportData())

    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated == 0:
            self.__brushNfoFull = (f'<b>{self.__name.replace("_", " ")}</b>'
                                   f'<small><i><table>'
                                   f' <tr><td align="left"><b>Blending&nbsp;mode:</b></td><td align="right">{self.__blendingMode}</td></tr>'
                                   f' <tr><td align="left"><b>Size:</b></td>         <td align="right">{self.__size:0.2f}px</td></tr>'
                                   f' <tr><td align="left"><b>Opacity:</b></td>      <td align="right">{100*self.__opacity:0.2f}%</td></tr>'
                                   f' <tr><td align="left"><b>Flow:</b></td>         <td align="right">{100*self.__flow:0.2f}%</td></tr>'
                                   f'</table></i></small>'
                                   )

            self.__brushNfoShort = (f'<b>{self.__name.replace("_", " ")}</b>'
                                    f'<small><br><i>{self.__size:0.2f}px - {self.__blendingMode}</i></small>'
                                    )

            self.updated.emit(self, property)

    def beginUpdate(self):
        """Start updating note massivelly and then do note emit update"""
        self.__emitUpdated += 1

    def endUpdate(self):
        """Start updating note massivelly and then do note emit update"""
        self.__emitUpdated -= 1
        if self.__emitUpdated < 0:
            self.__emitUpdated = 0
        elif self.__emitUpdated == 0:
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

        brush = view.currentBrushPreset()

        self.__name = brush.name()
        self.__size = view.brushSize()
        self.__flow = view.paintingFlow()
        self.__opacity = view.paintingOpacity()
        self.__blendingMode = view.currentBlendingMode()
        self.__image = brush.image()

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

        if not self.__name or not BNBrushPreset.found(self.__name):
            return False

        view.setCurrentBrushPreset(BNBrushPreset.getPreset(self.__name))

        view.setBrushSize(self.__size)
        view.setPaintingFlow(self.__flow)
        view.setPaintingOpacity(self.__opacity)
        view.setCurrentBlendingMode(self.__blendingMode)
        return True

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
        dataWrite = BytesRW()
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
            data = bytes(qImageToPngQByteArray(self.__image))
            dataWrite.writeUInt8(len(data))
            dataWrite.write(data)

        returned = dataWrite.getvalue()
        dataWrite.close()

        return returned

    def importData(self, value):
        """Import definition from bytes()"""
        if not isinstance(value, (bytes, QByteArray)):
            return False

        self.beginUpdate()

        dataRead = BytesRW(value)
        dataRead.readUShort()

        self.__name = dataRead.readPStr2()
        self.__size = dataRead.readFloat8()
        self.__flow = dataRead.readFloat8()
        self.__opacity = dataRead.readFloat8()
        self.__blendingMode = dataRead.readPStr2()
        self.__fileName = dataRead.readPStr2()
        self.__comments = dataRead.readPStr2()

        dataLength = dataRead.readUInt8()
        if dataLength > 0:
            self.__image = QImage.fromData(QByteArray(dataRead.read(dataLength)))
        else:
            self.__image = None

        dataRead.close()

        self.endUpdate()

    def name(self):
        """Return brush name"""
        return self.__name

    def setName(self, value):
        """Set name"""
        if value != self.__name:
            self.__name = value
            self.__fingerPrint = ''
            self.__updated('name')

    def size(self):
        """Return brush size"""
        return self.__size

    def setSize(self, value):
        """Set size"""
        if isinstance(value, (int, float)) and value > 0 and self.__size != value:
            self.__size = value
            self.__fingerPrint = ''
            self.__updated('size')

    def flow(self):
        """Return brush flow"""
        return self.__flow

    def setFlow(self, value):
        """Set flow"""
        if isinstance(value, (int, float)) and value >= 0 and value <= 1.0 and self.__flow != value:
            self.__flow = value
            self.__fingerPrint = ''
            self.__updated('flow')

    def opacity(self):
        """Return brush opacity"""
        return self.__opacity

    def setOpacity(self, value):
        """Set opacity"""
        if isinstance(value, (int, float)) and value >= 0 and value <= 1.0 and self.__opacity != value:
            self.__opacity = value
            self.__fingerPrint = ''
            self.__updated('opacity')

    def blendingMode(self):
        """Return blending mode"""
        return self.__blendingMode

    def setBlendingMode(self, value):
        """Set blending mode"""
        if value != self.__blendingMode:
            self.__blendingMode = value
            self.__fingerPrint = ''
            self.__updated('blendingMode')

    def comments(self):
        """Return current comment for brush"""
        return self.__comments

    def setComments(self, value):
        """Set current comment for brush"""
        if value != self.__comments:
            if stripHtml(value).strip() != '':
                self.__comments = value
            else:
                self.__comments = ''
            self.__updated('comments')

    def image(self):
        """Return brush image"""
        return self.__image

    def setImage(self, image):
        """Set brush image"""
        if isinstance(image, QImage) and self.__image != image:
            self.__image = image
            self.__updated('image')

    def id(self):
        """Return unique id"""
        return self.__uuid

    def fingerPrint(self):
        """Return uuid for brush"""
        if self.__fingerPrint == '':
            hash = blake2b()

            hash.update(self.__name.encode())
            hash.update(struct.pack('!d', self.__size))
            hash.update(struct.pack('!d', self.__flow))
            hash.update(struct.pack('!d', self.__opacity))
            hash.update(self.__blendingMode.encode())
            hash.update(self.__fileName.encode())
            self.__fingerPrint = hash.hexdigest()

        return self.__fingerPrint

    def information(self, full=True):
        """Return synthetised brush information (HTML)"""
        if full:
            return self.__brushNfoFull
        else:
            return self.__brushNfoShort

    def exportAsText(self):
        """Return synthetised brush information (Text)"""
        returned = []
        returned.append(f'{self.__name.replace("_", " ")}')
        returned.append(f'- Blending mode: {self.__blendingMode}')
        returned.append(f'- Size:          {self.__size:0.2f}px')
        returned.append(f'- Opacity:       {100*self.__opacity:0.2f}%')
        returned.append(f'- Flow:          {100*self.__flow:0.2f}%')

        if stripHtml(self.__comments) != '':
            returned.append(stripHtml(self.__comments))

        return "\n".join(returned)

    def found(self):
        """Return True if bursh preset exists in krita otherwise False"""
        return BNBrushPreset.found(self.__name)


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

        self.__temporaryDisabled = True

        # list of added hash
        self.__updateAdd = []
        self.__updateRemove = []

        if isinstance(brushes, BNBrushes):
            for brushId in brushes.idList():
                self.add(BNBrush(brushes.get(brushId)))

        self.__temporaryDisabled = False

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
        items = self.__updateAdd.copy()
        self.__updateAdd = []
        if not self.__temporaryDisabled:
            self.updateAdded.emit(items)

    def __emitUpdateRemoved(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items = self.__updateRemove.copy()
        self.__updateRemove = []
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
            if self.__brushes[key].fingerPrint() == fp:
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
        state = self.__temporaryDisabled

        self.__temporaryDisabled = True
        for key in list(self.__brushes.keys()):
            self.remove(self.__brushes[key])
        self.__temporaryDisabled = state
        if not self.__temporaryDisabled:
            self.__emitUpdateReset()

    def add(self, item):
        """Add Brush to list"""
        if isinstance(item, BNBrush):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__brushes[item.id()] = item
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Remove Brush from list"""
        removedBrush = None

        if isinstance(item, list) and len(item) > 0:
            self.__temporaryDisabled = True
            for brush in item:
                self.remove(brush)
            self.__temporaryDisabled = False
            self.__emitUpdateRemoved()
            return True

        if isinstance(item, str) and item in self.__brushes:
            removedBrush = self.__brushes.pop(item, None)
        elif isinstance(item, BNBrush):
            removedBrush = self.__brushes.pop(item.id(), None)

        if removedBrush is not None:
            removedBrush.updated.disconnect(self.__itemUpdated)
            self.__updateRemove.append(removedBrush.id())
            self.__emitUpdateRemoved()
            return True
        return False

    def update(self, item):
        """Update brush"""
        if isinstance(item, BNBrush):
            if self.exists(item.id()):
                self.__notes[item.id()] = item
                self.__itemUpdated(item, '*')
            return True
        return False

    def copyFrom(self, brushes):
        """Copy brushes from another brushes"""
        if isinstance(brushes, BNBrushes):
            self.__temporaryDisabled = True
            self.clear()
            for brushId in brushes.idList():
                self.add(BNBrush(brushes.get(brushId)))
        self.__temporaryDisabled = False
        self.__emitUpdateReset()
