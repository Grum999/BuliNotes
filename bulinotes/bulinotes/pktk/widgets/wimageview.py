# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# Based from C++ Qt example:
#   https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/layouts/flowlayout/flowlayout.cpp?h=5.15
#
#   Original example source code published under BSD License Usage
#       Copyright (C) 2016 The Qt Company Ltd.
#       Contact: https://www.qt.io/licensing/
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The wimagepreview module provides widget used to render an image preview
#
# Main class from this module
#
# - WImageView:
#       Widget to display image with functions like zoom in/out
#
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

class WImageGView(QGraphicsView):
    """Display image with pan/zoom hability"""
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
        super(WImageGView, self).__init__(parent)

        # Image is a QPixmap in a QGraphicsScene
        self.__gScene = QGraphicsScene()
        self.__gScene.setBackgroundBrush(QBrush(Qt.NoBrush))
        self.setScene(self.__gScene)

        # Handle for current image
        self.__bgImg = QPixmap()
        self.__imgBgHandle = self.__imgHandle = self.__gScene.addPixmap(self.__bgImg)
        self.__imgBgHandle.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)

        self.__imgHandle = None
        self.__imgRectF = None

        self.__minimumZoomFactor = 0.01
        self.__maximumZoomFactor = 16.0
        self.__currentZoomFactor = 1.0
        self.__zoomStep = 0.25

        # default properties
        self.__allowPan = True
        self.__allowZoom = True

        self.__mousePos = None

        # Set a default scrollbar configuration
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.viewport().setStyleSheet("background: transparent")

    def __setZoomFactor(self, value):
        """Set current zoom factor, applying defined min/max allowed values"""
        if value > self.__maximumZoomFactor:
            self.__currentZoomFactor = round(self.__maximumZoomFactor, 2)
        elif value < self.__minimumZoomFactor:
            self.__currentZoomFactor = round(self.__minimumZoomFactor, 2)
        else:
            self.__currentZoomFactor = round(value, 2)

    def __calculateZoomStep(self, increasing):
        """Calculate zoom step value"""
        if increasing:
            if self.__currentZoomFactor < 0.1:
                self.__zoomStep = 0.01
            elif self.__currentZoomFactor < 0.25:
                self.__zoomStep = 0.05
            elif self.__currentZoomFactor < 5:
                self.__zoomStep = 0.25
            else:
                self.__zoomStep = 0.5
        else:
            if self.__currentZoomFactor <= 0.1:
                self.__zoomStep = 0.01
            elif self.__currentZoomFactor <= 0.25:
                self.__zoomStep = 0.05
            elif self.__currentZoomFactor <= 5:
                self.__zoomStep = 0.25
            else:
                self.__zoomStep = 0.5

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

    def zoom(self):
        """Return current zoom property

        returned value is a tuple (ratio, QRectF) or None if there's no image
        """
        return self.__currentZoomFactor

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

        oldZoomFactor = self.__currentZoomFactor

        if isinstance(value, QRectF):
            # QRectF given, zoom to this rect (scene coordinates)
            sceneRect = self.mapFromScene(value).boundingRect()

            self.fitInView(value, Qt.KeepAspectRatio)

            self.__currentZoomFactor = self.transform().m11()
            self.resetTransform()
            self.__setZoomFactor(self.__currentZoomFactor)
            self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            self.centerOn(value.center())
        elif isinstance(value, float) or isinstance(value, int):
            if value == 0:
                # zoom to fit
                self.resetTransform()
                self.setSceneRect(self.__imgRectF)

                sceneRect = self.transform().mapRect(self.__imgRectF)
                self.__setZoomFactor(min(viewportRect.width() / sceneRect.width(),
                                         viewportRect.height() / sceneRect.height()))
                self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            elif value > 0:
                self.__setZoomFactor(value)
                self.resetTransform()
                self.scale(self.__currentZoomFactor, self.__currentZoomFactor)
            else:
                # ignore invalid given zoom
                return
        else:
            raise EInvalidType("Given `value` must be a <float> or <QRectF>")

        self.__calculateZoomStep(oldZoomFactor > self.__currentZoomFactor)

        self.zoomChanged.emit(round(self.__currentZoomFactor * 100, 2))

    def minimumZoom(self):
        """Return Minimum zoom that can be applied"""
        return self.__minimumZoomFactor

    def setMinimumZoom(self, value):
        """Minimum zoom that can be applied

        1.00 = 100%
        """
        if value > 0 and value <= 1.00:
            self.__minimumZoomFactor = value
            if self.__currentZoomFactor < self.__minimumZoomFactor:
                self.setZoom(self.__minimumZoomFactor)

    def maximumZoom(self):
        """Return Maximum zoom that can be applied"""
        return self.__maximumZoomFactor

    def setMaximumZoom(self, value):
        """Maximum zoom that can be applied

        1.00 = 100%
        """
        if value >= 1.00:
            self.__maximumZoomFactor = value
            if self.__currentZoomFactor > self.__maximumZoomFactor:
                self.setZoom(self.__maximumZoomFactor)

    def zoomToFit(self):
        """Zoom to fit scene content"""
        self.setZoom(0.0)

    def centerToContent(self, content=None):
        """Center view to `content`

        If None, get nodes bounding rect
        Otherwise use given content (QRect/QRectF)
        """
        if isinstance(content, QRectF):
            boundingRect = content
        elif isinstance(content, QRect):
            boundingRect = QRectF(content)
        else:
            boundingRect = self.sceneRect()
        self.centerOn(boundingRect.center())

    def resetZoom(self):
        """reset zoom to 1:1 + center to content"""
        self.setZoom(1.0)
        self.centerToContent()

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
            elif event.button() == Qt.MidButton and self.__allowPan:
                self.setDragMode(QGraphicsView.ScrollHandDrag)

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
                self.__calculateZoomStep(True)
                self.setZoom(self.__currentZoomFactor + self.__zoomStep)
            else:
                self.__calculateZoomStep(False)
                if (self.__currentZoomFactor - self.__zoomStep) > 0:
                    self.setZoom(self.__currentZoomFactor - self.__zoomStep)

            newPos = event.pos() - self.mapFromScene(self.__mousePos)
            self.translate(newPos.x(), newPos.y())


