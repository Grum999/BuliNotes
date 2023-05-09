# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The imgutils module provides miscellaneous image functions
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtGui import (
        QBrush,
        QPainter,
        QPixmap,
        QColor
    )

from math import ceil
import re
import pickle

from ..pktk import *


def warningAreaBrush(size=32):
    """Return a checker board brush"""
    tmpPixmap = QPixmap(size, size)
    tmpPixmap.fill(QColor(255, 255, 255, 32))
    brush = QBrush(QColor(0, 0, 0, 32))

    canvas = QPainter()
    canvas.begin(tmpPixmap)
    canvas.setPen(Qt.NoPen)
    canvas.setBrush(brush)

    s1 = size >> 1
    s2 = size - s1

    canvas.setRenderHint(QPainter.Antialiasing, True)
    canvas.drawPolygon(QPolygon([QPoint(s1, 0), QPoint(size, 0), QPoint(0, size), QPoint(0, s1)]))
    canvas.drawPolygon(QPolygon([QPoint(size, s1), QPoint(size, size), QPoint(s1, size)]))
    canvas.end()

    return QBrush(tmpPixmap)


def checkerBoardBrush(size=32, color1=QColor(255, 255, 255), color2=QColor(220, 220, 220), strictSize=True):
    """Return a checker board brush"""
    s1 = size >> 1
    if strictSize:
        s2 = size - s1
    else:
        s2 = s1

    size = s1+s2

    tmpPixmap = QPixmap(size, size)
    tmpPixmap.fill(color1)
    brush = QBrush(color2)

    canvas = QPainter()
    canvas.begin(tmpPixmap)
    canvas.setPen(Qt.NoPen)

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


