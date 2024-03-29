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
# The bnnote_postit module provides classes used to manage note rendered as
# post-it window
#
# Main classes from this module
#
# - BNNotePostIt:
#       A post-it note
#
# - BNNotePostItText:
#       Render text in post-it
#
# - BNWLabelScratch:
#       Render scratchpad content in post-it
#
# -----------------------------------------------------------------------------

import time
import struct
import re

import krita
from krita import (
                View,
                ManagedColor,
                Resource
            )

from bulinotes.pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from .bnwbrushes import (
                    BNBrushesModel,
                    BNWBrushes
                )
from .bnwlinkedlayers import (
                    BNLinkedLayersModel,
                    BNWLinkedLayers
                )
from bulinotes.pktk.modules.imgutils import buildIcon
from bulinotes.pktk.modules.timeutils import Timer
from bulinotes.pktk.modules.ekrita import EKritaDocument
from bulinotes.pktk.widgets.wtoolbox import WToolBox


class BNNotePostIt(WToolBox):

    VSCROLLBAR_COMPACT_CSS = """
QScrollBar:vertical {
background-color: palette(base);
width: 8px;
margin: 0px;
border: 1px transparent #000000;
}

QScrollBar::handle:vertical {
background-color: palette(text);
min-height: 8px;
border-radius: 4px;
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
margin: 0px 0px 0px 0px;
height: 0px;
}
"""
    HSCROLLBAR_COMPACT_CSS = """
QScrollBar:horizontal {
background-color: palette(base);
width: 8px;
margin: 0px;
border: 1px transparent #000000;
}

QScrollBar::handle:horizontal {
background-color: palette(text);
min-height: 8px;
border-radius: 4px;
}

QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
margin: 0px 0px 0px 0px;
width: 0px;
}
"""
    VSCROLLBAR_NORMAL_CSS = """
QScrollBar:vertical {
background-color: palette(base);
width: 14px;
margin: 0px;
border: 1px transparent #000000;
}

QScrollBar::handle:vertical {
background-color: palette(text);
min-height: 14px;
border-radius: 7px;
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
margin: 0px 0px 0px 0px;
height: 0px;
}
"""
    HSCROLLBAR_NORMAL_CSS = """
QScrollBar:horizontal {
background-color: palette(base);
width: 14px;
margin: 0px;
border: 1px transparent #000000;
}

QScrollBar::handle:horizontal {
background-color: palette(text);
min-height: 14px;
border-radius: 7px;
}

QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
margin: 0px 0px 0px 0px;
width: 0px;
}
"""
    HSLIDER_NORMAL_CSS = """
QSlider::groove:horizontal {
background-color: palette(base);
height: 14px;
margin: 0px;
border: 1px transparent #000000;
border-radius: 7px;
}

QSlider::handle:horizontal {
background-color: palette(text);
height: 14px;
width: 14px;
border-radius: 7px;
}
"""

    HSLIDER_COMPACT_CSS = """
QSlider::groove:horizontal {
background-color: palette(base);
height: 10px;
margin: 0px;
border: 1px transparent #000000;
border-radius: 5px;
}

QSlider::handle:horizontal {
background-color: palette(text);
height: 10px;
width: 10px;
border-radius: 5px;
}
"""

    def __init__(self, note):
        super(BNNotePostIt, self).__init__(Krita.instance().activeWindow().qwindow())

        self.__note = note
        self.__pageNumber = 0

        self.__note.updated.connect(self.__updatedNote)

        self.compactModeUpdated.connect(self.__setCompact)
        self.pinnedModeUpdated.connect(self.__setPinned)
        self.geometryUpdated.connect(self.__updateNoteGeometry)

        self.__initUi()

        self.show()

    def __initUi(self):
        """Build window interface"""
        if self.__note.windowPostItGeometry():
            self.setGeometry(self.__note.windowPostItGeometry())
        else:
            self.setCenteredPosition()

        self.__stackedWidgets = QStackedWidget(self)

        self.__textEdit = BNNotePostItText(self)
        self.__scratchpadImg = BNWLabelScratch("scratchpad")
        self.__brushesList = BNWBrushes(self)
        self.__brushesList.setBrushes(self.__note.brushes())
        self.__brushesList.setColumnHidden(BNBrushesModel.COLNUM_COMMENT, True)
        self.__brushesList.setHeaderHidden(True)
        self.__brushesList.setIndentation(0)
        self.__brushesList.setAllColumnsShowFocus(True)
        self.__brushesList.setExpandsOnDoubleClick(False)
        self.__brushesList.setRootIsDecorated(False)
        self.__brushesList.setUniformRowHeights(False)
        self.__brushesList.setIconSizeIndex(self.__note.windowPostItBrushIconSizeIndex())
        self.__brushesList.selectionModel().selectionChanged.connect(self.__brushesListSelectionChanged)
        self.__brushesList.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.__brushesList.iconSizeIndexChanged.connect(self.__brushesListIconSizeIndexChanged)
        header = self.__brushesList.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(BNBrushesModel.COLNUM_BRUSH, QHeaderView.Stretch)

        self.__linkedLayersList = BNWLinkedLayers(self)
        self.__linkedLayersList.setLinkedLayers(self.__note.linkedLayers())
        self.__linkedLayersList.setColumnHidden(BNLinkedLayersModel.COLNUM_COMMENT, True)
        self.__linkedLayersList.setHeaderHidden(True)
        self.__linkedLayersList.setIndentation(0)
        self.__linkedLayersList.setAllColumnsShowFocus(True)
        self.__linkedLayersList.setExpandsOnDoubleClick(False)
        self.__linkedLayersList.setRootIsDecorated(False)
        self.__linkedLayersList.setUniformRowHeights(False)
        self.__linkedLayersList.setIconSizeIndex(self.__note.windowPostItLinkedLayersIconSizeIndex())
        self.__linkedLayersList.selectionModel().selectionChanged.connect(self.__linkedLayersListSelectionChanged)
        self.__linkedLayersList.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.__linkedLayersList.iconSizeIndexChanged.connect(self.__linkedLayersListIconSizeIndexChanged)
        header = self.__linkedLayersList.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(BNLinkedLayersModel.COLNUM_NAME, QHeaderView.Stretch)

        self.__stackedWidgets.addWidget(self.__textEdit)
        self.__stackedWidgets.addWidget(self.__scratchpadImg)
        self.__stackedWidgets.addWidget(self.__brushesList)
        self.__stackedWidgets.addWidget(self.__linkedLayersList)
        self.__stackedWidgets.setCurrentIndex(0)

        self.setCentralWidget(self.__stackedWidgets)

        self.__btShowText = QToolButton(self)
        self.__btShowText.clicked.connect(self.__showNotePage)
        self.__btShowText.setToolTip(i18n('Text note'))
        self.__btShowText.setIcon(buildIcon('pktk:text_t'))
        self.__btShowText.setFocusPolicy(Qt.NoFocus)
        self.__btShowText.setAutoRaise(True)
        self.__btShowText.setCheckable(True)

        self.__btShowScratchpad = QToolButton(self)
        self.__btShowScratchpad.clicked.connect(self.__showNotePage)
        self.__btShowScratchpad.setToolTip(i18n('Handwritten note'))
        self.__btShowScratchpad.setIcon(buildIcon('pktk:draw'))
        self.__btShowScratchpad.setFocusPolicy(Qt.NoFocus)
        self.__btShowScratchpad.setAutoRaise(True)
        self.__btShowScratchpad.setCheckable(True)

        self.__btShowBrushes = QToolButton(self)
        self.__btShowBrushes.clicked.connect(self.__showNotePage)
        self.__btShowBrushes.setToolTip(i18n('Brushes note'))
        self.__btShowBrushes.setIcon(buildIcon('pktk:brush'))
        self.__btShowBrushes.setFocusPolicy(Qt.NoFocus)
        self.__btShowBrushes.setAutoRaise(True)
        self.__btShowBrushes.setCheckable(True)

        self.__btShowLinkedLayers = QToolButton(self)
        self.__btShowLinkedLayers.clicked.connect(self.__showNotePage)
        self.__btShowLinkedLayers.setToolTip(i18n('Linked layers'))
        self.__btShowLinkedLayers.setIcon(buildIcon('pktk:layers'))
        self.__btShowLinkedLayers.setFocusPolicy(Qt.NoFocus)
        self.__btShowLinkedLayers.setAutoRaise(True)
        self.__btShowLinkedLayers.setCheckable(True)

        self.__buttonGroup = QButtonGroup()
        self.__buttonGroup.addButton(self.__btShowText)
        self.__buttonGroup.addButton(self.__btShowScratchpad)
        self.__buttonGroup.addButton(self.__btShowBrushes)
        self.__buttonGroup.addButton(self.__btShowLinkedLayers)

        self.__hsThumbSize = QSlider(Qt.Horizontal)
        self.__hsThumbSize.setStyleSheet(BNNotePostIt.HSLIDER_NORMAL_CSS)
        self.__hsThumbSize.setMaximumWidth(100)
        self.__hsThumbSize.setPageStep(1)
        self.__hsThumbSize.valueChanged.connect(self.__hsThumbSizeChanged)

        self.bottomBarAddWidget(self.__btShowText)
        self.bottomBarAddWidget(self.__btShowScratchpad)
        self.bottomBarAddWidget(self.__btShowBrushes)
        self.bottomBarAddWidget(self.__btShowLinkedLayers)
        self.bottomBarAddStretch()
        self.bottomBarAddWidget(self.__hsThumbSize)

        # -1 because note type start from 1 and page from 0
        self.__showNotePage(self.__note.selectedType()-1)

        self.__setCompact(self.__note.windowPostItCompact())
        self.__setPinned(self.__note.pinned())
        self.__updateUi()

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __updatedNote(self, note, property):
        if property == 'pinned':
            self.__setPinned(self.__note.pinned())
        else:
            self.__updateUi()

    def changeEvent(self, event):
        """When toolbox become inactive deselect brush"""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.__brushesList.selectionModel().clearSelection()
                if not self.__note.pinned():
                    self.__note.closeWindowPostIt()

    def showEvent(self, event):
        """Need to update treeview columns size..."""
        self.__brushesList.resizeColumns()
        self.__linkedLayersList.resizeColumns()

    def __setCompact(self, value):
        """Set post-it as compact"""
        self.__note.setWindowPostItCompact(value)

        if value:
            self.__textEdit.setHtml(re.sub(r"font-size\s*:\s*(\d+)pt;", self.__applyCompactFactor, self.__note.text()))
        else:
            self.__textEdit.setHtml(self.__note.text())
        self.__textEdit.setCompact(value)
        self.__brushesList.setCompact(value)
        self.__linkedLayersList.setCompact(value)

        if value:
            self.__brushesList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_COMPACT_CSS)
            self.__brushesList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_COMPACT_CSS)
            self.__linkedLayersList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_COMPACT_CSS)
            self.__linkedLayersList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_COMPACT_CSS)
            self.__hsThumbSize.setStyleSheet(BNNotePostIt.HSLIDER_COMPACT_CSS)
        else:
            self.__brushesList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_NORMAL_CSS)
            self.__brushesList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_NORMAL_CSS)
            self.__linkedLayersList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_NORMAL_CSS)
            self.__linkedLayersList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_NORMAL_CSS)
            self.__hsThumbSize.setStyleSheet(BNNotePostIt.HSLIDER_NORMAL_CSS)

        self.setCompact(value)

    def __setPinned(self, value):
        """Set post-it as pinned"""
        self.__note.setPinned(value)
        self.setPinned(value)

    def __updateUi(self):
        """Update UI content according to note content"""
        self.setTitle(self.__note.title())

        text = self.__note.text()
        if self.__note.windowPostItCompact():
            text = re.sub(r"font-size:\s*(\d+)pt;", self.__applyCompactFactor, text)

        # display buttons only if more than one button to display, otherwise all are hidden
        nb = 0
        if self.__note.hasText():
            self.__textEdit.setHtml(text)
            nb += 1
        else:
            self.__textEdit.setHtml('')

        if self.__note.hasScratchpad():
            self.__scratchpadImg.setPixmap(QPixmap.fromImage(self.__note.scratchpadImage()))
            nb += 1
        else:
            self.__scratchpadImg.setPixmap(None)

        if self.__note.hasBrushes():
            nb += 1

        if self.__note.hasLinkedLayers():
            nb += 1

        self.__btShowText.setVisible(self.__note.hasText() and nb > 1)
        self.__btShowScratchpad.setVisible(self.__note.hasScratchpad() and nb > 1)
        self.__btShowBrushes.setVisible(self.__note.hasBrushes() and nb > 1)
        self.__btShowLinkedLayers.setVisible(self.__note.hasLinkedLayers() and nb > 1)

        if nb == 1:
            if self.__note.hasText():
                self.__showNotePage(0)
            elif self.__note.hasScratchpad():
                self.__showNotePage(1)
            elif self.__note.hasBrushes():
                self.__showNotePage(2)
            elif self.__note.hasLinkedLayers():
                self.__showNotePage(3)

        self.setColorIndex(self.__note.colorIndex())

    def __showNotePage(self, pageNumber=None):
        if isinstance(pageNumber, bool):
            # button clicked
            if self.__btShowText.isChecked():
                pageNumber = 0
            elif self.__btShowScratchpad.isChecked():
                pageNumber = 1
            elif self.__btShowBrushes.isChecked():
                pageNumber = 2
            elif self.__btShowLinkedLayers.isChecked():
                pageNumber = 3
                self.__note.linkedLayers().updateFromDocument()

            # +1 because types start from 1 and pages from 0
            self.__note.setSelectedType(pageNumber+1)
        else:
            if pageNumber == 0:
                self.__btShowText.setChecked(True)
            elif pageNumber == 1:
                self.__btShowScratchpad.setChecked(True)
            elif pageNumber == 2:
                self.__btShowBrushes.setChecked(True)
            elif pageNumber == 3:
                self.__btShowLinkedLayers.setChecked(True)

        self.__pageNumber = pageNumber
        self.__stackedWidgets.setCurrentIndex(self.__pageNumber)

        if self.__pageNumber == 2:
            # brushes
            self.__hsThumbSize.setVisible(True)
            self.__hsThumbSize.setMaximum(4)
            self.__hsThumbSize.setValue(self.__brushesList.iconSizeIndex())
        elif self.__pageNumber == 3:
            # linkedLayers
            self.__hsThumbSize.setVisible(True)
            self.__hsThumbSize.setMaximum(5)
            self.__hsThumbSize.setValue(self.__linkedLayersList.iconSizeIndex())
        else:
            self.__hsThumbSize.setVisible(False)

    def __updateNoteGeometry(self, value):
        """Update note geometry"""
        self.__note.setWindowPostItGeometry(value)

    def __brushesListIconSizeIndexChanged(self, index, size):
        """Icon size index has been changed"""
        self.__note.setWindowPostItBrushIconSizeIndex(index)
        if self.__pageNumber == 2:
            self.__hsThumbSize.setValue(index)

    def __brushesListSelectionChanged(self, selected, deselected):
        """Selection in brush list has changed"""
        selectedBrushes = self.__brushesList.selectedItems()
        if len(selectedBrushes) == 1:
            selectedBrushes[0].toBrush()

    def __linkedLayersListIconSizeIndexChanged(self, index, size):
        """Icon size index has been changed"""
        self.__note.setWindowPostItLinkedLayersIconSizeIndex(index)
        if self.__pageNumber == 3:
            self.__hsThumbSize.setValue(index)

    def __linkedLayersListSelectionChanged(self, selected, deselected):
        """Selection in linked layer list has changed"""
        selectedLayer = self.__linkedLayersList.selectedItems()
        if len(selectedLayer) == 1:
            document = Krita.instance().activeDocument()
            node = EKritaDocument.findLayerById(document, selectedLayer[0].id())
            if node and node != document.activeNode():
                document.setActiveNode(node)

    def __hsThumbSizeChanged(self, value):
        """Value for thumb size has been modified from slider"""
        if self.__pageNumber == 2:
            self.__brushesList.setIconSizeIndex(value)
        elif self.__pageNumber == 3:
            self.__linkedLayersList.setIconSizeIndex(value)

    def closeEvent(self, event):
        """About to close window"""
        self.__note.setWindowPostIt(None)
        self.__note.closeWindowPostIt()