class WImageView(QWidget):
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

    @staticmethod
    def backgroundList():
        """return list of possible values"""
        return [WImageView.BG_BLACK,
                WImageView.BG_WHITE,
                WImageView.BG_NEUTRAL_GRAY,
                WImageView.BG_TRANSPARENT,
                WImageView.BG_CHECKER_BOARD]

    def __init__(self, parent=None):
        """Initialise viewer"""
        super(WImageView, self).__init__(parent)

        self.__wImgView = WImageGView(self)
        self.__wImgView.setCacheMode(QGraphicsView.CacheBackground)
        self.__wImgView.leftButtonPressed.connect(lambda x, y: self.leftButtonPressed.emit(x, y))
        self.__wImgView.rightButtonPressed.connect(lambda x, y: self.rightButtonPressed.emit(x, y))
        self.__wImgView.leftButtonReleased.connect(lambda x, y: self.leftButtonReleased.emit(x, y))
        self.__wImgView.rightButtonReleased.connect(lambda x, y: self.rightButtonReleased.emit(x, y))
        self.__wImgView.leftButtonDoubleClicked.connect(lambda x, y: self.leftButtonDoubleClicked.emit(x, y))
        self.__wImgView.rightButtonDoubleClicked.connect(lambda x, y: self.rightButtonDoubleClicked.emit(x, y))
        self.__wImgView.zoomChanged.connect(lambda z: self.zoomChanged.emit(z))

        self.__layout = QVBoxLayout()
        self.__layout.addWidget(self.__wImgView)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)

        # default properties
        self.__allowMenu = True
        self.__backgroundType = None

        self.__bgBrush = checkerBoardBrush(32)

        self.__actionZoom1x1 = QAction(buildIcon("pktk:zoom_1x1"), i18n('Zoom 1:1'), self)
        self.__actionZoom1x1.triggered.connect(lambda: self.__wImgView.resetZoom())
        self.__actionZoomToFit = QAction(buildIcon("pktk:zoom_fit"), i18n('Zoom to fit'), self)
        self.__actionZoomToFit.triggered.connect(lambda: self.__wImgView.zoomToFit())

        self.__actionBgBlack = QAction(buildIcon("pktk:color_black"), i18n('Black'), self)
        self.__actionBgBlack.triggered.connect(lambda: self.setBackgroundType(WImageView.BG_BLACK))
        self.__actionBgBlack.setCheckable(True)
        self.__actionBgWhite = QAction(buildIcon("pktk:color_white"), i18n('White'), self)
        self.__actionBgWhite.triggered.connect(lambda: self.setBackgroundType(WImageView.BG_WHITE))
        self.__actionBgWhite.setCheckable(True)
        self.__actionBgNGray = QAction(buildIcon("pktk:color_ngray"), i18n('Gray'), self)
        self.__actionBgNGray.triggered.connect(lambda: self.setBackgroundType(WImageView.BG_NEUTRAL_GRAY))
        self.__actionBgNGray.setCheckable(True)
        self.__actionBgNone = QAction(buildIcon("pktk:color_none"), i18n('Default'), self)
        self.__actionBgNone.triggered.connect(lambda: self.setBackgroundType(WImageView.BG_TRANSPARENT))
        self.__actionBgNone.setCheckable(True)
        self.__actionBgCheckerBoard = QAction(buildIcon("pktk:color_checkerboard"), i18n('Checker board'), self)
        self.__actionBgCheckerBoard.triggered.connect(lambda: self.setBackgroundType(WImageView.BG_CHECKER_BOARD))
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

        self.setBackgroundType(WImageView.BG_CHECKER_BOARD)

    def contextMenuEvent(self, event):
        self.__contextMenu.exec_(event.globalPos())

    def paintEvent(self, event):
        """paint background"""
        super(WImageView, self).paintEvent(event)

        painter = QPainter(self)
        painter.fillRect(event.rect(), self.__bgBrush)

    def allowZoom(self):
        """Return True if user is allowed to zoom with mouse"""
        return self.__wImgView.allowZoom()

    def setAllowZoom(self, value=True):
        """define if user is allowed to zoom with mouse"""
        self.__wImgView.setAllowZoom(value)

    def allowPan(self):
        """Return True if user is allowed to pan with mouse"""
        return self.__wImgView.allowPan()

    def setAllowPan(self, value=True):
        """define if user is allowed to pan with mouse"""
        self.__wImgView.setAllowPan(value)

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

        if value not in [WImageView.BG_BLACK,
                         WImageView.BG_WHITE,
                         WImageView.BG_NEUTRAL_GRAY,
                         WImageView.BG_TRANSPARENT,
                         WImageView.BG_CHECKER_BOARD]:
            raise EInvalidValue("Given `value` is not valid")

        if self.__backgroundType != value:
            self.__backgroundType = value
            if self.__backgroundType == WImageView.BG_BLACK:
                self.__bgBrush = QBrush(Qt.black)
                self.__actionBgBlack.setChecked(True)
            elif self.__backgroundType == WImageView.BG_WHITE:
                self.__bgBrush = QBrush(Qt.white)
                self.__actionBgWhite.setChecked(True)
            elif self.__backgroundType == WImageView.BG_NEUTRAL_GRAY:
                self.__bgBrush = QBrush(QColor(128, 128, 128))
                self.__actionBgNGray.setChecked(True)
            elif self.__backgroundType == WImageView.BG_TRANSPARENT:
                self.__bgBrush = QBrush(Krita.activeWindow().qwindow().palette().color(QPalette.Mid))
                self.__actionBgNone.setChecked(True)
            elif self.__backgroundType == WImageView.BG_CHECKER_BOARD:
                self.__bgBrush = checkerBoardBrush(32)
                self.__actionBgCheckerBoard.setChecked(True)
            self.update()

    def zoom(self):
        """Return current zoom property

        returned value is a tuple (ratio, QRectF) or None if there's no image
        """
        return self.__wImgView.zoom()

    def setZoom(self, value=0.0):
        """Set current zoom value

        If value is a QRect() or QRectF(), set zoom to given bounds
        If value is a float, bounds are calculated automatically:
            0 = fit to view
        """
        self.__wImgView.setZoom(value)

    def hasImage(self):
        """Return if an image is set or not"""
        return self.__wImgView.hasImage()

    def clearImage(self):
        """Clear current image"""
        self.__wImgView.clearImage()

    def image(self, asPixmap=False):
        """Return current image as QImage or None if not image is defined
        """
        return self.__wImgView.image(asPixmap)

    def setImage(self, image, resetZoom=True):
        """Set current image

        Given image is a QImage or a QPixmap
        """
        return self.__wImgView.setImage(image, resetZoom)

    def minimumZoom(self):
        """Return Minimum zoom that can be applied"""
        return self.__wImgView.minimumZoom()

    def setMinimumZoom(self, value):
        """Minimum zoom that can be applied

        1.00 = 100%
        """
        self.__wImgView.setMinimumZoom(value)

    def maximumZoom(self):
        """Return Maximum zoom that can be applied"""
        return self.__wImgView.maximumZoom()

    def setMaximumZoom(self, value):
        """Maximum zoom that can be applied

        1.00 = 100%
        """
        self.__wImgView.setMaximumZoom(value)

    def zoomToFit(self):
        """Zoom to fit scene content"""
        self.__wImgView.zoomToFit()

    def centerToContent(self, content=None):
        """Center view to `content`

        If None, get nodes bounding rect
        Otherwise use given content (QRect/QRectF)
        """
        self.__wImgView.centerToContent(content)

    def resetZoom(self):
        """reset zoom to 1:1 + center to content"""
        self.__wImgView.resetZoom()
