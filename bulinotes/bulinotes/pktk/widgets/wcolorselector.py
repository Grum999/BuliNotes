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


import math
import re

from krita import (
        Krita,
        Palette,
        Swatch
    )
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtGui import (
        QColor,
        QImage,
        QPixmap,
    )
from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QLabel,
        QHBoxLayout
    )

from pktk.modules.utils import (checkerBoardImage, checkerBoardBrush)

# todo:
#   * Fix management with CMYK colorspace
#       - On a CMYK document, selecting a color is buggy (cursor is repositionned on each move)
#
#   * WColorWheel
#       - Implement INNER_MODE
#
#   * WColorPicker
#       - Last used colors (X last color)
#       - Load from palette
#       - WebColor (#rrggbb|#rrggbbaa|rgb(255,255,255)|rgba(255,255,255,255)| +floating mode 0.00-1.00  )
#


class WColorWheel(QWidget):
    """A basic color wheel"""
    colorUpdated = Signal(QColor)       # when color is changed from user interface
    colorChanged = Signal(QColor)       # when color is changed programmatically

    # The 6 main color on hue wheel
    __HUE_COLORS=[
            (0, Qt.red),
            (1/6, Qt.yellow),       # 60°
            (1/3, Qt.green),        # 120°
            (0.5, Qt.cyan),         # 180°
            (2/3, Qt.blue),         # 240°
            (5/6, Qt.magenta),      # 300°
            (1, Qt.red)
        ]

    __UPDATE_MODE_NONE = 0
    __UPDATE_MODE_HUE = 1
    __UPDATE_MODE_HUE_CONSTRAINED = 2
    __UPDATE_MODE_INNER = 3
    __UPDATE_MODE_OVER_COLOR_PREVIEW = 4

    __INNER_MODE_HSV_SQ = 0
    __INNER_MODE_HSL_SQ = 1
    __INNER_MODE_HSV_TR = 2


    def __init__(self, color=None, parent=None):
        super(WColorWheel, self).__init__(parent)

        # options
        self.__optionAntialiasing=True
        self.__optionBorderWidth=0
        self.__optionBorderColor=QColor(Qt.black)
        self.__optionWheelWidthMin=8
        self.__optionWheelWidthMax=28
        self.__optionTracking=True
        self.__optionPreviewColor=True
        self.__optionInnerModel=WColorWheel.__INNER_MODE_HSV_SQ

        # properties
        self.__propAlpha=255
        self.__propColor=QColor(Qt.red)
        self.__propColorHue=QColor(Qt.red)

        # pixmap cache
        self.__pixmapColorWheel=None
        self.__pixmapColorInner=None

        # regions
        self.__regionColorWheel=None
        self.__regionColorInner=None
        self.__regionColorPreview=None

        # internal calculated values used to render widget
        self.__hWidth=0
        self.__hHeight=0

        self.__borderLength=0.0
        self.__outerRect=QRect()
        self.__middleRect=QRect()
        self.__innerRect=QRect()
        self.__showColorRect=QRect()

        self.__outerPosition=QPoint()
        self.__innerPosition=QPoint()

        self.__wheelWidth=18

        # -- technical

        self.__checkerBoardBrush=checkerBoardBrush()

        # current update mode
        self.__updateMode=WColorWheel.__UPDATE_MODE_NONE

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMouseTracking(True)
        self.setColor(color)

    def resizeEvent(self, event):
        """Widget is resized, need to recalculate properties depending of widget dimensions"""
        self.__calculateFromSize()

    def paintEvent(self, event):
        """refresh widget content"""
        painter = QPainter(self)

        if self.__optionAntialiasing:
            # if antialiased, set it active
            painter.setRenderHint(QPainter.Antialiasing)

        # draw final color
        if self.__optionPreviewColor:
            self.__drawColorPreview(painter)
            if self.__updateMode==WColorWheel.__UPDATE_MODE_OVER_COLOR_PREVIEW:
                # on preview mode 'over', all area is set with color
                return

        if self.__pixmapColorWheel is None:
            # color wheel has been removed from cache, need to regenerate it
            self.__buildPixmapColorWheel()

        if self.__pixmapColorInner is None:
            # inner color has been removed from cache, need to regenerate it
            self.__buildPixmapColorInner()

        # draw color wheel
        painter.drawPixmap(self.__outerPosition, self.__pixmapColorWheel)

        # draw inner color
        painter.fillRect(QRect(self.__innerPosition, self.__innerRect.size()), self.__propColorHue)
        painter.drawPixmap(self.__innerPosition, self.__pixmapColorInner)

        # draw cursor position (inner color)
        self.__drawCursorCircleColorInner(painter)

        # draw cursor position (color wheel)
        self.__drawCursorCircleColorWheel(painter)

    def mousePressEvent(self, event):
        """A mouse button is clicked on widget"""
        self.__updateMode=WColorWheel.__UPDATE_MODE_NONE
        if Qt.LeftButton and event.buttons() == Qt.LeftButton:
            if self.__regionColorWheel.contains((event.localPos() - self.__outerPosition).toPoint()):
                if Qt.ControlModifier & int(event.modifiers()) == Qt.ControlModifier:
                    self.__updateMode=WColorWheel.__UPDATE_MODE_HUE_CONSTRAINED
                else:
                    self.__updateMode=WColorWheel.__UPDATE_MODE_HUE
            elif self.__regionColorInner.contains((event.localPos() - self.__innerPosition).toPoint()):
                self.__updateMode=WColorWheel.__UPDATE_MODE_INNER

            self.__updateMouseCursor(event.localPos(), False)

    def mouseReleaseEvent(self, event):
        """A mouse button is clicked on widget"""
        if self.__updateMode!=WColorWheel.__UPDATE_MODE_NONE:
            self.__updateMode=WColorWheel.__UPDATE_MODE_NONE
            self.__updateMouseCursor(event.localPos(), False)

    def mouseMoveEvent(self, event):
        """A mouse move occured on widget"""
        if self.__updateMode in [WColorWheel.__UPDATE_MODE_HUE_CONSTRAINED, WColorWheel.__UPDATE_MODE_HUE]:
            if Qt.ShiftModifier and int(event.modifiers()) == Qt.ShiftModifier:
                self.__updateMode=WColorWheel.__UPDATE_MODE_HUE_CONSTRAINED
            else:
                self.__updateMode=WColorWheel.__UPDATE_MODE_HUE
            self.__updateMouseCursor(event.localPos(), True)
        elif self.__updateMode==WColorWheel.__UPDATE_MODE_INNER:
            self.__updateMouseCursor(event.localPos(), True)
        else:
            if self.__regionColorPreview.contains(event.localPos().toPoint()):
                if self.__updateMode!=WColorWheel.__UPDATE_MODE_OVER_COLOR_PREVIEW:
                    self.__updateMode=WColorWheel.__UPDATE_MODE_OVER_COLOR_PREVIEW
                    self.update()
            else:
                if self.__updateMode!=WColorWheel.__UPDATE_MODE_NONE:
                    self.__updateMode=WColorWheel.__UPDATE_MODE_NONE
                    self.update()

    def wheelEvent(self, event):
        """Mouse wheel...
            up:     increment
            down:   decrement
        """
        localPos=self.mapFromGlobal(event.globalPos())
        factor=1
        modifiers=int(event.modifiers())

        if Qt.ControlModifier & modifiers == Qt.ControlModifier:
            factor=10

        if self.__regionColorWheel.contains(localPos - self.__outerPosition):
            if event.angleDelta().y() > 0:
                # increment hue
                self.__propColorHue.setHsv((self.__propColorHue.hue() + factor) % 360, 255, 255)
            else:
                # decrement hue
                self.__propColorHue.setHsv((self.__propColorHue.hue() - factor) % 360, 255, 255)
            self.__propColor.setHsv(self.__propColorHue.hue(), self.__propColor.saturation(), self.__propColor.value())
            self.__propColor.setAlpha(self.__propAlpha)
            self.update()
            self.__emitColorUpdated()
        elif self.__regionColorInner.contains(localPos - self.__innerPosition):
            if Qt.ShiftModifier & modifiers == Qt.ShiftModifier:
                if event.angleDelta().y() > 0:
                    # increment saturation
                    self.__propColor.setHsv(self.__propColorHue.hue(), min(self.__propColor.saturation()+factor, 255), self.__propColor.value())
                else:
                    # decrement saturation
                    self.__propColor.setHsv(self.__propColorHue.hue(), max(self.__propColor.saturation()-factor, 0), self.__propColor.value())
            else:
                if event.angleDelta().y() > 0:
                    # increment value
                    self.__propColor.setHsv(self.__propColorHue.hue(), self.__propColor.saturation(), min(self.__propColor.value()+factor, 255) )
                else:
                    # decrement value
                    self.__propColor.setHsv(self.__propColorHue.hue(), self.__propColor.saturation(), max(self.__propColor.value()-factor, 0) )
            self.__propColor.setAlpha(self.__propAlpha)
            self.update()
            self.__emitColorUpdated()

    def __calculateFromSize(self):
        """need to recalculate properties depending of widget dimensions"""
        # half width/height
        self.__hWidth = self.width() / 2
        self.__hHeight = self.height() / 2

        # calculate size for color wheel within widget, taking in account margins
        self.__borderLength=min(self.height(), self.width())
        # half size (color wheel radius)
        self.cpHSize=self.__borderLength>>1

        self.__wheelWidth=round(max(min(self.__borderLength * 0.045, self.__optionWheelWidthMax), self.__optionWheelWidthMin))


        self.__outerRect=QRect(0, 0, self.__borderLength, self.__borderLength)
        tmpSize=self.__borderLength-(self.__wheelWidth<<1)
        self.__middleRect=QRect(self.__wheelWidth, self.__wheelWidth, tmpSize, tmpSize)

        self.__outerPosition=QPoint(int(self.__hWidth-self.cpHSize), int(self.__hHeight-self.cpHSize))

        # sqrt(0.5)
        tmpSize=int(tmpSize * 0.7071067811865476)
        self.__innerRect=QRect(0, 0, tmpSize, tmpSize)

        tmpSize>>=1
        self.__innerPosition=QPoint(int(self.__hWidth-tmpSize), int(self.__hHeight-tmpSize))

        #
        tmpSize= int(self.cpHSize - self.cpHSize * 0.7071067811865476)
        self.__showColorRect=QRect(self.__outerPosition,QSize(tmpSize,tmpSize))
        self.__regionColorPreview=QRegion(self.__showColorRect, QRegion.Ellipse)

        # reset cache, as dimension has been modified need to regenerate it
        self.__pixmapColorWheel=None
        self.__pixmapColorInner=None


    def __updateMouseCursor(self, positionXY, isTracking=False):
        """Cursor position has been changed from a mouse event"""
        if self.__updateMode==WColorWheel.__UPDATE_MODE_HUE:
            h=(-math.degrees(math.atan2(positionXY.y() - self.__hHeight, positionXY.x() - self.__hWidth))%360)/360.0
            self.__propColorHue.setHsv( int(-math.degrees(math.atan2(positionXY.y() - self.__hHeight, positionXY.x() - self.__hWidth))%360), 255, 255)
            self.__propColor.setHsv(self.__propColorHue.hue(), self.__propColor.saturation(), self.__propColor.value())
            self.__propColor.setAlpha(self.__propAlpha)

            if isTracking or self.__optionTracking:
                self.__emitColorUpdated()
        elif self.__updateMode==WColorWheel.__UPDATE_MODE_HUE_CONSTRAINED:
            self.__propColorHue.setHsv( round((-math.degrees(math.atan2(positionXY.y() - self.__hHeight, positionXY.x() - self.__hWidth))%360)/30)*30, 255, 255)
            self.__propColor.setHsv(self.__propColorHue.hue(), self.__propColor.saturation(), self.__propColor.value())
            self.__propColor.setAlpha(self.__propAlpha)

            if isTracking or self.__optionTracking:
                self.__emitColorUpdated()
        elif self.__updateMode==WColorWheel.__UPDATE_MODE_INNER:
            if self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_SQ:
                positionXY-=self.__innerPosition
                innerWidth=self.__innerRect.width()

                saturation=int(255*positionXY.x()/innerWidth)
                if saturation>255:
                    saturation=255
                elif saturation<0:
                    saturation=0

                value=int(255*(innerWidth-positionXY.y())/innerWidth)
                if value>255:
                    value=255
                elif value<0:
                    value=0

                self.__propColor.setHsv(self.__propColorHue.hue(), saturation, value)
                self.__propColor.setAlpha(self.__propAlpha)

                if isTracking or self.__optionTracking:
                    self.__emitColorUpdated()
            elif self.__optionInnerModel==WColorWheel.__INNER_MODE_HSL_SQ:
                pass
            elif self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_TR:
                pass

        if self.__updateMode!=WColorWheel.__UPDATE_MODE_NONE:
            self.update()

    def __buildPixmapColorWheel(self):
        """Generate pixmap cache for color wheel"""
        img=QImage(self.__borderLength, self.__borderLength, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        self.__pixmapColorWheel = QPixmap.fromImage(img)

        gradientHue = QConicalGradient(self.cpHSize, self.cpHSize, 0)
        for color in WColorWheel.__HUE_COLORS:
            gradientHue.setColorAt(color[0], color[1])

        canvas = QPainter()
        canvas.begin(self.__pixmapColorWheel)

        if self.__optionAntialiasing:
            canvas.setRenderHint(QPainter.Antialiasing)

        canvas.setPen(Qt.NoPen)

        canvas.setBrush(gradientHue)
        canvas.drawEllipse(self.__outerRect)

        # mask
        canvas.setCompositionMode(QPainter.CompositionMode_Clear)
        canvas.setBrush(Qt.black)
        canvas.drawEllipse(self.__middleRect)

        canvas.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # borders
        if self.__optionBorderWidth>0:
            pen=QPen(self.__optionBorderColor)
            pen.setWidth(self.__optionBorderWidth)
            canvas.setPen(pen)
            canvas.setBrush(Qt.transparent)
            canvas.drawEllipse(self.__outerRect)
            canvas.drawEllipse(self.__middleRect)
        canvas.end()

        # also need to regenerate region
        self.__regionColorWheel=QRegion(self.__outerRect, QRegion.Ellipse)
        self.__regionColorWheel-=QRegion(self.__middleRect, QRegion.Ellipse)

    def __buildPixmapColorInner(self):
        """Generate pixmap cache for inner color"""
        img=QImage(self.__innerRect.size(), QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        self.__pixmapColorInner = QPixmap.fromImage(img)

        canvas = QPainter()
        canvas.begin(self.__pixmapColorInner)

        if self.__optionAntialiasing:
            canvas.setRenderHint(QPainter.Antialiasing)

        if self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_SQ or self.__optionInnerModel==WColorWheel.__INNER_MODE_HSL_SQ:
            if self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_SQ:
                gradientLinearB = QLinearGradient(0, self.__innerRect.height(), 0, 0)
                gradientLinearB.setColorAt(0, Qt.black)
                gradientLinearB.setColorAt(1, Qt.transparent)

                gradientLinearW = QLinearGradient(0, 0, self.__innerRect.width(), 0)
                gradientLinearW.setColorAt(0, Qt.white)
                gradientLinearW.setColorAt(1, Qt.transparent)
            else:
                gradientLinearB = QLinearGradient(0, self.__innerRect.height(), 0, 0)
                #gradientLinearB.setColorAt(0, Qt.black)
                #gradientLinearB.setColorAt(1, Qt.transparent)

                gradientLinearW = QLinearGradient(0, 0, self.__innerRect.width(), 0)
                #gradientLinearW.setColorAt(0, qt.white)
                #gradientLinearW.setColorAt(1, Qt.transparent)

            canvas.setPen(Qt.NoPen)
            rect=QRect(QPoint(0,0), self.__middleRect.size())

            canvas.setBrush(gradientLinearW)
            canvas.drawRect(rect)
            canvas.setBrush(gradientLinearB)
            canvas.drawRect(rect)

            # borders
            if self.__optionBorderWidth>0:
                pen=QPen(self.__optionBorderColor)
                pen.setWidth(self.__optionBorderWidth)
                canvas.setPen(pen)
                canvas.setBrush(Qt.transparent)
                canvas.drawRect(rect)

            # also need to regenerate region
            self.__regionColorInner=QRegion(self.__innerRect, QRegion.Rectangle)
        elif self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_TR:
            pass

        canvas.end()

    def __drawCursorCircle(self, canvas, position, size):
        """Draw a cursor as a circle"""
        penB=QPen(Qt.black)
        penB.setWidth(2)
        penW=QPen(Qt.white)
        penW.setWidth(4)

        canvas.setBrush(Qt.transparent)
        canvas.setPen(penW)
        canvas.drawEllipse(position, size, size)
        canvas.setPen(penB)
        canvas.drawEllipse(position, size+1.5, size+1.5)

    def __drawCursorCircleColorWheel(self, canvas):
        """Draw cursor for color wheel"""
        hWheelSize=self.__wheelWidth>>1
        r=hWheelSize-3

        canvas.translate(QPointF(self.__hWidth, self.__hHeight))
        canvas.rotate(-self.__propColor.hue())
        self.__drawCursorCircle(canvas, QPointF(self.cpHSize-hWheelSize, 0), r)

        canvas.resetTransform()

    def __drawCursorCircleColorInner(self, canvas):
        """Draw cursor for inner color"""
        if self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_SQ:
            canvas.translate(self.__innerPosition)
            innerWidth=self.__innerRect.width()
            pY = (1-self.__propColor.valueF()) * innerWidth
            pX = self.__propColor.hsvSaturationF() * innerWidth
        elif self.__optionInnerModel==WColorWheel.__INNER_MODE_HSL_SQ:
            pass
        elif self.__optionInnerModel==WColorWheel.__INNER_MODE_HSV_TR:
            pass

        self.__drawCursorCircle(canvas, QPointF(pX, pY), 7)

        canvas.resetTransform()

    def __drawColorPreview(self, canvas):
        """Draw color preview"""
        canvas.setPen(Qt.NoPen)
        if self.__propAlpha==255:
            # No transparency
            if self.__updateMode==WColorWheel.__UPDATE_MODE_OVER_COLOR_PREVIEW:
                # full area
                canvas.fillRect(QRect(self.__outerPosition, self.__outerRect.size()), self.__propColor)
            else:
                # circle area
                canvas.setBrush(self.__propColor)
                canvas.drawEllipse(self.__showColorRect)
        else:
            # manage transparency...
            tmpColor=QColor(self.__propColor)
            tmpColor.setAlpha(255)
            if self.__updateMode==WColorWheel.__UPDATE_MODE_OVER_COLOR_PREVIEW:
                # full area
                path=QPainterPath(QPointF(0, 0))
                path.lineTo(self.__outerRect.width(), 0)
                path.lineTo(0, self.__outerRect.height())

                canvas.fillRect(QRect(self.__outerPosition, self.__outerRect.size()), self.__checkerBoardBrush)
                canvas.fillRect(QRect(self.__outerPosition, self.__outerRect.size()), self.__propColor)
                canvas.fillPath(path.translated(self.__outerPosition), tmpColor)
            else:
                # circle area
                pathE=QPainterPath()
                pathE.addEllipse(QRectF(QPointF(0,0), QSizeF(self.__showColorRect.size())))

                pathT=QPainterPath(QPointF(0,0))
                pathT.lineTo(self.__showColorRect.width(), 0)
                pathT.lineTo(0, self.__showColorRect.height())

                canvas.setBrush(self.__checkerBoardBrush)
                canvas.drawEllipse(self.__showColorRect)
                canvas.setBrush(self.__propColor)
                canvas.drawEllipse(self.__showColorRect)
                canvas.fillPath(pathT.intersected(pathE).translated(self.__outerPosition), tmpColor)

    def __emitColorUpdated(self):
        """Emit signal when color has been updated (from mouse position)"""
        self.colorUpdated.emit(self.__propColor)

    def __emitColorChanged(self):
        """Emit signal when color has been changed (programmatically)"""
        self.colorChanged.emit(self.__propColor)


    def color(self):
        """Return current color"""
        return self.__propColor

    def colorHue(self):
        """Return current color hue"""
        return self.__propColorHue

    def alpha(self):
        """Return current alpha value"""
        return self.__propAlpha

    def alpha(self):
        """Return current alpha value"""
        return self.__propAlpha

    def setColor(self, color):
        """Set current color

        If given `color` saturation equal 0, current color hue is not changed
        """
        if not isinstance(color, QColor):
            return

        self.__propColor=color
        if self.__propColor.saturation()!=0 and (self.__propColor.red()!=self.__propColor.green() or self.__propColor.green()!=self.__propColor.blue()):
            self.__propColorHue.setHsv(self.__propColor.hue(), 255, 255)
        self.__propAlpha=self.__propColor.alpha()
        self.update()
        self.__emitColorChanged()


    def optionAntialiasing(self):
        """Return True if antialiasing option is active"""
        return self.__optionAntialiasing

    def optionBorderWidth(self):
        """Return current inner border width (border for color wheel, inner colors)"""
        return self.__optionBorderWidth

    def optionBorderColor(self):
        """Return current inner border color (border for color wheel, inner colors)"""
        return self.__optionBorderColor

    def optionWheelWidthMin(self):
        """Return current minimum width for color color"""
        return self.__optionWheelWidthMin

    def optionWheelWidthMax(self):
        """Return current maximum width for color color"""
        return self.__optionWheelWidthMax

    def optionTracking(self):
        """Return True if tracking is activated"""
        return self.__optionTracking

    def optionPreviewColor(self):
        """Return True if preview color is visible"""
        return self.__optionPreviewColor

    def optionInnerModel(self):
        """Return current inner color model applied (model inside color wheel)"""
        return self.__optionInnerModel


    def setOptionAntialiasing(self, value):
        """Set if antialiasing option is active"""
        if not isinstance(value, bool) or value==self.__optionAntialiasing:
            return

        self.__optionAntialiasing=value
        self.update()

    def setOptionBorderWidth(self, value):
        """set inner border width (border for color wheel, inner colors)"""
        if not isinstance(value, (int, float)) or value==self.__optionBorderWidth:
            return

        self.__optionBorderWidth=max(0, value)
        self.update()

    def setOptionBorderColor(self, value):
        """set inner border width (border for color wheel, inner colors)"""
        if not isinstance(value, QColor) or value==self.__optionBorderColor:
            return

        self.__optionBorderColor=value
        self.update()

    def setOptionWheelWidthMin(self, value):
        """set minimum wheel width"""
        if not isinstance(value, (int, float)) or value==self.__optionWheelWidthMin:
            return

        self.__optionWheelWidthMin=round(value)
        if self.__optionWheelWidthMin>self.__optionWheelWidthMax:
            self.__optionWheelWidthMax=self.__optionWheelWidthMin
        self.__calculateFromSize()
        self.update()

    def setOptionWheelWidthMax(self, value):
        """set maximum wheel width"""
        if not isinstance(value, (int, float)) or value==self.__optionWheelWidthMax:
            return

        self.__optionWheelWidthMax=round(value)
        if self.__optionWheelWidthMax<self.__optionWheelWidthMin:
            self.__optionWheelWidthMin=self.__optionWheelWidthMax
        self.__calculateFromSize()
        self.update()

    def setOptionTracking(self, value):
        """Set if mouse tracking is active

        When
        """
        if not isinstance(value, bool) or value==self.__optionTracking:
            return

        self.__optionTracking=value

    def setOptionPreviewColor(self, value):
        """Set if preview color is active"""
        if not isinstance(value, bool) or value==self.__optionPreviewColor:
            return

        self.__optionPreviewColor=value
        self.update()

    def setOptionInnerModel(self, value):
        """Return current inner color model applied (model inside color wheel)"""
        if not value in [WColorWheel.__INNER_MODE_HSV_SQ] or value==self.__optionInnerModel:
            return

        self.__optionInnerModel=value
        self.__calculateFromSize()
        self.update()



class WColorSlider(QWidget):
    """A slider with color"""
    valueUpdated = Signal(float)       # when value is changed from user interface
    valueChanged = Signal(float)       # when value is changed programmatically

    __MODELS={
            'red':          {'fgGradient': [(0, QColor(Qt.black)), (1, QColor(Qt.red))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Red (RGB)')
                            },

            'green':        {'fgGradient': [(0, QColor(Qt.black)), (1, QColor(Qt.green))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Green (RGB)')
                            },

            'blue':         {'fgGradient': [(0, QColor(Qt.black)), (1, QColor(Qt.blue))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Blue (RGB)')
                            },

            'cyan':         {'fgGradient': [(0, QColor(Qt.white)), (1, QColor(Qt.cyan))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Cyan (CMYK)')
                            },

            'magenta':      {'fgGradient': [(0, QColor(Qt.white)), (1, QColor(Qt.magenta))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Magenta (CMYK)')
                            },

            'yellow':       {'fgGradient': [(0, QColor(Qt.white)), (1, QColor(Qt.yellow))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Yellow (CMYK)')
                            },

            'black':        {'fgGradient': [(0, QColor(Qt.white)), (1, QColor(Qt.black))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Black (CMYK)')
                            },

            'alpha':        {'fgGradient': [(0, QColor(Qt.transparent)), (1, QColor(Qt.black))],
                             'bgColor': checkerBoardBrush(),
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Alpha')
                            },

            'hue':          {'fgGradient': [(0,   QColor(Qt.red)),
                                            (1/6, QColor(Qt.yellow)),       # 60°
                                            (1/3, QColor(Qt.green)),        # 120°
                                            (0.5, QColor(Qt.cyan)),         # 180°
                                            (2/3, QColor(Qt.blue)),         # 240°
                                            (5/6, QColor(Qt.magenta)),      # 300°
                                            (1,   QColor(Qt.red))
                                           ],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 360,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Hue (HSL/HSV)')
                            },

            'saturation':   {'fgGradient': [(0, QColor('#808080')), (1, QColor(Qt.transparent))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Saturation (HSL/HSV)')
                            },

            'value':        {'fgGradient': [(0, QColor(Qt.black)), (1, QColor(Qt.transparent))],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Value (HSV)')
                            },

            'lightness':    {'fgGradient': [(0,   QColor(Qt.black)),
                                            (0.5, QColor(Qt.transparent)),
                                            (1,   QColor(Qt.white))
                                        ],
                             'bgColor': None,
                             'valueMin': 0,
                             'valueMax': 255,
                             'valueDec': 0,
                             'ticksMain': 0,
                             'ticksSecond': 0,
                             'tooltip': i18n('Lightness (HSL)')
                            }
        }

    class WColoredSlider(QWidget):
        valueUpdated = Signal(float)       # when value is changed from user interface
        valueChanged = Signal(float)       # when value is changed programmatically

        __UPDATE_MODE_NONE=0
        __UPDATE_MODE_SLIDE=1

        def __init__(self, parent=None):
            super(WColorSlider.WColoredSlider, self).__init__(parent)

            # by default... need to review sizehint
            #self.setMaximumHeight(20)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

            # options
            self.__optionTracking=True
            self.__optionAntialiasing=True
            self.__optionRoundCorner=5
            self.__optionMarginV=8
            self.__optionMarginH=-1
            self.__optionTickWidth=2
            self.__optionTickColor=QColor('#888888')
            self.__optionTickHideLimit=3
            self.__optionCursorSize=-1
            self.__optionCursorMaxSize=12
            self.__optionCursorMinSize=6
            self.__optionCursorBWidth=2
            self.__optionCursorWWidth=2

            # properties
            self.__propFgGradient=None
            self.__propBgColor=None
            self.__propValue=0
            self.__propValueMin=0
            self.__propValueMax=255
            self.__propValueDec=0
            self.__propTicksMain=0
            self.__propTicksSecond=0

            # pixmap cache
            self.__pixmapFgGradient=None
            self.__pixmapBgTicks=None

            # -- technical
            self.__invalidatedFgGradient=True
            self.__invalidatedBgTicks=True

            self.__cursorPosition=0
            self.__cursorBSize=0
            self.__cursorWSize=0

            self.__paintRect=QRect()
            self.__margins=QMargins()

            # - need to be reviewed (calculation depend of options)
            self.__hHeight=self.height()/2

            self.__ticksOffsetX=self.__optionTickWidth/2
            self.__ticksOffsetY=self.__optionMarginV/2
            self.__ticksHideLimit=self.__optionTickHideLimit*self.__optionTickWidth

            self.__updateMode=WColorSlider.WColoredSlider.__UPDATE_MODE_NONE


        def mousePressEvent(self, event):
            """A mouse button is clicked on widget"""
            self.__updateMode=WColorSlider.WColoredSlider.__UPDATE_MODE_NONE
            if Qt.LeftButton and event.buttons() == Qt.LeftButton:
                self.__updateMode=WColorSlider.WColoredSlider.__UPDATE_MODE_SLIDE
                self.__updateMouseCursor(event.localPos(), False)


        def mouseReleaseEvent(self, event):
            """A mouse button is clicked on widget"""
            if self.__updateMode!=WColorSlider.WColoredSlider.__UPDATE_MODE_NONE:
                self.__updateMode=WColorSlider.WColoredSlider.__UPDATE_MODE_NONE
                self.__updateMouseCursor(event.localPos(), False)


        def mouseMoveEvent(self, event):
            """A mouse move occured on widget"""
            if self.__updateMode == WColorSlider.WColoredSlider.__UPDATE_MODE_SLIDE:
                self.__updateMouseCursor(event.localPos(), True)


        def wheelEvent(self, event):
            """Mouse wheel...
                up:     increment
                down:   decrement
            """
            if event.angleDelta().y() > 0:
                # increment
                self.setValue(self.__propValue + 1)
                self.__emitValueUpdated()
            else:
                # decrement
                self.setValue(self.__propValue - 1)
                self.__emitValueUpdated()


        def resizeEvent(self, event):
            """Widget is resized, need to recalculate properties depending of widget dimensions"""
            # reset cache, as dimension has been modified need to regenerate it
            self.__calculateFromSize()


        def paintEvent(self, event):
            """Draw current slider"""
            painter = QPainter(self)

            if self.__optionAntialiasing:
                painter.setRenderHint(QPainter.Antialiasing)

            if self.__propTicksMain>0 and self.__optionMarginV>0:
                # draw background ticks if defined and if margins are available
                if self.__invalidatedBgTicks:
                    # regenerate cache for ticks
                    self.__buildPixmapBgTicks()

                if self.__pixmapBgTicks:
                    painter.drawPixmap(0, 0, self.__pixmapBgTicks)

            if self.__propBgColor:
                # draw background color if a color is defined
                if self.__optionRoundCorner==0:
                    painter.fillRect(self.__paintRect, self.__propBgColor)
                else:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.__propBgColor)
                    painter.drawRoundedRect(self.__paintRect, self.__optionRoundCorner, self.__optionRoundCorner)

            if self.__propFgGradient:
                # draw foreground gradient if defined
                if self.__invalidatedFgGradient:
                    # regenerate cache for gradient
                    self.__buildPixmapFgGradient()

                painter.drawPixmap(0, 0, self.__pixmapFgGradient)

            # cursor
            self.__drawCursor(painter)

            # debug...
            #painter.setPen(QPen(QColor(255,255,255,128)))
            #painter.drawRect(self.__paintRect)
            #painter.drawRect(self.rect())
            pass


        def __calculateFromSize(self):
            """Recalculate properties depending of widget dimensions"""
            # reset cache, as dimension has been modified need to regenerate it
            self.__pixmapGradient=None
            self.__invalidatedFgGradient=True
            self.__invalidatedBgTicks=True

            self.__hHeight=self.height()/2

            self.__paintRect=self.rect()
            if self.__optionMarginV!=0 or self.__optionMarginH!=0:
                self.__margins=QMargins(0, self.__optionMarginV, 0, self.__optionMarginV)
                if self.__optionMarginH>0:
                    self.__margins.setLeft(self.__optionMarginH)
                    self.__margins.setRight(self.__optionMarginH)
                elif self.__optionMarginH<0:
                    self.__margins.setLeft(int(self.__hHeight))
                    self.__margins.setRight(int(self.__hHeight))
                self.__paintRect-=self.__margins


            if self.__optionCursorSize==-1:
                size=self.__paintRect.height()/2
            else:
                size=self.__optionCursorSize
            if size>self.__optionCursorMaxSize:
                size=self.__optionCursorMaxSize
            elif size<self.__optionCursorMinSize:
                size=self.__optionCursorMinSize
            self.__cursorBSize=size-self.__optionCursorBWidth/2
            self.__cursorWSize=size-self.__optionCursorBWidth


            self.__calculateCursorPosition()


        def __calculateCursorPosition(self):
            """Calculate cursor position (center) according to:
                - value
                - min/max value
                - widget width
            """
            if self.__propValueMax == self.__propValueMin:
                # should not occurs, but in this case...
                self.__cursorPosition=-1
            else:
                self.__cursorPosition=self.__margins.left() + self.__paintRect.width() * self.__propValue/(self.__propValueMax - self.__propValueMin)

            self.update()


        def __updateMouseCursor(self, positionXY, isTracking=False):
            """Calculate position from mouse position"""
            if self.__updateMode==WColorSlider.WColoredSlider.__UPDATE_MODE_SLIDE:
                newValue=round(self.__propValueMin + (self.__propValueMax - self.__propValueMin) * (positionXY.x() - self.__margins.left())/self.__paintRect.width(), self.__propValueDec)
                if newValue < self.__propValueMin:
                    newValue=self.__propValueMin
                elif newValue > self.__propValueMax:
                    newValue=self.__propValueMax

                if newValue!=self.__propValue:
                    self.__propValue=newValue
                    self.__calculateCursorPosition()

                    if isTracking or self.__optionTracking:
                        self.__emitValueUpdated()

                    if self.__updateMode!=WColorSlider.WColoredSlider.__UPDATE_MODE_NONE:
                        self.update()


        def __drawCursor(self, canvas):
            """Draw cursor"""
            position=QPointF(self.__cursorPosition, self.height()/2)

            penB=QPen(Qt.black)
            penB.setWidth(self.__optionCursorBWidth)
            penW=QPen(Qt.white)
            penW.setWidth(self.__optionCursorWWidth)

            canvas.setBrush(Qt.transparent)
            canvas.setPen(penW)
            canvas.drawEllipse(position, self.__cursorWSize, self.__cursorWSize)
            canvas.setPen(penB)
            canvas.drawEllipse(position, self.__cursorBSize, self.__cursorBSize)


        def __buildPixmapFgGradient(self):
            """Generate pixmap cache for foreground gradient wheel"""
            img=QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent)
            self.__pixmapFgGradient = QPixmap.fromImage(img)

            gradientLinear = QLinearGradient(0, 0, 1, 0)
            gradientLinear.setCoordinateMode(QGradient.ObjectBoundingMode)
            for gradientPoint in self.__propFgGradient:
                gradientLinear.setColorAt(gradientPoint[0], gradientPoint[1])

            canvas = QPainter()
            canvas.begin(self.__pixmapFgGradient)

            if self.__optionAntialiasing:
                canvas.setRenderHint(QPainter.Antialiasing)

            canvas.setPen(Qt.NoPen)

            canvas.setBrush(gradientLinear)
            if self.__optionRoundCorner==0:
                canvas.drawRect(self.__paintRect)
            else:
                canvas.drawRoundedRect(self.__paintRect, self.__optionRoundCorner, self.__optionRoundCorner)

            canvas.end()


        def __buildPixmapBgTicks(self):
            """Generate pixmap cache for background ticks"""
            # calculate number of ticks
            nbTicksMain=round((self.__propValueMax - self.__propValueMin)/self.__propTicksMain)

            nbTicksSecond=0
            if self.__propTicksSecond>0:
                nbTicksSecond=round((self.__propValueMax - self.__propValueMin)/self.__propTicksSecond)

            # calculate space between ticks
            spaceTicksMain=self.__paintRect.width()/nbTicksMain

            if spaceTicksMain<self.__ticksHideLimit:
                nbTicksMain=0
                nbTicksSecond=0
                self.__pixmapBgTicks=None
                return

            spaceTicksSecond=0
            if nbTicksSecond>0:
                spaceTicksSecond=self.__paintRect.width()/nbTicksSecond

                if spaceTicksSecond<self.__ticksHideLimit:
                    nbTicksSecond=0


            img=QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent)
            self.__pixmapBgTicks = QPixmap.fromImage(img)

            canvas = QPainter()
            canvas.begin(self.__pixmapBgTicks)

            if self.__optionAntialiasing:
                canvas.setRenderHint(QPainter.Antialiasing)

            canvas.setPen(Qt.NoPen)
            canvas.setBrush(self.__optionTickColor)

            if nbTicksSecond>0:
                position=self.__paintRect.left()
                for tick in range(1, nbTicksSecond):
                    position+=spaceTicksSecond
                    canvas.fillRect(QRectF(position-self.__ticksOffsetX, self.__ticksOffsetY, self.__optionTickWidth, self.height()-self.__margins.top()), self.__optionTickColor)

            if nbTicksMain>0:
                position=self.__paintRect.left()
                for tick in range(1, nbTicksMain):
                    position+=spaceTicksMain
                    canvas.fillRect(QRectF(position-self.__ticksOffsetX, 0, self.__optionTickWidth, self.height()), self.__optionTickColor)

            canvas.end()


        def __emitValueUpdated(self):
            """Emit signal when value has been updated (from mouse position)"""
            self.valueUpdated.emit(self.__propValue)


        def __emitValueChanged(self):
            """Emit signal when color has been changed (programmatically)"""
            self.valueChanged.emit(self.__propValue)


        def setFgGradient(self, value):
            """Define a customized foreground gradient"""
            if isinstance(value, list):
                self.__propFgGradient=[]

                for item in value:
                    if isinstance(item, tuple) and isinstance(item[0], (int, float)) and isinstance(item[1], QColor):
                        self.__propFgGradient.append(item)

                self.__invalidatedFgGradient=True
                self.update()


        def setBgColor(self, value):
            """Define a customized background color"""
            if isinstance(value, (QBrush, QColor)):
                self.__propBgColor=value
                self.update()


        def setValueMin(self, value):
            """Define minimum allowed value"""
            self.__propValueMin=round(value, self.__propValueDec)

            if self.__propValueMin > self.__propValueMax:
                self.setValueMax(self.__propValueMin)

            if self.__propValue < self.__propValueMin:
                self.setValue(self.__propValueMin)

            self.__calculateCursorPosition()


        def setValueMax(self, value):
            """Define maximum allowed value"""
            self.__propValueMax=round(value, self.__propValueDec)

            if self.__propValueMax < self.__propValueMin:
                self.setValueMin(self.__propValueMax)

            if self.__propValue > self.__propValueMax:
                self.setValue(self.__propValueMax)

            self.__calculateCursorPosition()


        def setValue(self, value):
            """Define current value"""
            newValue=round(value, self.__propValueDec)

            if self.__propValue==newValue:
                return False

            self.__propValue=newValue

            if self.__propValue < self.__propValueMin:
                self.__propValue=self.__propValueMin
            elif self.__propValue > self.__propValueMax:
                self.__propValue=self.__propValueMax

            self.__calculateCursorPosition()

            return True


        def setValueDecimals(self, value):
            """Define current decimals for value"""
            if value!=self.__propValueDec:
                self.__propValueDec=value

                self.setValueMin(self.__propValueMin)
                self.setValueMax(self.__propValueMax)
                self.setValue(self.__propValue)


        def setTicksMain(self, value):
            """Define current main ticks value"""
            if value!=self.__propTicksMain and value>=0:
                self.__propTicksMain=value
                self.__invalidatedBgTicks=True
                self.update()


        def setTicksSecond(self, value):
            """Define current second ticks value"""
            if value!=self.__propTicksSecond and value>=0:
                self.__propTicksSecond=value
                self.__invalidatedBgTicks=True
                self.update()


        def fgGradient(self):
            """Return current foreground gradient"""
            return self.__propFgGradient


        def bgColor(self):
            """Return current background color"""
            return self.__propBgColor


        def valueMin(self):
            """Return current minimum value"""
            return self.__propValueMin


        def valueMax(self):
            """Return current maximum value"""
            return self.__propValueMax


        def value(self):
            """Return current value"""
            return self.__propValue


        def valueDecimals(self):
            """Return value decimals """
            return self.__propValueDec


        def ticksMain(self):
            """Return main ticks value"""
            return self.__propTicksMain


        def ticksSecond(self):
            """Return second ticks value"""
            return self.__propTicksSecond


        def optionMarginV(self):
            """Return current vertical margin value"""
            return self.__optionMarginV


        def setOptionMarginV(self, value):
            if not isinstance(value, int) or value==self.__optionMarginV:
                return
            self.__optionMarginV=value
            self.__calculateFromSize()

    def __init__(self, model=None, fgGradient=None, bgColor=None, parent=None):
        super(WColorSlider, self).__init__(parent)

        self.__optionCompactUi=False
        self.__optionAsPct=False

        self.__disableSignal=False

        self.__layout = QHBoxLayout(self)
        self.__modelId='custom'

        self.__wColorSlider=WColorSlider.WColoredSlider(self)
        self.__wValueSpin=QDoubleSpinBox()
        self.__wValueSpin.setAlignment(Qt.AlignRight)

        self.__layout.addWidget(self.__wColorSlider)
        self.__layout.addWidget(self.__wValueSpin)

        self.__wValueSpin.valueChanged.connect(self.__updateFromSpin)
        self.__wColorSlider.valueUpdated.connect(self.__updateFromSlider)

        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.__layout)

        if isinstance(model, str):
            self.setModel(model)
        else:
            self.setFgGradient(fgGradient)
            self.setBgColor(bgColor)


    def __updateFromSlider(self, value):
        if self.__disableSignal:
            return
        self.__defineSpinValue()
        self.valueUpdated.emit(value)


    def __updateFromSpin(self, value):
        if self.__disableSignal:
            return
        if self.__optionAsPct:
            errorFix=0
            if value<=50:
                errorFix=1
            self.__wColorSlider.setValue(round(value*(errorFix+self.__wColorSlider.valueMax()-self.__wColorSlider.valueMin())/100+self.__wColorSlider.valueMin(), self.__wColorSlider.valueDecimals()))
        else:
            self.__wColorSlider.setValue(value)
        self.valueUpdated.emit(self.__wColorSlider.value())


    def __defineSpinValueMin(self):
        """Calculate spin min value according to slider values and PCT option"""
        if self.__optionAsPct:
            self.__wValueSpin.setMinimum(0)
        else:
            self.__wValueSpin.setMinimum(self.__wColorSlider.valueMin())

    def __defineSpinValueMax(self):
        """Calculate spin max value according to slider values and PCT option"""
        if self.__optionAsPct:
            self.__wValueSpin.setMaximum(100)
        else:
            self.__wValueSpin.setMaximum(self.__wColorSlider.valueMax())

    def __defineSpinValue(self):
        """Calculate spin current value according to slider values and PCT option"""
        if self.__optionAsPct:
            errorFix=0
            if self.__wColorSlider.value()<=128:
                errorFix=1
            divisor=(errorFix+self.__wColorSlider.valueMax()-self.__wColorSlider.valueMin())
            if divisor!=0:
                self.__wValueSpin.setValue(round(100*self.__wColorSlider.value()/divisor, 2))
            else:
                self.__wValueSpin.setValue(0)
        else:
            self.__wValueSpin.setValue(self.__wColorSlider.value())

    def __defineSpinDecimals(self):
        """Calculate spin current value according to slider values and PCT option"""
        if self.__optionAsPct:
            self.__wValueSpin.setDecimals(2)
        else:
            self.__wValueSpin.setDecimals(self.__wColorSlider.valueDecimals())


    def setModel(self, value):
        """Define slider according to a given model"""
        if value in WColorSlider.__MODELS:
            self.__modelId=value
            self.setToolTip(WColorSlider.__MODELS[value]['tooltip'])
            self.setTicksMain(WColorSlider.__MODELS[value]['ticksMain'])
            self.setTicksSecond(WColorSlider.__MODELS[value]['ticksSecond'])
            self.setFgGradient(WColorSlider.__MODELS[value]['fgGradient'])
            self.setBgColor(WColorSlider.__MODELS[value]['bgColor'])
            self.setValueDecimals(WColorSlider.__MODELS[value]['valueDec'])
            self.setValueMin(WColorSlider.__MODELS[value]['valueMin'])
            self.setValueMax(WColorSlider.__MODELS[value]['valueMax'])


    def setFgGradient(self, value):
        """Define a customized foreground gradient"""
        self.__wColorSlider.setFgGradient(value)


    def setBgColor(self, value):
        """Define a customized background color"""
        self.__wColorSlider.setBgColor(value)


    def setValueMin(self, value):
        """Define minimum allowed value"""
        self.__disableSignal=True
        self.__wColorSlider.setValueMin(value)
        self.__defineSpinValueMin()
        self.__disableSignal=False


    def setValueMax(self, value):
        """Define maximum allowed value"""
        self.__disableSignal=True
        self.__wColorSlider.setValueMax(value)
        self.__defineSpinValueMax()
        self.__disableSignal=False


    def setValue(self, value):
        """Define current value"""
        self.__disableSignal=True
        self.__wColorSlider.setValue(value)
        self.__defineSpinValue()
        self.__disableSignal=False
        self.valueChanged.emit(value)


    def setValueDecimals(self, value):
        """Define current decimals for value"""
        self.__disableSignal=True
        self.__wColorSlider.setValueDecimals(value)
        self.__defineSpinDecimals()
        self.__disableSignal=False


    def setTicksMain(self, value):
        """Define current main ticks value"""
        self.__wColorSlider.setTicksMain(value)


    def setTicksSecond(self, value):
        """Define current second ticks value"""
        self.__wColorSlider.setTicksSecond(value)


    def setSuffix(self, value):
        """Define current suffix"""
        self.__wValueSpin.setSuffix(value)


    def fgGradient(self):
        """Return current foreground gradient"""
        return self.__propFgGradient


    def bgColor(self):
        """Return current background color"""
        return self.__propBgColor


    def valueMin(self):
        """Return current minimum value"""
        return self.__wColorSlider.valueMin()


    def valueMax(self):
        """Return current maximum value"""
        return self.__wColorSlider.valueMax()


    def value(self):
        """Return current value"""
        return self.__wColorSlider.value()


    def valuePct(self, decimals=2):
        """Return current value as Pct"""
        errorFix=0
        if self.__wColorSlider.value()<=128:
            errorFix=1
        divisor=(errorFix+self.__wColorSlider.valueMax()-self.__wColorSlider.valueMin())
        if divisor!=0:
            returned=100*self.__wColorSlider.value()/divisor
            if isinstance(decimals, int) and decimals>=0:
                returned=round(returned, decimals)
        else:
            returned=0
        return returned


    def valueDecimals(self):
        """Return value decimals """
        return self.__wColorSlider.valueDecimals()


    def ticksMain(self):
        """Return main ticks value"""
        return self.__propTicksMain


    def ticksSecond(self):
        """Return second ticks value"""
        return self.__propTicksSecond


    def suffix(self):
        """Return current suffix"""
        return self.__wValueSpin.suffix()


    def model(self):
        """Return current model"""
        return self.__modelId


    def optionCompactUi(self):
        """Return if option 'small size' is active or not"""
        return self.__optionCompactUi


    def setOptionCompactUi(self, value):
        """Set if option 'small size' is active or not"""
        if not isinstance(value, bool) or self.__optionCompactUi==value:
            return

        self.__optionCompactUi=value

        if self.__optionCompactUi:
            self.__wValueSpin.setMaximumHeight(22)
            self.__wColorSlider.setOptionMarginV(4)
        else:
            self.__wValueSpin.setMaximumHeight(99999)
            self.__wColorSlider.setOptionMarginV(8)


    def optionAsPct(self):
        """Return if slider works in PCT mode"""
        return self.__optionAsPct

    def setOptionAsPct(self, value):
        """Set if slider works in PCT mode"""
        if isinstance(value, bool) and value!=self.__optionAsPct:
            self.__optionAsPct=value

            if value:
                self.__wValueSpin.setSuffix('%')
            else:
                self.__wValueSpin.setSuffix('')
            self.__disableSignal=True
            self.__defineSpinDecimals()
            self.__defineSpinValueMin()
            self.__defineSpinValueMax()
            self.__defineSpinValue()
            self.__disableSignal=False



class WColorComplementary(QWidget):
    """Display complementary colors"""
    colorClicked = Signal(QColor, int)       # when color is clicked from user interface (color, color index)
    colorOver = Signal(QColor, int)       # when mouse is over a color (color, color index)

    COLOR_COMBINATION_NONE=0
    COLOR_COMBINATION_MONOCHROMATIC=1
    COLOR_COMBINATION_COMPLEMENTARY=2
    COLOR_COMBINATION_ANALOGOUS=3
    COLOR_COMBINATION_TRIADIC=4
    COLOR_COMBINATION_TETRADIC=5

    # position of current color
    __COLOR_INDEX=(
                -1,     # COLOR_COMBINATION_NONE
                3,      # COLOR_COMBINATION_MONOCHROMATIC
                0,      # COLOR_COMBINATION_COMPLEMENTARY
                1,      # COLOR_COMBINATION_ANALOGOUS
                1,      # COLOR_COMBINATION_TRIADIC
                0       # COLOR_COMBINATION_TETRADIC
        )

    def __init__(self, color, parent=None):
        super(WColorComplementary, self).__init__(parent)

        if isinstance(color, QColor):
            self.__color=color
        else:
            self.__color=QColor(Qt.red)

        self.__mode=WColorComplementary.COLOR_COMBINATION_NONE

        self.__optionMargin=8
        self.__optionAntialiasing=True
        self.__optionRoundCorner=5

        # calculated colors
        self.__colors=()
        self.__regions=[]

        self.__width=0
        self.__positions=[]
        self.__mouseOver=None

        margin=round(self.__optionMargin*0.6)
        self.__margins=QMargins(margin, margin, margin, margin)

        self.__alpha=255

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.setVisible(False)
        self.setMouseTracking(True)

    def resizeEvent(self, event):
        """Widget is resized, need to recalculate properties depending of widget dimensions"""
        self.__calculateFromSize()

    def mouseMoveEvent(self, event):
        """A mouse move occured on widget"""
        mouseOver=self.__mouseOver

        over=False
        for colorNumber in range(len(self.__colors)):
            if self.__regions[colorNumber].contains(event.localPos().toPoint()):
                mouseOver=colorNumber
                over=True
                break

        if not over or mouseOver==WColorComplementary.__COLOR_INDEX[self.__mode]:
            # when over current color, ignore it
            mouseOver=None

        if mouseOver!=self.__mouseOver:
            self.__mouseOver=mouseOver
            if self.__mouseOver is None:
                self.setCursor(Qt.ArrowCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
            self.update()

            if not self.__mouseOver is None:
                self.colorOver.emit(self.__color, self.__mouseOver)

    def mousePressEvent(self, event):
        """Mouse cliked, emit signal if over a color"""
        if Qt.LeftButton and event.buttons() == Qt.LeftButton and not self.__mouseOver is None:
            self.colorClicked.emit(self.colors()[self.__mouseOver], self.__mouseOver)

    def leaveEvent(self, event):
        """Mouse leav widget, ensure color are painter normally"""
        if not self.__mouseOver is None:
            self.__mouseOver=None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def paintEvent(self, event):
        """paint widget content..."""
        painter = QPainter(self)

        if self.__optionAntialiasing:
            # if antialiased, set it active
            painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        for colorNumber in range(len(self.__colors)):
            painter.setBrush(self.__colors[colorNumber])
            if self.__mouseOver==colorNumber:
                painter.drawRoundedRect(self.__positions[colorNumber]+self.__margins, self.__optionRoundCorner, self.__optionRoundCorner)
            else:
                painter.drawRoundedRect(self.__positions[colorNumber], self.__optionRoundCorner, self.__optionRoundCorner)


    def __calculateFromSize(self):
        """recalculate properties depending of widget dimensions"""
        self.__regions=[]
        self.__positions=[]

        nbColors=len(self.__colors)

        if nbColors>0:
            self.__width=round(self.width()/nbColors-2*self.__optionMargin)
        else:
            self.__width=0
            return

        height=round(self.height()-2*self.__optionMargin)

        position=self.__optionMargin
        for colorNumber in range(nbColors):
            rect=QRect(round(position), self.__optionMargin, self.__width, height)
            self.__positions.append(rect)
            self.__regions.append(QRegion(rect))
            position+=self.__width+2*self.__optionMargin

    def __calculateColors(self):
        """Caclulate colors according to current color and current mode"""
        if self.__mode==WColorComplementary.COLOR_COMBINATION_NONE:
            self.__colors=()
        elif self.__mode==WColorComplementary.COLOR_COMBINATION_MONOCHROMATIC:
            self.__colors=(self.__color.darker(400),
                           self.__color.darker(200),
                           self.__color.darker(150),
                           self.__color,
                           self.__color.lighter(125),
                           self.__color.lighter(150),
                           self.__color.lighter(175))
        elif self.__mode==WColorComplementary.COLOR_COMBINATION_COMPLEMENTARY:
            self.__colors=(self.__color,
                           QColor.fromHsv((self.__color.hue() + 180)%360, self.__color.saturation(), self.__color.value())
                        )
        elif self.__mode==WColorComplementary.COLOR_COMBINATION_ANALOGOUS:
            self.__colors=(QColor.fromHsv((self.__color.hue() - 30)%360, self.__color.saturation(), self.__color.value()),
                           self.__color,
                           QColor.fromHsv((self.__color.hue() + 30)%360, self.__color.saturation(), self.__color.value())
                        )
        elif self.__mode==WColorComplementary.COLOR_COMBINATION_TRIADIC:
            self.__colors=(QColor.fromHsv((self.__color.hue() - 120)%360, self.__color.saturation(), self.__color.value()),
                           self.__color,
                           QColor.fromHsv((self.__color.hue() + 120)%360, self.__color.saturation(), self.__color.value())
                        )
        elif self.__mode==WColorComplementary.COLOR_COMBINATION_TETRADIC:
            self.__colors=(self.__color,
                           QColor.fromHsv((self.__color.hue() - 90)%360, self.__color.saturation(), self.__color.value()),
                           QColor.fromHsv((self.__color.hue() + 180)%360, self.__color.saturation(), self.__color.value()),
                           QColor.fromHsv((self.__color.hue() + 90)%360, self.__color.saturation(), self.__color.value())
                        )


    def mode(self):
        """Return current combination mode"""
        return self.__mode

    def setMode(self, value):
        """Set  current combination mode"""
        if value==self.__mode or not value in [
                                        WColorComplementary.COLOR_COMBINATION_NONE,
                                        WColorComplementary.COLOR_COMBINATION_MONOCHROMATIC,
                                        WColorComplementary.COLOR_COMBINATION_COMPLEMENTARY,
                                        WColorComplementary.COLOR_COMBINATION_ANALOGOUS,
                                        WColorComplementary.COLOR_COMBINATION_TRIADIC,
                                        WColorComplementary.COLOR_COMBINATION_TETRADIC
                                    ]:
            return

        self.__mode=value
        self.__calculateColors()

        if self.__mode==WColorComplementary.COLOR_COMBINATION_NONE:
            self.__nbColors=0
            self.setVisible(False)
        else:
            self.__calculateFromSize()
            if self.isVisible():
                self.update()
            else:
                self.setVisible(True)

    def color(self):
        """Return current color"""
        if self.__alpha!=255:
            returned=QColor(self.__color)
            returned.setAlpha(self.__alpha)
            return returned
        return self.__color

    def colors(self):
        """Return all colors as a tuple

        - COLOR_COMBINATION_NONE:           (color)
        - COLOR_COMBINATION_MONOCHROMATIC:  (color, darkerColor, lighterColor)
        - COLOR_COMBINATION_ANALOGOUS:      (color, -30DegreeColor,+30DegreeColor)
        - COLOR_COMBINATION_COMPLEMENTARY:  (color, opposite)
        - COLOR_COMBINATION_TRIADIC:        (color, -120DegreeColor,+120DegreeColor)
        - COLOR_COMBINATION_TETRADIC:       (color, -90DegreeColor, opposite, +90DegreeColor)
        """
        if self.__alpha!=255:
            returned=[]
            for color in self.__colors:
                tmp=QColor(color)
                tmp.setAlpha(self.__alpha)
                returned.append(tmp)
            return returned

        return self.__colors

    def setColor(self, value):
        """Set current color"""
        if value==self.__color or not isinstance(value, QColor):
            return

        self.__color=QColor(value)
        # ignore alpha value to render color, but keep alpha value in memory
        self.__alpha=self.__color.alpha()
        self.__color.setAlpha(255)

        self.__calculateColors()
        self.update()



class WColorCssEdit(QWidget):
    """A simple widget to manage Css value edit (#rrggbb)"""
    colorUpdated = Signal(QColor)       # when color is changed from user interface
    colorChanged = Signal(QColor)       # when color is changed programmatically

    def __init__(self, parent=None):
        super(WColorCssEdit, self).__init__(parent)

        self.__color=None

        self.__leWebColorEdit=QLineEdit(self)
        self.__leWebColorEdit.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.__leWebColorEdit.setAlignment(Qt.AlignRight)
        self.__leWebColorEdit.textEdited.connect(self.__colorCssRGBChanged)

        webColorLayout=QHBoxLayout(self)
        webColorLayout.setContentsMargins(0, 0, 0, 0)
        webColorLayout.addStretch()
        webColorLayout.addWidget(self.__leWebColorEdit)

        self.setLayout(webColorLayout)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)

    def __colorCssRGBChanged(self, value):
        """Value modified manually by user"""
        try:
            self.__color=QColor(value)
            self.colorUpdated.emit(self.__color)
        except:
            return


    def setColor(self, value):
        """Set given color"""
        try:
            self.__color=QColor(value)
        except:
            return
        self.__leWebColorEdit.setText(self.__color.name(QColor.HexRgb))
        self.colorChanged.emit(self.__color)

    def color(self):
        """Return current color

        Note: if current defined color in editor is not valid, return None
        """
        return self.__color



class WColorPalette(QWidget):
    """A simple widget to manage palettes"""
    colorOver = Signal(int, Swatch, QColor)             # when mouse is over a color (color index, color swatch, color)
    colorClicked = Signal(int, Swatch, QColor, int)       # when a color has been clicked (color index, color swatch, color, mouse button)
    paletteChanged = Signal(str)                        # when palette has been changed,

    class WPaletteGrid(QWidget):
        """A palette widget

        Because signals for PaletteView class are not working...
        """
        colorOver = Signal(int, Swatch, QColor)             # when mouse is over a color (color index, color swatch, color)
        colorClicked = Signal(int, Swatch, QColor, int)       # when a color has been clicked (color index, color swatch, color, mouse button)

        def __init__(self, parent=None):
            super(WColorPalette.WPaletteGrid, self).__init__(parent)

            # track mouse move event on widget
            self.setMouseTracking(True)

            # current palette
            self.__palette=None
            # number of colors, columns and rows for palette
            self.__nbColors=0
            self.__columns=0
            self.__rows=0

            # cell size in pixel for palette grid
            self.__cellSize=0

            # color index on which mouse is over; -1 means outside palette grid
            self.__overIndex=-1
            # color cell coordinates on which mouse is over; as tuple(row, column) or None if no index
            self.__overCell=None

            # rendered grid in a pixmap cache
            self.__cachedGrid=None

            # QPen used for mouse over rendering
            self.__qPalette=QApplication.palette()
            self.__penOver=QPen(self.__qPalette.color(QPalette.Base))
            self.__penOver.setWidth(3)

            self.__idealSize=QSize()

        def __colorRect(self, row, column):
            """Return a QRect for a color square in grid"""
            return QRect(column * (1 + self.__cellSize), row *(1 + self.__cellSize), self.__cellSize, self.__cellSize)

        def __renderCache(self):
            """Render current grid in cache"""
            if self.__palette is None or self.__columns==0:
                self.__cachedGrid=None
                return


            # generate pixmap cache
            self.__cachedGrid=QPixmap(self.__idealSize)
            self.__cachedGrid.fill(self.__qPalette.color(QPalette.Base))

            noColorPixMap=checkerBoardImage(self.__cellSize, self.__cellSize)

            painter=QPainter()
            painter.begin(self.__cachedGrid)

            for row in range(self.__rows):
                for col in range(self.__columns):
                    color=self.colorFromRowColumn(row, col)
                    if color:
                        painter.fillRect(self.__colorRect(row, col), QBrush(color))
                    else:
                        # no color defined, let the checker board be displayed
                        painter.drawPixmap(self.__colorRect(row, col).topLeft(), noColorPixMap)

            painter.end()

        def invalidate(self):
            self.__cachedGrid=None
            # calculate pixel size of a color square
            # total width - number of columns ==> because keep 1 pixel per column
            # as separator
            self.__cellSize=(self.width() - self.__columns)//self.__columns

            # recalculate size according to:
            # - current width
            # - current cell size
            # - number of rows
            self.__idealSize=QSize(self.width(), (self.__cellSize+1)*self.__rows)

            # and set ideal height as minimal height for widget
            self.setMinimumHeight(self.__idealSize.height())

        def resizeEvent(self, event):
            """Widget is resized, need to invalidate pixmap cache"""
            self.__cachedGrid=None
            super(WColorPalette.WPaletteGrid, self).resizeEvent(event)
            self.invalidate()

        def paintEvent(self, event):
            """refresh widget content"""
            if self.__cachedGrid is None:
                # cache is not valid anymore, regenerate it
                self.__renderCache()

                if self.__cachedGrid is None:
                    # wow big problem here!
                    # hope it will never occur :)
                    super(WColorPalette.WPaletteGrid, self).paintEvent(event)
                    return

            painter = QPainter(self)
            painter.drawPixmap(QPoint(0, 0), self.__cachedGrid)

            if not self.__overCell is None:
                painter.setPen(self.__penOver)
                painter.setBrush(QBrush(Qt.NoBrush))
                painter.drawRect(self.__colorRect(self.__overCell[0], self.__overCell[1])-QMargins(0,0,1,1))

        def mousePressEvent(self, event):
            """A mouse button is clicked on widget"""
            if isinstance(self.__overIndex, int) and self.__overIndex>-1:
                swatch=self.colorFromIndex(self.__overIndex, False)
                if swatch.isValid():
                    qColor=self.colorFromIndex(self.__overIndex, True)
                else:
                    qColor=QColor(Qt.transparent)
                self.colorClicked.emit(self.__overIndex, swatch, qColor, event.buttons())
            else:
                super(WColorPalette.WPaletteGrid, self).mousePressEvent(event)

        def mouseMoveEvent(self, event):
            """Mouse has been moved over widget"""
            pos=event.localPos()

            # calculate (row,column) cell in grid from current mouse position
            row=int(pos.y()//(self.__cellSize+1))
            column=int(pos.x()//(self.__cellSize+1))

            # determinate color index
            overIndex=self.colorIndex(row, column)
            if overIndex>-1:
                self.__overIndex=overIndex
                self.__overCell=(row, column)
            elif self.__overIndex>-1:
                self.__overIndex=-1
                self.__overCell=None
            else:
                return

            # redraw palette to display marker over cell
            self.update()

            if isinstance(self.__overIndex, int) and self.__overIndex>-1:
                swatch=self.colorFromIndex(self.__overIndex, False)
                if swatch.isValid():
                    qColor=self.colorFromIndex(self.__overIndex, True)
                else:
                    qColor=QColor(Qt.transparent)
                self.colorOver.emit(self.__overIndex, swatch, qColor)
            else:
                self.colorOver.emit(-1, Swatch(), QColor())

        def leaveEvent(self, event):
            """Mouse is not over widget anymore"""
            self.__overIndex=-1
            self.__overCell=None
            self.update()
            self.colorOver.emit(-1, Swatch(), QColor())

        def idealSize(self):
            """Return ideal size"""
            return self.__idealSize

        def colorIndex(self, row, column):
            """return color index for given row/column

            If no color exist for given row/column, -1 is returned
            """
            if column<0 or column>=self.__columns or row<0 or row>=self.__rows:
                return -1

            return int(row * self.__columns + column)

        def colorCoordinates(self, index):
            """Return a tuple(row, column) of given color `index` in grid

            If index is not valid, return None
            """
            if index<0 or index>=self.__nbColors:
                return None

            row = int(index//self.__columns)
            column = int(index - (self.__columns * row))

            return (row, column)

        def colorFromIndex(self, index, asQColor=True):
            """Return color from given index

            If `asQColor`is True, return a QColor otherwise return a krita Swatch

            Return None is index is not valid or (if asked for QColor) if no color is defined for index
            """
            if index<0 or self.__palette is None:
                return None

            color=self.__palette.colorSetEntryByIndex(index)

            if asQColor:
                if not color.isValid():
                    return None
                if Krita.instance().activeWindow():
                    if Krita.instance().activeWindow().activeView():
                        return color.color().colorForCanvas(Krita.instance().activeWindow().activeView().canvas())
            else:
                return color

            return None

        def colorFromRowColumn(self, row, column, asQColor=True):
            """Return QColor for given row color

            If no color exist for given row/column, None is returned

            If `asQColor` is True (default), return a QColor otherwise return swatch
            """
            colorIndex=self.colorIndex(row, column)
            if colorIndex<0 or self.__palette is None:
                return None

            return self.colorFromIndex(colorIndex, asQColor)

        def setPalette(self, palette):
            """Set current palette"""
            if isinstance(palette, Palette):
                self.__palette=palette
                self.__nbColors=self.__palette.colorsCountTotal()
                self.__columns=self.__palette.columnCount()
                self.__rows=math.ceil(self.__nbColors/self.__columns)
                self.invalidate()
                #self.update()

        def palette(self):
            """Return current applied palette"""
            return self.__palette

    def __init__(self, parent=None):
        super(WColorPalette, self).__init__(parent)

        self.__layout = QVBoxLayout(self)

        self.__cbPalettes = QComboBox()
        self.__scrollArea = QScrollArea()
        self.__pgPalette = WColorPalette.WPaletteGrid(self.__scrollArea)

        self.__scrollArea.setWidgetResizable(True)
        self.__scrollArea.setWidget(self.__pgPalette)
        self.__scrollArea.setFrameStyle(QFrame.NoFrame)
        # note:
        #   QScrollArea > QWidget > QScrollBar { background: 0; }
        #   => setting a number allows to keep the default scrollbar style
        self.__scrollArea.setStyleSheet("""
QScrollArea { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollArea > QWidget > QScrollBar { background: 0; }
""")

        self.__layout.addWidget(self.__cbPalettes)
        self.__layout.addWidget(self.__scrollArea)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(3)

        # list of palettes (key=palette name / value=Palette())
        self.__palettes={}
        # current palette (name)
        self.__palette=None

        self.__cbPalettes.currentTextChanged.connect(self.__paletteChanged)

        self.__pgPalette.colorOver.connect(self.__colorOver)
        self.__pgPalette.colorClicked.connect(self.__colorClicked)

        self.setPalettes()

    def __paletteChanged(self, palette):
        """Palette has been changed in list"""
        self.__palette=palette
        self.__pgPalette.setPalette(self.__palettes[self.__palette])
        self.paletteChanged.emit(palette)

    def __colorOver(self, index, swatch, color):
        """Mouse over a color"""
        self.colorOver.emit(index, swatch, color)

    def __colorClicked(self, index, swatch, color, buttons):
        """Mouse over a color"""
        self.colorClicked.emit(index, swatch, color, buttons)

    def updateHeight(self):
        iSize=self.__pgPalette.idealSize()
        if iSize.width()==-1:
            height=int(0.7 * self.width())
        else:
            height=min(iSize.height(), int(0.7 * self.width()))

        if self.__cbPalettes.isVisible():
            height+=self.__cbPalettes.height()+3

        self.setMinimumHeight(height + self.__cbPalettes.height())

    def palette(self):
        """Return current selected palette"""
        return self.__palette

    def setPalette(self, palette):
        """Set current selected palette"""
        if palette in self.__palettes and palette!=self.__palette:
            self.__cbPalettes.setCurrentText(palette)

    def palettes(self):
        """Return a dictionary of palettes resources managed by widget"""
        return {name: self.__palette }

    def setPalettes(self, palettes=None):
        """Set list of palettes managed by widgets

        If `palettes` is None, widget will manage and expose all Krita's palettes
        If `palettes` is an empty list, widget will manage the "Default" palette only
        If `palettes` is a list(<str>), widget will manage the palettes from list
        """
        allPalettes=Krita.instance().resources("palette")

        if palettes is None:
            self.__palettes={palette: Palette(allPalettes[palette]) for palette in allPalettes}
        elif isinstance(palettes, str) and palettes.strip()!='':
            # use the default
            self.setPalettes([palettes])
        elif isinstance(palettes, list) and len(palettes)==0:
            # use the default
            self.setPalettes(['Default'])
        elif isinstance(palettes, list) and len(palettes)>1:
            # use the default
            self.__palettes={palette: Palette(allPalettes[palette]) for palette in palettes if palette in allPalettes}

            if len(self.__palettes)==0:
                # None of given palettes is available??
                self.setPalettes(['Default'])

        # Initialise combox
        self.__cbPalettes.clear()
        for palette in self.__palettes:
            self.__cbPalettes.addItem(palette)

        self.__cbPalettes.model().sort(0)

        self.__cbPalettes.setVisible(len(self.__palettes)>1)

        if 'Default' in self.__palettes:
            self.setPalette('Default')
        else:
            self.setPalette(list(self.__palettes.keys())[0])



class WColorPicker(QWidget):
    """A color picker"""
    colorUpdated = Signal(QColor)       # when color is changed from user interface
    colorChanged = Signal(QColor)       # when color is changed programmatically
    uiChanged = Signal()

    __COLOR_NONE=0
    __COLOR_WHEEL=1
    __COLOR_RED=2
    __COLOR_GREEN=3
    __COLOR_BLUE=4
    __COLOR_CYAN=5
    __COLOR_MAGENTA=6
    __COLOR_YELLOW=7
    __COLOR_BLACK=8
    __COLOR_HUE=9
    __COLOR_SATURATION=10
    __COLOR_VALUE=11
    __COLOR_LIGHTNESS=12
    __COLOR_ALPHA=13
    __COLOR_COMPLEMENTARY=20
    __COLOR_PALETTE=30
    __COLOR_CSSRGB=40

    OPTION_MENU_RGB=        0b0000000000000001
    OPTION_MENU_CMYK=       0b0000000000000010
    OPTION_MENU_HSV=        0b0000000000000100
    OPTION_MENU_HSL=        0b0000000000001000
    OPTION_MENU_ALPHA=      0b0000000000010000
    OPTION_MENU_CSSRGB=     0b0000000000100000
    OPTION_MENU_COLCOMP=    0b0000000001000000

    OPTION_MENU_COLWHEEL=   0b0001000000000000
    OPTION_MENU_PALETTE=    0b0010000000000000
    OPTION_MENU_UICOMPACT=  0b0100000000000000
    OPTION_MENU_COLPREVIEW= 0b1000000000000000

    OPTION_MENU_ALL=        0b1111111111111111  # All

    def __init__(self, color=None, parent=None):
        super(WColorPicker, self).__init__(parent)

        self.__inUpdate=True

        self.__compactWidth=350
        self.__normalWidth=450

        # compact ui let interface be smaller
        self.__optionCompactUi=True     # fored to false at the end of init
        self.__optionShowPreviewColor=True
        self.__optionShowColorCssRGB=True
        self.__optionShowColorWheel=True
        self.__optionShowColorPalette=False

        # "Show" option define which sliders are visible or not
        # individual sliders can't be visible/hidden; only group of sliders (RGB, CMYK, ...)
        self.__optionShowColorRGB=True
        self.__optionShowColorCMYK=True
        self.__optionShowColorHSV=True
        self.__optionShowColorHSL=True
        self.__optionShowColorAlpha=True

        # Display color combination type
        self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_NONE

        # define if value are displayed as pct or value
        self.__optionDisplayAsPctRGB=False
        self.__optionDisplayAsPctCMYK=False
        self.__optionDisplayAsPctHSV=False
        self.__optionDisplayAsPctHSL=False
        self.__optionDisplayAsPctAlpha=False

        # options to define which options are available in context menu
        self.__optionMenu=WColorPicker.OPTION_MENU_ALL

        self.__optionAllowRightClick=False

        # --
        self.__color=QColor()
        self.__colorHue=QColor()
        self.__layout = QVBoxLayout(self)

        self.__contextMenu=QMenu('Options')
        self.__initMenu()

        self.__colorPalette=WColorPalette()
        self.__colorPalette.setVisible(self.__optionShowColorPalette)
        self.__colorPalette.paletteChanged.connect(self.__colorPaletteChanged)
        self.__colorPalette.colorClicked.connect(self.__colorPaletteClicked)

        self.__colorWheel=WColorWheel(self.__color)

        self.__colorComplementary=WColorComplementary(self.__color)
        self.__colorComplementary.colorClicked.connect(self.__colorComplementaryClicked)

        self.__colorCssEdit=WColorCssEdit(self)

        self.__colorSliderRed=WColorSlider('red')
        self.__colorSliderGreen=WColorSlider('green')
        self.__colorSliderBlue=WColorSlider('blue')
        self.__colorSliderCyan=WColorSlider('cyan')
        self.__colorSliderMagenta=WColorSlider('magenta')
        self.__colorSliderYellow=WColorSlider('yellow')
        self.__colorSliderBlack=WColorSlider('black')
        self.__colorSliderHue=WColorSlider('hue')
        self.__colorSliderSaturation=WColorSlider('saturation')
        self.__colorSliderValue=WColorSlider('value')
        self.__colorSliderLightness=WColorSlider('lightness')
        self.__colorSliderAlpha=WColorSlider('alpha')

        self.__colorWheel.colorUpdated.connect(self.__colorWheelChanged)
        self.__colorCssEdit.colorUpdated.connect(self.__colorCssRGBChanged)
        self.__colorSliderRed.valueUpdated.connect(self.__colorRChanged)
        self.__colorSliderGreen.valueUpdated.connect(self.__colorGChanged)
        self.__colorSliderBlue.valueUpdated.connect(self.__colorBChanged)
        self.__colorSliderCyan.valueUpdated.connect(self.__colorCChanged)
        self.__colorSliderMagenta.valueUpdated.connect(self.__colorMChanged)
        self.__colorSliderYellow.valueUpdated.connect(self.__colorYChanged)
        self.__colorSliderBlack.valueUpdated.connect(self.__colorKChanged)
        self.__colorSliderHue.valueUpdated.connect(self.__colorHChanged)
        self.__colorSliderSaturation.valueUpdated.connect(self.__colorSChanged)
        self.__colorSliderValue.valueUpdated.connect(self.__colorVChanged)
        self.__colorSliderLightness.valueUpdated.connect(self.__colorLChanged)
        self.__colorSliderAlpha.valueUpdated.connect(self.__colorAChanged)


        self.__layout.addWidget(self.__colorPalette)
        self.__layout.addSpacing(4)
        self.__layout.addWidget(self.__colorWheel)
        self.__layout.addWidget(self.__colorComplementary)
        self.__layout.addWidget(self.__colorCssEdit)
        self.__layout.addWidget(self.__colorSliderRed)
        self.__layout.addWidget(self.__colorSliderGreen)
        self.__layout.addWidget(self.__colorSliderBlue)
        self.__layout.addWidget(self.__colorSliderCyan)
        self.__layout.addWidget(self.__colorSliderMagenta)
        self.__layout.addWidget(self.__colorSliderYellow)
        self.__layout.addWidget(self.__colorSliderBlack)
        self.__layout.addWidget(self.__colorSliderHue)
        self.__layout.addWidget(self.__colorSliderSaturation)
        self.__layout.addWidget(self.__colorSliderValue)
        self.__layout.addWidget(self.__colorSliderLightness)
        self.__layout.addWidget(self.__colorSliderAlpha)

        self.__layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.__layout)

        self.__colorWheel.setMinimumSize(350,350)
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum))

        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setOptionCompactUi(False)
        self.setColor(color)

        self.__inUpdate=False
        self.__updateSize()

    def __initMenu(self):
        """Initialise context menu"""
        self.__actionShowCompactUi = QAction(i18n('Compact UI'), self)
        self.__actionShowCompactUi.toggled.connect(self.setOptionCompactUi)
        self.__actionShowCompactUi.setCheckable(True)

        self.__actionShowCssRGB = QAction(i18n('CSS Color code'), self)
        self.__actionShowCssRGB.toggled.connect(self.setOptionShowCssRgb)
        self.__actionShowCssRGB.setCheckable(True)

        self.__actionShowColorPalette = QAction(i18n('Palette'), self)
        self.__actionShowColorPalette.toggled.connect(self.setOptionShowColorPalette)
        self.__actionShowColorPalette.setCheckable(True)

        self.__subMenuColorWheel = self.__contextMenu.addMenu('Color wheel')
        self.__actionShowColorWheel = QAction(i18n('Show'), self)
        self.__actionShowColorWheel.toggled.connect(self.setOptionShowColorWheel)
        self.__actionShowColorWheel.setCheckable(True)
        self.__subMenuColorWheel.addAction(self.__actionShowColorWheel)
        self.__actionShowPreviewColor = QAction(i18n('Preview color'), self)
        self.__actionShowPreviewColor.toggled.connect(self.setOptionShowPreviewColor)
        self.__actionShowPreviewColor.setCheckable(True)
        self.__subMenuColorWheel.addAction(self.__actionShowPreviewColor)

        self.__subMenuColorCombination = self.__contextMenu.addMenu('Color combination')
        self.__actionShowColorCombinationNone = QAction(i18n('None'), self)
        self.__actionShowColorCombinationNone.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationNone.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationNone)
        self.__actionShowColorCombinationMono = QAction(i18n('Monochromatic'), self)
        self.__actionShowColorCombinationMono.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationMono.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationMono)
        self.__actionShowColorCombinationAnalog = QAction(i18n('Analogous'), self)
        self.__actionShowColorCombinationAnalog.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationAnalog.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationAnalog)
        self.__actionShowColorCombinationComplementary = QAction(i18n('Complementary'), self)
        self.__actionShowColorCombinationComplementary.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationComplementary.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationComplementary)
        self.__actionShowColorCombinationTriadic = QAction(i18n('Triadic'), self)
        self.__actionShowColorCombinationTriadic.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationTriadic.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationTriadic)
        self.__actionShowColorCombinationTetradic = QAction(i18n('Tetradic'), self)
        self.__actionShowColorCombinationTetradic.toggled.connect(self.setOptionShowColorCombination)
        self.__actionShowColorCombinationTetradic.setCheckable(True)
        self.__subMenuColorCombination.addAction(self.__actionShowColorCombinationTetradic)


        subMenuColorCombinationGrp = QActionGroup(self)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationNone)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationMono)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationAnalog)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationComplementary)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationTriadic)
        subMenuColorCombinationGrp.addAction(self.__actionShowColorCombinationTetradic)


        self.__subMenuRGB = self.__contextMenu.addMenu('RGB')
        self.__actionShowColorRGB = QAction(i18n('Show RGB'), self)
        self.__actionShowColorRGB.toggled.connect(self.setOptionShowColorRGB)
        self.__actionShowColorRGB.setCheckable(True)
        self.__actionShowColorRGB.setChecked(self.__optionShowColorRGB)
        self.__subMenuRGB.addAction(self.__actionShowColorRGB)
        self.__actionDisplayAsPctColorRGB = QAction(i18n('Display as percentage'), self)
        self.__actionDisplayAsPctColorRGB.toggled.connect(self.setOptionDisplayAsPctColorRGB)
        self.__actionDisplayAsPctColorRGB.setCheckable(True)
        self.__actionDisplayAsPctColorRGB.setChecked(self.__optionDisplayAsPctRGB)
        self.__subMenuRGB.addAction(self.__actionDisplayAsPctColorRGB)

        self.__subMenuCMYK = self.__contextMenu.addMenu('CMYK')
        self.__actionShowColorCMYK = QAction(i18n('Show CMYK'), self)
        self.__actionShowColorCMYK.toggled.connect(self.setOptionShowColorCMYK)
        self.__actionShowColorCMYK.setCheckable(True)
        self.__actionShowColorCMYK.setChecked(self.__optionShowColorCMYK)
        self.__subMenuCMYK.addAction(self.__actionShowColorCMYK)
        self.__actionDisplayAsPctColorCMYK = QAction(i18n('Display as percentage'), self)
        self.__actionDisplayAsPctColorCMYK.toggled.connect(self.setOptionDisplayAsPctColorCMYK)
        self.__actionDisplayAsPctColorCMYK.setCheckable(True)
        self.__actionDisplayAsPctColorCMYK.setChecked(self.__optionDisplayAsPctCMYK)
        self.__subMenuCMYK.addAction(self.__actionDisplayAsPctColorCMYK)

        self.__subMenuHSV = self.__contextMenu.addMenu('HSV')
        self.__actionShowColorHSV = QAction(i18n('Show HSV'), self)
        self.__actionShowColorHSV.toggled.connect(self.setOptionShowColorHSV)
        self.__actionShowColorHSV.setCheckable(True)
        self.__actionShowColorHSV.setChecked(self.__optionShowColorHSV)
        self.__subMenuHSV.addAction(self.__actionShowColorHSV)
        self.__actionDisplayAsPctColorHSV = QAction(i18n('Display as percentage'), self)
        self.__actionDisplayAsPctColorHSV.toggled.connect(self.setOptionDisplayAsPctColorHSV)
        self.__actionDisplayAsPctColorHSV.setCheckable(True)
        self.__actionDisplayAsPctColorHSV.setChecked(self.__optionDisplayAsPctHSV)
        self.__subMenuHSV.addAction(self.__actionDisplayAsPctColorHSV)

        self.__subMenuHSL = self.__contextMenu.addMenu('HSL')
        self.__actionShowColorHSL = QAction(i18n('Show HSL'), self)
        self.__actionShowColorHSL.toggled.connect(self.setOptionShowColorHSL)
        self.__actionShowColorHSL.setCheckable(True)
        self.__actionShowColorHSL.setChecked(self.__optionShowColorHSL)
        self.__subMenuHSL.addAction(self.__actionShowColorHSL)
        self.__actionDisplayAsPctColorHSL = QAction(i18n('Display as percentage'), self)
        self.__actionDisplayAsPctColorHSL.toggled.connect(self.setOptionDisplayAsPctColorHSL)
        self.__actionDisplayAsPctColorHSL.setCheckable(True)
        self.__actionDisplayAsPctColorHSL.setChecked(self.__optionDisplayAsPctHSL)
        self.__subMenuHSL.addAction(self.__actionDisplayAsPctColorHSL)

        self.__subMenuAlpha = self.__contextMenu.addMenu('Alpha')
        self.__actionShowColorAlpha = QAction(i18n('Show Alpha'), self)
        self.__actionShowColorAlpha.toggled.connect(self.setOptionShowColorAlpha)
        self.__actionShowColorAlpha.setCheckable(True)
        self.__actionShowColorAlpha.setChecked(self.__optionShowColorAlpha)
        self.__subMenuAlpha.addAction(self.__actionShowColorAlpha)
        self.__actionDisplayAsPctColorAlpha = QAction(i18n('Display as percentage'), self)
        self.__actionDisplayAsPctColorAlpha.toggled.connect(self.setOptionDisplayAsPctColorAlpha)
        self.__actionDisplayAsPctColorAlpha.setCheckable(True)
        self.__actionDisplayAsPctColorAlpha.setChecked(self.__optionDisplayAsPctAlpha)
        self.__subMenuAlpha.addAction(self.__actionDisplayAsPctColorAlpha)

        self.__contextMenu.addAction(self.__actionShowCompactUi)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addMenu(self.__subMenuColorWheel)
        self.__contextMenu.addAction(self.__actionShowColorPalette)
        self.__contextMenu.addMenu(self.__subMenuColorCombination)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionShowCssRGB)
        self.__contextMenu.addSeparator()
        self.__contextMenu.addMenu(self.__subMenuRGB)
        self.__contextMenu.addMenu(self.__subMenuCMYK)
        self.__contextMenu.addMenu(self.__subMenuHSV)
        self.__contextMenu.addMenu(self.__subMenuHSL)
        self.__contextMenu.addMenu(self.__subMenuAlpha)

    def __updateSize(self):
        """Update size according to current widget visible"""
        if self.__inUpdate:
            return
        self.adjustSize()
        self.uiChanged.emit()

    def contextMenuEvent(self, event):
        """Display context menu, updated according to current options"""
        if self.__optionMenu==0:
            # no menu allowed!
            return
        self.__actionShowCompactUi.setChecked(self.__optionCompactUi)
        self.__actionShowPreviewColor.setChecked(self.__optionShowPreviewColor)
        self.__actionShowColorPalette.setChecked(self.__optionShowColorPalette)
        self.__actionShowColorWheel.setChecked(self.__optionShowColorWheel)
        self.__actionShowCssRGB.setChecked(self.__optionShowColorCssRGB)

        self.__actionShowColorCombinationNone.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_NONE)
        self.__actionShowColorCombinationMono.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_MONOCHROMATIC)
        self.__actionShowColorCombinationAnalog.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_ANALOGOUS)
        self.__actionShowColorCombinationComplementary.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_COMPLEMENTARY)
        self.__actionShowColorCombinationTriadic.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_TRIADIC)
        self.__actionShowColorCombinationTetradic.setChecked(self.__optionShowColorCombination==WColorComplementary.COLOR_COMBINATION_TETRADIC)
        self.__actionShowColorRGB.setChecked(self.__optionShowColorRGB)
        self.__actionShowColorCMYK.setChecked(self.__optionShowColorCMYK)
        self.__actionShowColorHSV.setChecked(self.__optionShowColorHSV)
        self.__actionShowColorHSL.setChecked(self.__optionShowColorHSL)
        self.__actionShowColorAlpha.setChecked(self.__optionShowColorAlpha)

        self.__actionDisplayAsPctColorRGB.setChecked(self.__optionDisplayAsPctRGB)
        self.__actionDisplayAsPctColorCMYK.setChecked(self.__optionDisplayAsPctCMYK)
        self.__actionDisplayAsPctColorHSV.setChecked(self.__optionDisplayAsPctHSV)
        self.__actionDisplayAsPctColorHSL.setChecked(self.__optionDisplayAsPctHSL)
        self.__actionDisplayAsPctColorAlpha.setChecked(self.__optionDisplayAsPctAlpha)

        self.__actionShowCompactUi.setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_UICOMPACT) == WColorPicker.OPTION_MENU_UICOMPACT)
        self.__actionShowPreviewColor.setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_COLPREVIEW) == WColorPicker.OPTION_MENU_COLPREVIEW)
        self.__actionShowCssRGB.setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_CSSRGB) == WColorPicker.OPTION_MENU_CSSRGB)

        self.__subMenuRGB.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_RGB) == WColorPicker.OPTION_MENU_RGB)
        self.__subMenuCMYK.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_CMYK) == WColorPicker.OPTION_MENU_CMYK)
        self.__subMenuHSV.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_HSV) == WColorPicker.OPTION_MENU_HSV)
        self.__subMenuHSL.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_HSL) == WColorPicker.OPTION_MENU_HSL)
        self.__subMenuAlpha.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_ALPHA) == WColorPicker.OPTION_MENU_ALPHA)
        self.__subMenuColorCombination.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_COLCOMP) == WColorPicker.OPTION_MENU_COLCOMP)
        self.__subMenuColorWheel.menuAction().setVisible( (self.__optionMenu & WColorPicker.OPTION_MENU_COLWHEEL) == WColorPicker.OPTION_MENU_COLWHEEL)

        self.__contextMenu.exec_(event.globalPos())

    def __colorComplementaryClicked(self, color, colorIndex):
        """A complementary color has been cliked, apply it"""
        self.__color=color
        self.__updateColor(WColorPicker.__COLOR_COMPLEMENTARY)

    def __colorWheelChanged(self, color):
        """Color from color wheel has been changed"""
        self.__color=self.__colorWheel.color()
        self.__updateColor(WColorPicker.__COLOR_WHEEL)

    def __colorCssRGBChanged(self, color):
        """Color from CSS color code editor has been changed"""
        self.__color=color
        self.__updateColor(WColorPicker.__COLOR_CSSRGB)

    def __colorPaletteChanged(self, palette):
        """Color palette has been changed"""
        self.__colorPalette.updateHeight()
        self.__updateSize()

    def __colorPaletteClicked(self, index, swatch, color, buttons):
        """Color palette has been changed"""
        if index>-1 and swatch.isValid():
            if self.__optionAllowRightClick or (int(buttons) & Qt.RightButton != Qt.RightButton):
                self.__color=color
                self.__updateColor(WColorPicker.__COLOR_PALETTE)

    def __colorRChanged(self, value):
        """Color from Red color slider has been changed"""
        self.__color.setRed(int(value))
        self.__updateColor(WColorPicker.__COLOR_RED)

    def __colorGChanged(self, value):
        """Color from Green color slider has been changed"""
        self.__color.setGreen(int(value))
        self.__updateColor(WColorPicker.__COLOR_GREEN)

    def __colorBChanged(self, value):
        """Color from Blue color slider has been changed"""
        self.__color.setBlue(int(value))
        self.__updateColor(WColorPicker.__COLOR_BLUE)

    def __colorCChanged(self, value):
        """Color from Cyan color slider has been changed"""
        self.__color.setCmyk(int(value), self.__color.magenta(), self.__color.yellow(), self.__color.black())
        self.__updateColor(WColorPicker.__COLOR_CYAN)

    def __colorMChanged(self, value):
        """Color from Magenta color slider has been changed"""
        self.__color.setCmyk(self.__color.cyan(), int(value), self.__color.yellow(), self.__color.black())
        self.__updateColor(WColorPicker.__COLOR_MAGENTA)

    def __colorYChanged(self, value):
        """Color from Yellow color slider has been changed"""
        self.__color.setCmyk(self.__color.cyan(), self.__color.magenta(), int(value), self.__color.black())
        self.__updateColor(WColorPicker.__COLOR_YELLOW)

    def __colorKChanged(self, value):
        """Color from Black color slider has been changed"""
        self.__color.setCmyk(self.__color.cyan(), self.__color.magenta(), self.__color.yellow(), int(value))
        self.__updateColor(WColorPicker.__COLOR_BLACK)

    def __colorHChanged(self, value):
        """Color from Hue color slider has been changed"""
        self.__color.setHsv(int(value), self.__color.saturation(), self.__color.value())
        self.__updateColor(WColorPicker.__COLOR_HUE)

    def __colorSChanged(self, value):
        """Color from Saturation color slider has been changed"""
        self.__color.setHsv(self.__colorHue.hue(), int(value), self.__color.value())
        self.__updateColor(WColorPicker.__COLOR_SATURATION)

    def __colorVChanged(self, value):
        """Color from Value color slider has been changed"""
        self.__color.setHsv(self.__colorHue.hue(), self.__color.saturation(), int(value))
        self.__updateColor(WColorPicker.__COLOR_VALUE)

    def __colorLChanged(self, value):
        """Color from Lightness color slider has been changed"""
        self.__color.setHsl(self.__colorHue.hue(), self.__color.saturation(), int(value))
        self.__updateColor(WColorPicker.__COLOR_LIGHTNESS)

    def __colorAChanged(self, value):
        """Color from Green color slider has been changed"""
        self.__color.setAlpha(int(value))
        self.__updateColor(WColorPicker.__COLOR_ALPHA)

    def __updateColor(self, updating=__COLOR_NONE):
        """Update color interface to current color"""
        if updating==WColorPicker.__COLOR_COMPLEMENTARY:
            self.__colorHue=QColor.fromHsv(self.__color.hue(), 255, 255)
        else:
            self.__colorHue=self.__colorWheel.colorHue()

        self.__colorComplementary.setColor(self.__color)

        if updating!=WColorPicker.__COLOR_WHEEL:
            self.__colorWheel.setColor(self.__color)
        if updating!=WColorPicker.__COLOR_RED:
            self.__colorSliderRed.setValue(self.__color.red())
        if updating!=WColorPicker.__COLOR_GREEN:
            self.__colorSliderGreen.setValue(self.__color.green())
        if updating!=WColorPicker.__COLOR_BLUE:
            self.__colorSliderBlue.setValue(self.__color.blue())
        if updating!=WColorPicker.__COLOR_CYAN:
            self.__colorSliderCyan.setValue(self.__color.cyan())
        if updating!=WColorPicker.__COLOR_MAGENTA:
            self.__colorSliderMagenta.setValue(self.__color.magenta())
        if updating!=WColorPicker.__COLOR_YELLOW:
            self.__colorSliderYellow.setValue(self.__color.yellow())
        if updating!=WColorPicker.__COLOR_BLACK:
            self.__colorSliderBlack.setValue(self.__color.black())
        if updating!=WColorPicker.__COLOR_HUE:
            self.__colorSliderHue.setValue(self.__color.hue())
        if updating!=WColorPicker.__COLOR_SATURATION:
            self.__colorSliderSaturation.setBgColor(self.__colorHue)
            self.__colorSliderSaturation.setValue(self.__color.saturation())
        if updating!=WColorPicker.__COLOR_VALUE:
            self.__colorSliderValue.setBgColor(self.__colorHue)
            self.__colorSliderValue.setValue(self.__color.value())
        if updating!=WColorPicker.__COLOR_LIGHTNESS:
            self.__colorSliderLightness.setBgColor(self.__colorHue)
            self.__colorSliderLightness.setValue(self.__color.lightness())
        if updating!=WColorPicker.__COLOR_ALPHA:
            self.__colorSliderAlpha.setFgGradient([(0, QColor(Qt.transparent)), (1, self.__colorHue)])
            self.__colorSliderAlpha.setValue(self.__color.alpha())
        if updating!=WColorPicker.__COLOR_CSSRGB:
            self.__colorCssEdit.setColor(self.__color)

        if updating!=WColorPicker.__COLOR_ALPHA:
            # when only alpha is modified, do not consider color is changed
            if updating==WColorPicker.__COLOR_NONE:
                # is none, consider it's a programmatically change
                self.__emitColorChanged()
            else:
                self.__emitColorUpdated()

    def __emitColorUpdated(self):
        """Emit signal when color has been updated (from mouse position)"""
        self.colorUpdated.emit(self.__color)

    def __emitColorChanged(self):
        """Emit signal when color has been changed (programmatically)"""
        self.colorChanged.emit(self.__color)

    def optionMenu(self):
        """Return current menu options"""
        return self.__optionMenu

    def setOptionMenu(self, value):
        """Return current menu options"""
        if isinstance(value, int):
            self.__optionMenu=value

    def color(self, value):
        """Get current color"""
        return self.__color

    def setColor(self, value):
        """Set current color"""
        if value==self.__color or not isinstance(value, QColor):
            return


        self.__color=value
        self.__updateColor()

    def optionShowColorRGB(self):
        """Return if option 'show color RGB sliders' is active or not"""
        return self.__optionShowColorRGB

    def optionShowColorCMYK(self):
        """Return if option 'show color CMYK sliders' is active or not"""
        return self.__optionShowColorCMYK

    def optionShowColorHSV(self):
        """Return if option 'show color HSV sliders' is active or not"""
        return self.__optionShowColorHSV

    def optionShowColorHSL(self):
        """Return if option 'show color HSl sliders' is active or not"""
        return self.__optionShowColorHSL

    def optionShowColorAlpha(self):
        """Return if option 'show color Alpha sliders' is active or not"""
        return self.__optionShowColorAlpha

    def optionShowColorCssRGB(self):
        """Return if option 'show colorCssRGB entry' is active or not"""
        return self.__optionShowColorCssRGB

    def optionShowColorCombination(self):
        """Return current option 'show color combination' value"""
        return self.__optionShowColorCombination

    def optionShowColorPalette(self):
        """Return current option 'show color palette' value"""
        return self.__optionShowColorPalette

    def optionShowColorWheel(self):
        """Return current option 'show color wheel' value"""
        return self.__optionShowColorWheel

    def optionCompactUi(self):
        """Return if option 'small size' is active or not"""
        return self.__optionCompactUi

    def optionShowPreviewColor(self):
        """Return if option 'preview color' is active or not"""
        return self.__optionShowPreviewColor

    def optionDisplayAsPctColorRGB(self):
        """Return if option 'display color RGB as pct' is active or not"""
        return self.__optionDisplayAsPctRGB

    def optionDisplayAsPctColorCMYK(self):
        """Return if option 'display color CMYK as pct' is active or not"""
        return self.__optionDisplayAsPctCMYK

    def optionDisplayAsPctColorHSV(self):
        """Return if option 'display color HSV as pct' is active or not"""
        return self.__optionDisplayAsPctHSV

    def optionDisplayAsPctColorHSL(self):
        """Return if option 'display color HSL as pct' is active or not"""
        return self.__optionDisplayAsPctHSL

    def optionDisplayAsPctColorAlpha(self):
        """Return if option 'display color alpha as pct' is active or not"""
        return self.__optionDisplayAsPctAlpha

    def optionAllowRightClick(self):
        """Return True if right click on palette allows to select a color"""
        return self.__optionAllowRightClick

    def setOptionShowColorRGB(self, value):
        """Set option 'show color RGB sliders' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorRGB==value:
            return

        self.__optionShowColorRGB=value

        self.__colorSliderRed.setVisible(self.__optionShowColorRGB)
        self.__colorSliderGreen.setVisible(self.__optionShowColorRGB)
        self.__colorSliderBlue.setVisible(self.__optionShowColorRGB)
        self.__updateSize()

    def setOptionShowColorCMYK(self, value):
        """Set option 'show color CMYK sliders' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorCMYK==value:
            return

        self.__optionShowColorCMYK=value

        self.__colorSliderCyan.setVisible(self.__optionShowColorCMYK)
        self.__colorSliderMagenta.setVisible(self.__optionShowColorCMYK)
        self.__colorSliderYellow.setVisible(self.__optionShowColorCMYK)
        self.__colorSliderBlack.setVisible(self.__optionShowColorCMYK)
        self.__updateSize()

    def setOptionShowColorHSV(self, value):
        """Set option 'show color HSV sliders' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorHSV==value:
            return

        self.__optionShowColorHSV=value

        self.__colorSliderHue.setVisible(self.__optionShowColorHSV or self.__optionShowColorHSL)
        self.__colorSliderSaturation.setVisible(self.__optionShowColorHSV or self.__optionShowColorHSL)

        self.__colorSliderValue.setVisible(self.__optionShowColorHSV)
        self.__updateSize()

    def setOptionShowColorHSL(self, value):
        """Set option 'show color HSL sliders' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorHSL==value:
            return

        self.__optionShowColorHSL=value

        self.__colorSliderHue.setVisible(self.__optionShowColorHSV or self.__optionShowColorHSL)
        self.__colorSliderSaturation.setVisible(self.__optionShowColorHSV or self.__optionShowColorHSL)

        self.__colorSliderLightness.setVisible(self.__optionShowColorHSL)
        self.__updateSize()

    def setOptionShowColorAlpha(self, value):
        """Set option 'show color Alpha sliders' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorAlpha==value:
            return

        self.__optionShowColorAlpha=value

        self.__colorSliderAlpha.setVisible(self.__optionShowColorAlpha)
        self.__updateSize()

    def setOptionShowCssRgb(self, value):
        """Set option 'css color code' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorCssRGB==value:
            return

        self.__optionShowColorCssRGB=value

        self.__colorCssEdit.setVisible(self.__optionShowColorCssRGB)
        self.__updateSize()

    def setOptionShowColorCombination(self, value):
        """Set option 'color combination'

        If value is a boolean (True or False), option is defined automatically
        according to current
        """
        if self.__optionShowColorCombination==value or not(
                isinstance(value, bool) or value in [
                    WColorComplementary.COLOR_COMBINATION_NONE,
                    WColorComplementary.COLOR_COMBINATION_MONOCHROMATIC,
                    WColorComplementary.COLOR_COMBINATION_COMPLEMENTARY,
                    WColorComplementary.COLOR_COMBINATION_ANALOGOUS,
                    WColorComplementary.COLOR_COMBINATION_TRIADIC,
                    WColorComplementary.COLOR_COMBINATION_TETRADIC
                ]):
            return

        if isinstance(value, bool):
            if self.__actionShowColorCombinationNone.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_NONE
            elif self.__actionShowColorCombinationMono.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_MONOCHROMATIC
            elif self.__actionShowColorCombinationComplementary.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_COMPLEMENTARY
            elif self.__actionShowColorCombinationAnalog.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_ANALOGOUS
            elif self.__actionShowColorCombinationTriadic.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_TRIADIC
            elif self.__actionShowColorCombinationTetradic.isChecked():
                self.__optionShowColorCombination=WColorComplementary.COLOR_COMBINATION_TETRADIC
        else:
            self.__optionShowColorCombination=value

        self.__colorComplementary.setMode(self.__optionShowColorCombination)
        self.__updateSize()

    def setOptionShowColorPalette(self, value):
        """Set option 'palette' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorPalette==value:
            return

        self.__optionShowColorPalette=value

        self.__colorPalette.setVisible(self.__optionShowColorPalette)
        self.__colorPalette.updateHeight()
        self.__updateSize()

    def setOptionShowColorWheel(self, value):
        """Set option 'color wheel' is active or not"""
        if not isinstance(value, bool) or self.__optionShowColorWheel==value:
            return

        self.__optionShowColorWheel=value

        self.__colorWheel.setVisible(self.__optionShowColorWheel)
        self.__updateSize()

    def setOptionCompactUi(self, value):
        """Set if option 'small size' is active or not"""
        if not isinstance(value, bool) or self.__optionCompactUi==value:
            return

        self.__optionCompactUi=value

        if self.__optionCompactUi:
            fnt=self.font()
            fnt.setPointSize(int(fnt.pointSize() * 0.75))

            minSize=int(0.85 * self.__compactWidth)
            self.setMinimumWidth(minSize)
            self.setMaximumWidth(self.__compactWidth)
            self.__layout.setSpacing(1)
            self.__colorComplementary.setMinimumHeight(40)
            self.__colorComplementary.setMaximumHeight(60)
            self.__colorCssEdit.setMaximumHeight(22)
            self.__colorWheel.setMinimumSize(minSize,minSize)
            self.__colorPalette.setMinimumSize(minSize,0)

        else:
            fnt=QApplication.font()

            minSize=int(0.85 * self.__normalWidth)

            self.setMinimumWidth(minSize)
            self.setMaximumWidth(self.__normalWidth)
            self.__layout.setSpacing(4)
            self.__colorComplementary.setMinimumHeight(60)
            self.__colorComplementary.setMaximumHeight(80)
            self.__colorCssEdit.setMaximumHeight(99999)
            self.__colorWheel.setMinimumSize(minSize, minSize)
            self.__colorPalette.setMinimumSize(minSize, 0)

        self.setFont(fnt)

        self.__colorSliderRed.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderGreen.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderBlue.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderCyan.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderMagenta.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderYellow.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderBlack.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderHue.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderSaturation.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderValue.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderLightness.setOptionCompactUi(self.__optionCompactUi)
        self.__colorSliderAlpha.setOptionCompactUi(self.__optionCompactUi)
        self.__updateSize()

    def optionColorPalette(self):
        """Return current color palette name"""
        return self.__colorPalette.palette()

    def setOptionColorPalette(self, paletteName):
        """Set color palette"""
        return self.__colorPalette.setPalette(paletteName)

    def setOptionShowPreviewColor(self, value):
        """Set option 'color preview' is active or not"""
        if not isinstance(value, bool) or self.__optionShowPreviewColor==value:
            return

        self.__optionShowPreviewColor=value
        self.__colorWheel.setOptionPreviewColor(value)

    def setOptionDisplayAsPctColorRGB(self, value):
        """Set option 'display RGB  as pct' is active or not"""
        if not isinstance(value, bool) or self.__optionDisplayAsPctRGB==value:
            return

        self.__optionDisplayAsPctRGB=value
        self.__colorSliderRed.setOptionAsPct(self.__optionDisplayAsPctRGB)
        self.__colorSliderGreen.setOptionAsPct(self.__optionDisplayAsPctRGB)
        self.__colorSliderBlue.setOptionAsPct(self.__optionDisplayAsPctRGB)

    def setOptionDisplayAsPctColorCMYK(self, value):
        """Set option 'display CMYK  as pct' is active or not"""
        if not isinstance(value, bool) or self.__optionDisplayAsPctCMYK==value:
            return

        self.__optionDisplayAsPctCMYK=value
        self.__colorSliderCyan.setOptionAsPct(self.__optionDisplayAsPctCMYK)
        self.__colorSliderMagenta.setOptionAsPct(self.__optionDisplayAsPctCMYK)
        self.__colorSliderYellow.setOptionAsPct(self.__optionDisplayAsPctCMYK)
        self.__colorSliderBlack.setOptionAsPct(self.__optionDisplayAsPctCMYK)

    def setOptionDisplayAsPctColorHSV(self, value):
        """Set option 'display HSV  as pct' is active or not"""
        if not isinstance(value, bool) or self.__optionDisplayAsPctHSV==value:
            return

        # HSV and HSL share the same 'HS' slider then both must be set to same
        # display mode value
        self.__optionDisplayAsPctHSV=value
        self.__optionDisplayAsPctHSL=value
        self.__colorSliderHue.setOptionAsPct(self.__optionDisplayAsPctHSV)
        self.__colorSliderSaturation.setOptionAsPct(self.__optionDisplayAsPctHSV)
        self.__colorSliderValue.setOptionAsPct(self.__optionDisplayAsPctHSV)
        self.__colorSliderLightness.setOptionAsPct(self.__optionDisplayAsPctHSV)

    def setOptionDisplayAsPctColorHSL(self, value):
        """Set option 'display HSL  as pct' is active or not"""
        if not isinstance(value, bool) or self.__optionDisplayAsPctHSL==value:
            return

        # HSV and HSL share the same 'HS' slider then both must be set to same
        # display mode value
        self.__optionDisplayAsPctHSV=value
        self.__optionDisplayAsPctHSL=value
        self.__colorSliderHue.setOptionAsPct(self.__optionDisplayAsPctHSL)
        self.__colorSliderSaturation.setOptionAsPct(self.__optionDisplayAsPctHSL)
        self.__colorSliderValue.setOptionAsPct(self.__optionDisplayAsPctHSL)
        self.__colorSliderLightness.setOptionAsPct(self.__optionDisplayAsPctHSL)

    def setOptionDisplayAsPctColorAlpha(self, value):
        """Set option 'display Alpha as pct' is active or not"""
        if not isinstance(value, bool) or self.__optionDisplayAsPctAlpha==value:
            return

        self.__optionDisplayAsPctAlpha=value
        self.__colorSliderAlpha.setOptionAsPct(self.__optionDisplayAsPctAlpha)

    def setOptionAllowRightClick(self, value):
        """Set if right click on palette is allowed to select a color"""
        if isinstance(value, bool):
            self.__optionAllowRightClick=value

    def compactWidth(self):
        """Return compact width"""
        return self.__compactWidth

    def setCompactWidth(self, value):
        """Define compact width"""
        self.__compactWidth=value
        if self.__normalWidth<=self.__compactWidth:
            self.__normalWidth=int(self.__compactWidth * 0.3)
        # force compact ui refresh...
        self.__optionCompactUi=not self.__optionCompactUi
        self.setOptionCompactUi(not self.__optionCompactUi)

    def normalWidth(self):
        """Return normal width"""
        return self.__normalWidth

    def setNormalWidth(self, value):
        """Define compact width"""
        self.__normalWidth=value
        if self.__compactWidth<=self.__normalWidth:
            self.__compactWidth=int(self.__compactWidth * 0.7)
        # force compact ui refresh...
        self.__optionCompactUi=not self.__optionCompactUi
        self.setOptionCompactUi(not self.__optionCompactUi)

    def optionLayout(self):
        """Return a list of current layout options status"""
        returned=[]
        if self.__optionShowColorRGB:
            returned.append('colorRGB')
        if self.__optionShowColorCMYK:
            returned.append('colorCMYK')
        if self.__optionShowColorHSV:
            returned.append('colorHSV')
        if self.__optionShowColorHSL:
            returned.append('colorHSL')
        if self.__optionShowColorAlpha:
            returned.append('colorAlpha')
        if self.__optionShowColorCssRGB:
            returned.append('colorCssRGB')
        if self.__optionShowColorPalette:
            returned.append('colorPalette')
        if self.__optionShowColorWheel:
            returned.append('colorWheel')
        if self.__optionShowPreviewColor:
            returned.append('colorPreview')

        if self.__optionDisplayAsPctRGB:
            returned.append('colorRGB%')
        if self.__optionDisplayAsPctCMYK:
            returned.append('colorCMYK%')
        if self.__optionDisplayAsPctHSV:
            returned.append('colorHSV%')
        if self.__optionDisplayAsPctHSL:
            returned.append('colorHSL%')
        if self.__optionDisplayAsPctAlpha:
            returned.append('colorAlpha%')

        if self.__optionCompactUi:
            returned.append('compactUi')

        returned.append(f"colorCombination:{self.__optionShowColorCombination}")
        returned.append(f"colorPalette:{self.__colorPalette.palette()}")

        return returned

    def setOptionLayout(self, layout):
        """Set layout from given options"""
        if not (isinstance(layout, list) or isinstance(layout, tuple)):
            raise EInvalidType('Given `layout` must be a <list> or <tuple>')

        self.__inUpdate=True

        self.setOptionShowColorRGB('colorRGB' in layout)
        self.setOptionShowColorCMYK('colorCMYK' in layout)
        self.setOptionShowColorHSV('colorHSV' in layout)
        self.setOptionShowColorHSL('colorHSL' in layout)
        self.setOptionShowColorAlpha('colorAlpha' in layout)
        self.setOptionShowCssRgb('colorCssRGB' in layout)
        self.setOptionShowColorPalette('colorPalette' in layout)
        self.setOptionShowColorWheel('colorWheel' in layout)
        self.setOptionShowPreviewColor('colorPreview' in layout)

        self.setOptionDisplayAsPctColorRGB('colorRGB%' in layout)
        self.setOptionDisplayAsPctColorCMYK('colorCMYK%' in layout)
        self.setOptionDisplayAsPctColorHSV('colorHSV%' in layout)
        self.setOptionDisplayAsPctColorHSL('colorHSL%' in layout)
        self.setOptionDisplayAsPctColorAlpha('colorAlpha%' in layout)

        self.setOptionCompactUi('compactUi' in layout)

        for item in layout:
            if r:=re.match('colorPalette:(.*)', item):
                self.setOptionColorPalette(r.groups()[0])
            elif r:=re.match('colorCombination:(\d)', item):
                self.setOptionShowColorCombination(int(r.groups()[0]))

        self.__inUpdate=False
        self.__updateSize()