class BNNotePostItText(QTextEdit):
    def __init__(self, parent):
        super(BNNotePostItText, self).__init__(parent)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setReadOnly(True)
        self.setWindowFlags(Qt.SubWindow)
        self.__parent = parent
        self.__moving = False
        self.__globalPos = None
        self.setCompact(False)

    def setCompact(self, value):
        if value:
            self.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_COMPACT_CSS)
            self.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_COMPACT_CSS)
        else:
            self.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_NORMAL_CSS)
            self.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_NORMAL_CSS)

    def mousePressEvent(self, event):
        """User press anywhere on note window, so enter on drag mode"""
        if event.modifiers() & Qt.ControlModifier or event.buttons() & Qt.MidButton:
            self.__globalPos = event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super(BNNotePostItText, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """If in drag mode, move current note window"""
        if self.__globalPos:
            if not self.__moving:
                self.__moving = True
                delta = QPoint(event.globalPos() - self.__globalPos)

                # -- the really dirty trick...
                # Don't really know why but without it, when moving window on my
                # secondary screen there's a really weird "shake" effect and
                # defined position sometime gets out of hand...
                #
                # having a 1ms timer is enough to fix the problem
                # suspecting something with too much event or something like that...
                Timer.sleep(1)
                # --

                self.__parent.move(self.__parent.x() + delta.x(), self.__parent.y() + delta.y())
                self.__globalPos = event.globalPos()
                self.__moving = False
        else:
            super(BNNotePostItText, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Exit drag mode"""
        if self.__globalPos:
            self.__globalPos = None
            self.setCursor(Qt.ArrowCursor)
        else:
            super(BNNotePostItText, self).mouseReleaseEvent(event)


class BNWLabelScratch(QLabel):
    """A label to display a streched pixmap that keep pixmap ratio"""
    def __init__(self, parent=None):
        super(BNWLabelScratch, self).__init__(parent)
        self.__pixmap = None
        self.__ratio = 1
        self.setMinimumSize(1, 1)
        self.setScaledContents(False)
        self.setStyleSheet("background-color: #ffffff;")

    def setPixmap(self, pixmap):
        """Set label pixmap"""
        self.__pixmap = pixmap
        if self.__pixmap:
            self.__ratio = self.__pixmap.width()/self.__pixmap.height()
            super(BNWLabelScratch, self).setPixmap(self.__scaledPixmap())
        else:
            super(BNWLabelScratch, self).clear()

    def __height(self, width):
        """Calculate height according to width"""
        if self.__pixmap is None or self.__pixmap.width() == 0:
            self.__nWidth = self.height()*self.__ratio
            return self.height()
        else:
            return round(self.__pixmap.height()*width/self.__pixmap.width())

    def __scaledPixmap(self):
        """Scale pixmap to current size"""
        return self.__pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def sizeHint(self):
        width = self.width()
        return QSize(width, self.__height(width))

    def resizeEvent(self, event):
        if self.__pixmap is not None:
            QLabel.setPixmap(self, self.__scaledPixmap())
            self.setContentsMargins(max(0, int((self.width()-self.height()*self.__ratio)/2)), 0, 0, 0)

    def mousePressEvent(self, event):
        """Pick color on click"""
        if event.modifiers() & Qt.ControlModifier or event.buttons() & Qt.MidButton:
            return super(BNWLabelScratch, self).mousePressEvent(event)
        else:
            view = Krita.instance().activeWindow().activeView()
            color = QApplication.primaryScreen().grabWindow(self.winId()).toImage().pixelColor(event.pos().x(), event.pos().y())
            view.setForeGroundColor(ManagedColor.fromQColor(color, view.canvas()))
