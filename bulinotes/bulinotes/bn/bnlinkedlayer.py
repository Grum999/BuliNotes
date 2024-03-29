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
# The bnlinkedlayer module provides classes used to manage link between documents
# layers and notes
#
# Main classes from this module
#
# - BNLinkedLayers:
#       Collection of linked layers
#
# - BNLinkedLayer:
#       A linked layer definition (managed by BNLinkedLayers collection)
#
# -----------------------------------------------------------------------------

import os.path

from bulinotes.pktk import *
from krita import (Node, Document)

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from bulinotes.pktk.modules.imgutils import qImageToPngQByteArray
from bulinotes.pktk.modules.strutils import stripHtml
from bulinotes.pktk.modules.bytesrw import BytesRW
from bulinotes.pktk.modules.ekrita import EKritaNode


class BNLinkedLayer(QObject):
    """A linked layer definition"""
    updated = Signal(QObject, str)

    THUMB_SIZE = 192

    def __init__(self, linkedLayer=None):
        super(BNLinkedLayer, self).__init__(None)
        self.__name = ''
        self.__comments = ''
        self.__uuid = None
        self.__thumbnail = None

        self.__emitUpdated = 0

        if isinstance(linkedLayer, BNLinkedLayer):
            self.importData(linkedLayer.exportData())

    def __repr__(self):
        return f"<BNLinkedLayer({self.__uuid}, {self.__name})>"

    def __updated(self, property):
        """Emit updated signal when a property has been changed"""
        if self.__emitUpdated == 0:
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

    def fromLayer(self, nodeRef):
        """Set linked layer properties from given view

        If no view is provided, use current active view
        """
        if isinstance(nodeRef, QUuid):
            document = Krita.instance().activeDocument()
            node = document.nodeByUniqueID(nodeRef)
            if node is None:
                return False
        elif isinstance(nodeRef, Node):
            node = nodeRef
        else:
            return False

        self.beginUpdate()

        self.setName(node.name())
        self.__uuid = QUuid(node.uniqueId())

        image = EKritaNode.toQImage(node)
        if image:
            self.setThumbnail(image.scaled(QSize(BNLinkedLayer.THUMB_SIZE, BNLinkedLayer.THUMB_SIZE), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.__thumbnail = None

        self.endUpdate()

        return True

    def exportData(self):
        """Export linked layer definition as bytes()

        export format

        size    | format          | description
        (bytes) |                 |
        --------+-----------------+------------------------------
        1       | bytes           | Format version=0x01
        N+2     | PStr2           | Linked layer UUID '{xxx-...-xxx}'
        N+2     | PStr2           | Linked layer Name
        N+2     | PStr2           | Comments
        8       | UInt8           | Thumbnail data size (in bytes)
        N       | bytes           | Thumbnail data (PNG)
                |                 |
        """
        dataWrite = BytesRW()
        dataWrite.writeUShort(0x01)
        if self.__uuid is None:
            dataWrite.writePStr2('')
        else:
            dataWrite.writePStr2(self.__uuid.toString())
        dataWrite.writePStr2(self.__name)
        dataWrite.writePStr2(self.__comments)

        if self.__thumbnail is None:
            dataWrite.writeUInt8(0)
        else:
            data = bytes(qImageToPngQByteArray(self.__thumbnail))
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

        uuid = dataRead.readPStr2()
        if uuid == '':
            self.__uuid = None
        else:
            self.__uuid = QUuid(uuid)
        self.__name = dataRead.readPStr2()
        self.__comments = dataRead.readPStr2()

        dataLength = dataRead.readUInt8()
        if dataLength > 0:
            self.__thumbnail = QImage.fromData(QByteArray(dataRead.read(dataLength)))
        else:
            self.__image = None

        dataRead.close()

        self.endUpdate()

    def name(self):
        """Return linked layer name"""
        return self.__name

    def setName(self, value):
        """Set linked layer name"""
        if value != self.__name:
            self.__name = value
            self.__updated('name')

    def comments(self):
        """Return current comment for linked layer"""
        return self.__comments

    def setComments(self, value):
        """Set current comment for linked layer"""
        if value != self.__comments:
            if stripHtml(value).strip() != '':
                self.__comments = value
            else:
                self.__comments = ''
            self.__updated('comments')

    def thumbnail(self):
        """Return linked layer image"""
        return self.__thumbnail

    def setThumbnail(self, thumbnail):
        """Set linked layer thumbnail"""
        if thumbnail is None or isinstance(thumbnail, QImage) and self.__thumbnail != thumbnail:
            self.__thumbnail = thumbnail
            self.__updated('thumbnail')

    def id(self):
        """Return linked layer unique id"""
        return self.__uuid

    def updateFromDocument(self, document=None):
        """Update name and thumbnail from given `document`

        If `document` is None, do update from current active document

        If there's no active document or if layer is not found, does nothing
        """
        if document is None:
            document = Krita.instance().activeDocument()

        if not isinstance(document, Document):
            return

        self.fromLayer(self.__uuid)

    def exportAsText(self):
        """Return synthetised brush information (Text)"""
        returned = []
        returned.append(f'{self.__name}')
        returned.append(stripHtml(self.__comments))

        return "\n".join(returned)


class BNLinkedLayers(QObject):
    """Collection of linked layers"""
    updated = Signal(BNLinkedLayer, str)
    updateReset = Signal()
    updateAdded = Signal(list)
    updateRemoved = Signal(list)

    def __init__(self, linkedLayers=None):
        """Initialize object"""
        super(BNLinkedLayers, self).__init__(None)

        # store everything in a dictionary
        # key = id
        # value = BNNotes
        self.__linkedLayers = {}

        self.__inUpdate = 1

        # list of added hash
        self.__updateAdd = []
        self.__updateRemove = []

        if isinstance(linkedLayers, BNLinkedLayers):
            for linkedLayerId in linkedLayers.idList():
                self.add(BNLinkedLayer(linkedLayers.get(linkedLayerId)))

        self.__inUpdate = 0

    def __repr__(self):
        return f"<BNLinkedLayers({self.length()})>"

    def __itemUpdated(self, item, property):
        """A linked layer have been updated"""
        if self.__inUpdate == 0:
            self.updated.emit(item, property)

    def __emitUpdateReset(self):
        """List have been cleared/loaded"""
        if self.__inUpdate == 0:
            self.updateReset.emit()

    def __emitUpdateAdded(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items = self.__updateAdd.copy()
        self.__updateAdd = []
        if self.__inUpdate == 0:
            self.updateAdded.emit(items)

    def __emitUpdateRemoved(self):
        """Emit update signal with list of id to update

        An empty list mean a complete update
        """
        items = self.__updateRemove.copy()
        self.__updateRemove = []
        if self.__inUpdate == 0:
            self.updateRemoved.emit(items)

    def length(self):
        """Return number of notes"""
        return len(self.__linkedLayers)

    def idList(self):
        """Return list of id; no sort"""
        return list(self.__linkedLayers.keys())

    def get(self, id):
        """Return linked layer from id, or None if nothing is found"""
        if id in self.__linkedLayers:
            return self.__linkedLayers[id]
        return None

    def exists(self, item):
        """Return True if item is already in linkedLayers, otherwise False"""
        if isinstance(item, QUuid):
            return (item in self.__linkedLayers)
        elif isinstance(item, BNLinkedLayer):
            return (item.id() in self.__linkedLayers)
        return False

    def clear(self):
        """Clear all linkedLayers"""
        self.beginUpdate()

        for key in list(self.__linkedLayers.keys()):
            self.remove(self.__linkedLayers[key])

        self.endUpdate()

    def add(self, item):
        """Add linked layer to list"""
        if isinstance(item, BNLinkedLayer):
            item.updated.connect(self.__itemUpdated)
            self.__updateAdd.append(item.id())
            self.__linkedLayers[item.id()] = item
            self.__emitUpdateAdded()
            return True
        return False

    def remove(self, item):
        """Remove linked layer from list"""
        removedLinkedLayer = None

        if isinstance(item, list) and len(item) > 0:
            self.beginUpdate()
            for linkedLayer in item:
                self.remove(linkedLayer)
            self.endUpdate()
            return True

        if isinstance(item, QUuid) and item in self.__linkedLayers:
            removedLinkedLayer = self.__linkedLayers.pop(item, None)
        elif isinstance(item, BNLinkedLayer):
            removedLinkedLayer = self.__linkedLayers.pop(item.id(), None)

        if removedLinkedLayer is not None:
            try:
                removedLinkedLayer.updated.disconnect(self.__itemUpdated)
            except Exception:
                # ignore case if there wasn't connection
                pass
            self.__updateRemove.append(removedLinkedLayer.id())
            self.__emitUpdateRemoved()
            return True
        return False

    def update(self, item):
        """Update linked layer"""
        if isinstance(item, BNLinkedLayer):
            if self.exists(item.id()):
                self.__linkedLayers[item.id()] = item
                self.__itemUpdated(item, '*')
            return True
        return False

    def copyFrom(self, linkedLayers):
        """Copy linkedLayers from another linkedLayers"""
        if isinstance(linkedLayers, BNLinkedLayers):
            self.beginUpdate()
            self.clear()
            for linkedLayerId in linkedLayers.idList():
                self.add(BNLinkedLayer(linkedLayers.get(linkedLayerId)))
        self.endUpdate()

    def updateFromDocument(self, document=None):
        """Update name and thumbnail from given `document` for all layers

        If `document` is None, do update from current active document

        If there's no active document or if a layer is not found, does nothing
        """
        if document is None:
            document = Krita.instance().activeDocument()

        if not isinstance(document, Document):
            return

        self.beginUpdate()

        for key in list(self.__linkedLayers.keys()):
            self.__linkedLayers[key].updateFromDocument(document)

        self.endUpdate()

    def beginUpdate(self):
        """Start to update model content, avoid to emit change signals"""
        self.__inUpdate += 1

    def endUpdate(self):
        """End to update model content, emit change signals"""
        self.__inUpdate -= 1
        if self.__inUpdate < 0:
            self.__inUpdate = 0
        elif self.__inUpdate == 0:
            self.__emitUpdateReset()