def bullet(size=16, color=QColor(255, 255, 255), shape='square', scaleShape=1.0):
    """Draw a bullet and return it as a QPixmap

    Given `size` define size of pixmap (width=height)
    Given `color` define color bullet
    Given `shape` define bullet shape ('circle' or 'square')
    Given `scaleShape` define size of bullet in pixmap (1.0 = 100% / 0.5=50% for example)
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    canvas = QPainter()
    canvas.begin(pixmap)
    canvas.setPen(Qt.NoPen)

    shapeWidth = size*scaleShape
    offset = (size-shapeWidth)/2

    if shape == 'square':
        canvas.fillRect(QRectF(offset, offset, shapeWidth, shapeWidth, color))
    elif shape == 'roundSquare':
        canvas.setBrush(color)
        canvas.drawRoundedRect(QRectF(offset, offset, shapeWidth, shapeWidth), 25, 25, Qt.RelativeSize)
    elif shape == 'circle':
        canvas.setBrush(color)
        canvas.drawEllipse(QRectF(offset, offset, shapeWidth, shapeWidth))
    else:
        raise EInvalidValue("Given `shape` value is not valid")

    canvas.end()
    return pixmap


def paintOpaqueAsColor(pixmap, color):
    """From given pixmap, non transparent color are replaced with given color"""
    if isinstance(pixmap, QPixmap):
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(),  color)
    return pixmap


def buildIcon(icons, size=None):
    """Return a QIcon build from given icons


    Given `icons` can be:
    - A string "pktk:XXXX"
        Where XXXX is name of a PkTk icon
        Return QIcon() will provide normal/disable icons
    - A list of tuple
        Each tuple can be:
            (QPixmap, )
            (QPixmap, QIcon.Mode)
            (QPixmap, QIcon.Mode, QIcon.State)
            (str, )
            (str, QIcon.Mode)
            (str, QIcon.Mode, QIcon.State)

    If provided, given `size` can be an <int> or an <QSize>
    """
    if isinstance(icons, QIcon):
        return icons
    elif isinstance(icons, list) and len(icons) > 0:
        returned = QIcon()

        if isinstance(size, int):
            appliedSize = QSize(size, size)
        elif isinstance(size, QSize):
            appliedSize = size
        else:
            appliedSize = QSize()

        for icon in icons:
            addPixmap = False
            if isinstance(icon[0], QPixmap):
                addPixmap = True
                iconListItem = [icon[0]]
            elif isinstance(icon[0], str):
                iconListItem = [icon[0], appliedSize]
            else:
                continue

            for index in range(1, 3):
                if index == 1:
                    if len(icon) >= 2:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Normal)
                elif index == 2:
                    if len(icon) >= 3:
                        iconListItem.append(icon[index])
                    else:
                        iconListItem.append(QIcon.Off)

            if addPixmap:
                returned.addPixmap(*tuple(iconListItem))
            else:
                returned.addFile(*tuple(iconListItem))
        return returned
    elif isinstance(icons, str) and (rfind := re.match("pktk:(.*)", icons)):
        return buildIcon([(f':/pktk/images/normal/{rfind.groups()[0]}', QIcon.Normal),
                          (f':/pktk/images/disabled/{rfind.groups()[0]}', QIcon.Disabled)], size)
    else:
        raise EInvalidType("Given `icons` must be a <str> or a <list> of <tuples>")


def qImageToPngQByteArray(image):
    """Convert a QImage as PNG and return a QByteArray"""
    if isinstance(image, QImage):
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        return ba
    return QByteArray()


def imgBoxSize(imageSize, boxSize):
    """Return size of given `imageSize` to fit within `boxSize`"""
    if not isinstance(imageSize, QSize):
        raise EInvalidType("Given `imageSize` must be a <QSize>")

    if not isinstance(boxSize, QSize):
        raise EInvalidType("Given `boxSize` must be a <QSize>")

    imageRatio = imageSize.width()/imageSize.height()
    boxRatio = boxSize.width()/boxSize.height()

    if boxRatio > imageRatio:
        h = boxSize.height()
        w = h*imageRatio
    else:
        w = boxSize.width()
        h = w/imageRatio

    return QSize(w, h)


def combineChannels(bytesPerChannel, *channels):
    """Combine given channels

    Given `bytesPerChannel` define how many byte are used for one pixel in channels
    Given `channels` are bytes or bytesarray (or memory view on bytes/bytearray)

    Return a bytearray

    Example:
        bytes per channel = 1
        channels =  red=[0xff, 0x01, 0x02]
                    green=[0x03, 0xff, 0x04]
                    blue=[0x05, 0x06, 0xff]

        returned byte array will be
        (0xff, 0x03, 0x05,
         0x01, 0xff, 0x06,
         0x02, 0x06, 0xff)
    """
    # First, need to ensure that all channels have the same size
    channelSize = None
    for channel in channels:
        if channelSize is None:
            channelSize = len(channel)
        elif channelSize != len(channel):
            raise EInvalidValue("All `channels` must have the same size")

    channelCount = len(channels)
    offsetTargetInc = channelCount*bytesPerChannel
    targetSize = channelSize*offsetTargetInc
    target = bytearray(targetSize)

    channelNumber = 0
    for channel in channels:
        offsetTarget = channelNumber*bytesPerChannel
        offsetSource = 0
        for index in range(channelSize//bytesPerChannel):
            target[offsetTarget] = channel[offsetSource]
            offsetTarget += offsetTargetInc
            offsetSource += bytesPerChannel
        channelNumber += 1

    return target


def convertSize(value, fromUnit, toUnit, resolution, roundValue=None):
    """Return converted `value` from given `fromUnit` to `toUnit`, using given `resolution` (if unit conversion implies px)

    Given `fromUnit` and `toUnit` can be:
        px: pixels
        mm: millimeters
        cm: centimeters
        in: inchs

    Given `fromUnit` can also be provided as 'pt' (points)

    The `roundValue` allows to define number of decimals for conversion
    If None is provided, according to `toUnit`:
        px: 0
        mm: 0
        cm: 2
        in: 4
    """
    if roundValue is None:
        if toUnit == 'in':
            roundValue = 4
        elif toUnit == 'cm':
            roundValue = 2
        else:
            roundValue = 0

    if resolution == 0:
        # avoid division by zero
        resolution = 1.0

    if fromUnit == 'mm':
        if toUnit == 'cm':
            return round(value/10, roundValue)
        elif toUnit == 'in':
            return round(value/25.4, roundValue)
        elif toUnit == 'px':
            return round(convertSize(value, fromUnit, 'in', resolution) * resolution, roundValue)
    elif fromUnit == 'cm':
        if toUnit == 'mm':
            return round(value*10, roundValue)
        elif toUnit == 'in':
            return round(value/2.54, roundValue)
        elif toUnit == 'px':
            return round(convertSize(value, fromUnit, 'in', resolution) * resolution, roundValue)
    elif fromUnit == 'in':
        if toUnit == 'mm':
            return round(value*25.4, roundValue)
        elif toUnit == 'cm':
            return round(value*2.54, roundValue)
        elif toUnit == 'px':
            return round(value * resolution, roundValue)
    elif fromUnit == 'px':
        if toUnit == 'mm':
            return round(convertSize(value, fromUnit, 'in', resolution)*25.4, roundValue)
        elif toUnit == 'cm':
            return round(convertSize(value, fromUnit, 'in', resolution)*2.54, roundValue)
        elif toUnit == 'in':
            return round(value / resolution, roundValue)
    elif fromUnit == 'pt':
        if toUnit == 'mm':
            return round(value * 0.35277777777777775, roundValue)   # 25.4/72
        elif toUnit == 'cm':
            return round(value * 0.035277777777777775, roundValue)  # 2.54/72
        elif toUnit == 'in':
            return round(value / 72, roundValue)
        elif toUnit == 'px':
            return round(resolution * convertSize(value, fromUnit, 'in', resolution)/72, roundValue)
    # all other combination are not valid, return initial value
    return value


def megaPixels(value, roundDec=2):
    """return value (in pixels) as megapixels rounded to given number of decimal"""
    if value is None or value == 0:
        return ""
    if value < 100000:
        return f"{ceil(value/10000)/100:.0{roundDec}f}"
    return f"{ceil(value/100000)/10:.0{roundDec}f}"


def ratioOrientation(ratio):
    """return ratio text for a given ratio value"""
    if ratio is None:
        return ""
    elif ratio < 1:
        return i18n("Portrait")
    elif ratio > 1:
        return i18n("Landscape")
    else:
        return i18n("Square")


class QIconPickable(QIcon):
    """A QIcon class that is serializable from pickle"""
    def __reduce__(self):
        return type(self), (), self.__getstate__()

    def __getstate__(self):
        ba = QByteArray()
        stream = QDataStream(ba, QIODevice.WriteOnly)
        stream << self
        return ba

    def __setstate__(self, ba):
        stream = QDataStream(ba, QIODevice.ReadOnly)
        stream >> self
