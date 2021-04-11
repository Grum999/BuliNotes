#-----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2021 - Grum999
#
# A toolkit to make pykrita plugin coding easier :-)
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

# -----------------------------------------------------------------------------
# Image utilities
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtGui import (
        QBrush,
        QPainter,
        QPixmap,
        QColor
    )

import re

from pktk import *

def warningAreaBrush(size=32):
    """Return a checker board brush"""
    tmpPixmap = QPixmap(size,size)
    tmpPixmap.fill(QColor(255,255,255,32))
    brush = QBrush(QColor(0,0,0,32))

    canvas = QPainter()
    canvas.begin(tmpPixmap)
    canvas.setPen(Qt.NoPen)
    canvas.setBrush(brush)

    s1 = size>>1
    s2 = size - s1

    canvas.setRenderHint(QPainter.Antialiasing, True)
    canvas.drawPolygon(QPolygon([QPoint(s1, 0), QPoint(size, 0), QPoint(0, size), QPoint(0, s1)]))
    canvas.drawPolygon(QPolygon([QPoint(size, s1), QPoint(size, size), QPoint(s1, size)]))
    canvas.end()

    return QBrush(tmpPixmap)

def checkerBoardBrush(size=32):
    """Return a checker board brush"""
    tmpPixmap = QPixmap(size,size)
    tmpPixmap.fill(QColor(255,255,255))
    brush = QBrush(QColor(220,220,220))

    canvas = QPainter()
    canvas.begin(tmpPixmap)
    canvas.setPen(Qt.NoPen)

    s1 = size>>1
    s2 = size - s1

    canvas.setRenderHint(QPainter.Antialiasing, False)
    canvas.fillRect(QRect(0, 0, s1, s1), brush)
    canvas.fillRect(QRect(s1, s1, s2, s2), brush)
    canvas.end()

    return QBrush(tmpPixmap)

def checkerBoardImage(size, checkerSize=32):
    """Return a checker board image"""
    if isinstance(size, int):
        size = QSize(size, size)

    if not isinstance(size, QSize):
        return None

    pixmap = QPixmap(size)
    painter = QPainter()
    painter.begin(pixmap)
    painter.fillRect(pixmap.rect(), checkerBoardBrush(checkerSize))
    painter.end()

    return pixmap

def buildIcon(icons):
    """Return a QIcon from given icons"""
    if isinstance(icons, QIcon):
        return icons
    elif isinstance(icons, list) and len(icons)>0:
        returned = QIcon()

        pixmapList=[]
        for icon in icons:
            if isinstance(icon[0], QPixmap):
                pixmapListItem=[icon[0]]
            elif isinstance(icon[0], str):
                pixmapListItem=[QPixmap(icon[0])]

            for index in range(1,3):
                if index == 1:
                    if len(icon) >= 2:
                        pixmapListItem.append(icon[index])
                    else:
                        pixmapListItem.append(QIcon.Normal)
                elif index == 2:
                    if len(icon) >= 3:
                        pixmapListItem.append(icon[index])
                    else:
                        pixmapListItem.append(QIcon.Off)

            returned.addPixmap(*tuple(pixmapListItem))
        return returned
    elif isinstance(icons, str) and (rfind:=re.match("pktk:(.*)", icons)):
        return buildIcon([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                          (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)])
    else:
        raise EInvalidType("Given `icons` must be a list of tuples")

def qImageToPngQByteArray(image):
    """Convert a QImage as PNG and return a QByteArray"""
    if isinstance(image, QImage):
        ba=QByteArray()
        buffer=QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        return ba
    return b''

def imgBoxSize(imageSize, boxSize):
    """Return size of given `imageSize` to fit within `boxSize`"""
    if not isinstance(imageSize, QSize):
        raise EInvalidType("Given `imageSize` must be a <QSize>")

    if not isinstance(boxSize, QSize):
        raise EInvalidType("Given `boxSize` must be a <QSize>")

    imageRatio=imageSize.width()/imageSize.height()
    boxRatio=boxSize.width()/boxSize.height()

    if boxRatio>imageRatio:
        h=boxSize.height()
        w=h*imageRatio
    else:
        w=boxSize.width()
        h=w/imageRatio

    return QSize(w,h)
