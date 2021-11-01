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

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal,
        QRectF
    )
from PyQt5.QtWidgets import (
        QAction,
        QActionGroup,
        QGraphicsView,
        QGraphicsScene,
        QMenu
    )
from PyQt5.QtGui import (
        QImage,
        QPainterPath,
        QPalette,
        QPixmap
    )

from ..modules.imgutils import (
        checkerBoardBrush,
        buildIcon
    )
from ..pktk import *

# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------
class WImageView(QGraphicsView):
    """Display image with pan/zoom hability"""

    BG_BLACK = 0
    BG_WHITE = 1
    BG_NEUTRAL_GRAY = 2
    BG_TRANSPARENT = 3
    BG_CHECKER_BOARD = 4

    # Mouse button emit coordinates on image
    leftButtonPressed = Signal(float, float)
    rightButtonPressed = Signal(float, float)
    leftButtonReleased = Signal(float, float)
    rightButtonReleased = Signal(float, float)
    leftButtonDoubleClicked = Signal(float, float)
    rightButtonDoubleClicked = Signal(float, float)
    zoomChanged = Signal(float)

    def __init__(self, parent=None):
        """Initialise viewer"""
        def zoomToFit(dummy):
            self.setZoom(0.0)
        def zoom1x1(dummy):
            self.setZoom(1.0)
        def bgColorBlack(dummy):
            self.setBackgroundType(WImageView.BG_BLACK)
        def bgColorWhite(dummy):
            self.setBackgroundType(WImageView.BG_WHITE)
        def bgColorNGray(dummy):
            self.setBackgroundType(WImageView.BG_NEUTRAL_GRAY)
        def bgColorNone(dummy):
            self.setBackgroundType(WImageView.BG_TRANSPARENT)
        def bgColorCheckerBoard(dummy):
            self.setBackgroundType(WImageView.BG_CHECKER_BOARD)

        super(WImageView, self).__init__(parent)

        # Image is a QPixmap in a QGraphicsScene
        self.__gScene = QGraphicsScene()
        self.setScene(self.__gScene)

        # Handle for current image
        self.__bgImg = QPixmap()
        self.__imgBgHandle = self.__imgHandle = self.__gScene.addPixmap(self.__bgImg)
        self.__imgBgHandle.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)


        self.__imgHandle = None
        self.__imgRectF = None

        self.__currentZoomFactor = 1.0

        # default properties
        self.__allowPan = True
        self.__allowZoom = True
        self.__allowMenu = True
        self.__backgroundType = None

        self.__mousePos = None


        self.__actionZoom1x1 = QAction(buildIcon("pktk:zoom_1x1"), i18n('Zoom 1:1'), self)
        self.__actionZoom1x1.triggered.connect(zoom1x1)
        self.__actionZoomToFit = QAction(buildIcon("pktk:zoom_fit"), i18n('Zoom to fit'), self)
        self.__actionZoomToFit.triggered.connect(zoomToFit)

        self.__actionBgBlack = QAction(buildIcon("pktk:color_black"), i18n('Black'), self)
        self.__actionBgBlack.triggered.connect(bgColorBlack)
        self.__actionBgBlack.setCheckable(True)
        self.__actionBgWhite = QAction(buildIcon("pktk:color_white"), i18n('White'), self)
        self.__actionBgWhite.triggered.connect(bgColorWhite)
        self.__actionBgWhite.setCheckable(True)
        self.__actionBgNGray = QAction(buildIcon("pktk:color_ngray"), i18n('Gray'), self)
        self.__actionBgNGray.triggered.connect(bgColorNGray)
        self.__actionBgNGray.setCheckable(True)
        self.__actionBgNone = QAction(buildIcon("pktk:color_none"), i18n('Default'), self)
        self.__actionBgNone.triggered.connect(bgColorNone)
        self.__actionBgNone.setCheckable(True)
        self.__actionBgCheckerBoard = QAction(buildIcon("pktk:color_checkerboard"), i18n('Checker board'), self)
        self.__actionBgCheckerBoard.triggered.connect(bgColorCheckerBoard)
        self.__actionBgCheckerBoard.setCheckable(True)



        self.__contextMenu = QMenu(i18n("Background"))
        self.__bgMenu = self.__contextMenu.addMenu(buildIcon("pktk:color"), 'Background')
        self.__contextMenu.addSeparator()
        self.__contextMenu.addAction(self.__actionZoom1x1)
        self.__contextMenu.addAction(self.__actionZoomToFit)


        self.__bgMenu.addAction(self.__actionBgCheckerBoard)
        self.__bgMenu.addSeparator()
        self.__bgMenu.addAction(self.__actionBgBlack)
        self.__bgMenu.addAction(self.__actionBgWhite)
        self.__bgMenu.addAction(self.__actionBgNGray)
        self.__bgMenu.addAction(self.__actionBgNone)



        menuGroup = QActionGroup(self)
        menuGroup.addAction(self.__actionBgCheckerBoard)
        menuGroup.addAction(self.__actionBgBlack)
        menuGroup.addAction(self.__actionBgWhite)
        menuGroup.addAction(self.__actionBgNGray)
        menuGroup.addAction(self.__actionBgNone)

        self.setContextMenuPolicy(Qt.DefaultContextMenu)


        # Set a default scrollbar configuration
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setBackgroundType(WImageView.BG_CHECKER_BOARD)



    def contextMenuEvent(self, event):
        self.__contextMenu.exec_(event.globalPos())

    @staticmethod
    def backgroundList():
        """return list of possible values"""
        return [WImageView.BG_BLACK,
                WImageView.BG_WHITE,
                WImageView.BG_NEUTRAL_GRAY,
                WImageView.BG_TRANSPARENT,
                WImageView.BG_CHECKER_BOARD]


    def allowZoom(self):
        """Return True if user is allowed to zoom with mouse"""
        return self.__allowZoom

    def setAllowZoom(self, value=True):
        """define if user is allowed to zoom with mouse"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be a <bool>")

        self.__allowZoom = value

    def allowPan(self):
        """Return True if user is allowed to pan with mouse"""
        return self.__allowPan

    def setAllowPan(self, value=True):
        """define if user is allowed to pan with mouse"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be a <bool>")

        self.__allowPan = value

    def allowMenu(self):
        """Return True if user is allowed to display default context menu"""
        return self.__allowMenu

    def setAllowMenu(self, value=True):
        """define if user is allowed to display context menu"""
        if not isinstance(value, bool):
            raise EInvalidType("Given `value` must be a <bool>")

        self.__allowMenu = value

    def backgroundType(self):
        """Return current background definition"""
        return self.__backgroundType

    def setBackgroundType(self, value):
        """Set current background definition

        Can be:
            WImageView.BG_BLACK = 0
            WImageView.BG_WHITE = 1
            WImageView.BG_NEUTRAL_GRAY = 2
            WImageView.BG_TRANSPARENT = 3
            WImageView.BG_CHECKER_BOARD = 4
        """
        if not isinstance(value, int):
            raise EInvalidType("Given `value` must be a valid <int>")

        if not value in [WImageView.BG_BLACK,
                         WImageView.BG_WHITE,
                         WImageView.BG_NEUTRAL_GRAY,
                         WImageView.BG_TRANSPARENT,
                         WImageView.BG_CHECKER_BOARD]:
            raise EInvalidValue("Given `value` is not valid")

        if self.__backgroundType != value:
            self.__backgroundType = value
            if self.__backgroundType == WImageView.BG_BLACK:
                self.__gScene.setBackgroundBrush(QBrush(Qt.black))
                self.__actionBgBlack.setChecked(True)
            elif self.__backgroundType == WImageView.BG_WHITE:
                self.__gScene.setBackgroundBrush(QBrush(Qt.white))
                self.__actionBgWhite.setChecked(True)
            elif self.__backgroundType == WImageView.BG_NEUTRAL_GRAY:
                self.__gScene.setBackgroundBrush(QBrush(QColor(128,128,128)))
                self.__actionBgNGray.setChecked(True)
            elif self.__backgroundType == WImageView.BG_TRANSPARENT:
                self.__gScene.setBackgroundBrush(QBrush(Krita.activeWindow().qwindow().palette().color(QPalette.Mid)))
                self.__actionBgNone.setChecked(True)
            elif self.__backgroundType == WImageView.BG_CHECKER_BOARD:
                self.__gScene.setBackgroundBrush(checkerBoardBrush(32))
                self.__actionBgCheckerBoard.setChecked(True)

    def zoom(self):
        """Return current zoom property

        returned value is a tuple (ratio, QRectF) or None if there's no image
        """
        return self.__currentZoomFactor

        if self.hasImage():
            if len(self.__zoomList)>0:
                rect = self.__zoomList[-1]
            else:
                rect = self.sceneRect()

            imgRect = QRectF(self.__imgHandle.pixmap().rect())
            if rect.width() > 0:
                ratio = imgRect.width() / rect.width()
            else:
                ratio = 1.0

            return (ratio, rect)
        else:
            return None

    def setZoom(self, value=0.0):
        """Set current zoom value

        If value is a QRect() or QRectF(), set zoom to given bounds
        If value is a float, bounds are calculated automatically:
            0 = fit to view
        """
        if not self.hasImage():
            return

        viewportRect = self.viewport().rect()

        if isinstance(value, QRect):
            value = QRectF(value)

        if isinstance(value, QRectF):
            sceneRect = self.transform().mapRect(value)
            self.__currentZoomFactor = min(viewportRect.width() / sceneRect.width(),
                                           viewportRect.height() / sceneRect.height())
            self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            self.centerOn(value.left() + value.width()/2, value.top() + value.height()/2,)
        elif isinstance(value, float) or isinstance(value, int):
            if value == 0:
                # fit
                self.resetTransform()
                self.setSceneRect(self.__imgRectF)

                sceneRect = self.transform().mapRect(self.__imgRectF)
                self.__currentZoomFactor = min(viewportRect.width() / sceneRect.width(),
                                               viewportRect.height() / sceneRect.height())
                self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            elif value > 0:
                self.__currentZoomFactor = value
                self.resetTransform()
                self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            else:
                # ignore invalid given zoom
                return
        else:
            raise EInvalidType("Given `value` must be a <float> or <QRectF>")
        self.zoomChanged.emit(round(self.__currentZoomFactor * 100,2))



    def hasImage(self):
        """Return if an image is set or not"""
        if self.__imgHandle is None:
            return False
        return True

    def clearImage(self):
        """Clear current image"""
        if self.hasImage():
            self.__gScene.removeItem(self.__imgHandle)
            self.__imgHandle = None
            self.__imgRectF = None
            self.__currentZoomFactor = 1.0

    def image(self, asPixmap=False):
        """Return current image as QImage or None if not image is defined
        """
        if self.hasImage():
            if asPixmap:
                return self.__imgHandle.pixmap()
            else:
                return self.__imgHandle.pixmap().toImage()
        return None

    def setImage(self, image, resetZoom=True):
        """Set current image

        Given image is a QImage or a QPixmap
        """
        if image is None:
            self.clearImage()
            return

        if not (isinstance(image, QImage) or isinstance(image, QPixmap)):
            raise EInvalidType("Given `image` must be a <QImage> or a <QPixmap>")

        if isinstance(image, QImage):
            img = QPixmap.fromImage(image)
        else:
            img = image

        if self.hasImage():
            self.__imgHandle.setPixmap(img)
        else:
            self.__imgHandle = self.__gScene.addPixmap(img)

        self.__imgRectF = QRectF(img.rect())

        if self.__imgRectF.isNull():
            self.clearImage()
        elif resetZoom:
            # view image to fit
            self.setZoom(0.0)

    def resizeEvent(self, event):
        """When viewer is resized, keep current view rect"""
        self.resetTransform()
        self.scale(self.__currentZoomFactor, self.__currentZoomFactor)

    def mousePressEvent(self, event):
        """Start Pan or Zoom"""
        # memorize current mouse position on image
        self.__mousePos = self.mapToScene(event.pos())

        if self.hasImage():
            if event.button() == Qt.LeftButton:
                if self.__allowZoom and event.modifiers() == Qt.ControlModifier:
                    self.setDragMode(QGraphicsView.RubberBandDrag)
                elif self.__allowPan:
                    self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.leftButtonPressed.emit(self.__mousePos.x(), self.__mousePos.y())

        QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Stop Pan or Zoom"""
        QGraphicsView.mouseReleaseEvent(self, event)

        # memorize current mouse position on image
        self.__mousePos = self.mapToScene(event.pos())

        if self.hasImage():
            if event.button() == Qt.LeftButton:
                if self.__allowZoom and event.modifiers() == Qt.ControlModifier:
                    if self.__gScene.selectionArea().boundingRect().width() > 0.0:
                        selectionRect = self.__gScene.selectionArea().boundingRect().intersected(self.__imgRectF)

                        self.__gScene.setSelectionArea(QPainterPath())  # Clear current selection area.
                        if selectionRect.isValid() and (selectionRect != self.viewport().rect()):
                            self.setZoom(selectionRect)

                    self.setDragMode(QGraphicsView.NoDrag)
                elif self.__allowPan:
                    self.setDragMode(QGraphicsView.NoDrag)
                self.leftButtonReleased.emit(self.__mousePos.x(), self.__mousePos.y())

    def mouseDoubleClickEvent(self, event):
        """Reset zoom

        - left: default image size
        - right: fit image
        """
        # memorize current mouse position on image
        self.__mousePos = self.mapToScene(event.pos())

        if event.button() == Qt.LeftButton:
            if self.zoom() == 1:
                # scale 1:1 => zoom to fit
                self.setZoom(0.0)
            else:
                # scale is not 1:1 => scale to 1
                self.setZoom(1.0)
            self.leftButtonDoubleClicked.emit(self.__mousePos.x(), self.__mousePos.y())
        QGraphicsView.mouseDoubleClickEvent(self, event)

    def wheelEvent(self, event):
        """Zoom in/out"""
        # memorize current mouse position on image
        self.__mousePos = self.mapToScene(event.pos())

        if self.hasImage():
            if event.angleDelta().y() > 0:
                self.setZoom(self.__currentZoomFactor * 1.25)
            else:
                self.setZoom(self.__currentZoomFactor * 0.8)
