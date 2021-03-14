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

import time
import struct
import re

import krita
from krita import (
                View,
                ManagedColor,
                Resource
            )

from pktk import *

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from .bnwbrushes import (
                    BNBrushesModel,
                    BNWBrushes
                )
from pktk.widgets.wtoolbox import WToolBox




class BNNotePostIt(WToolBox):

    VSCROLLBAR_COMPACT_CSS="""
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
    HSCROLLBAR_COMPACT_CSS="""
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
    VSCROLLBAR_NORMAL_CSS="""
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
    HSCROLLBAR_NORMAL_CSS="""
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



    def __init__(self, note):
        super(BNNotePostIt, self).__init__(Krita.instance().activeWindow().qwindow())

        self.__note=note

        self.__note.updated.connect(self.__updatedNote)

        self.compactModeUpdated.connect(self.__setCompact)
        self.geometryUpdated.connect(self.__updateNoteGeometry)

        self.__initUi()

        self.show()

    def __initUi(self):
        """Build window interface"""
        if self.__note.windowPostItGeometry():
            self.setGeometry(self.__note.windowPostItGeometry())
        else:
            self.setCenteredPosition()

        self.__stackedWidgets=QStackedWidget(self)

        self.__textEdit=BNNotePostItText(self)
        self.__scratchpadImg=BNWLabelScratch("scratchpad")
        self.__brushesList=BNWBrushes(self)
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


        self.__stackedWidgets.addWidget(self.__textEdit)
        self.__stackedWidgets.addWidget(self.__scratchpadImg)
        self.__stackedWidgets.addWidget(self.__brushesList)
        self.__stackedWidgets.setCurrentIndex(0)

        self.setCentralWidget(self.__stackedWidgets)

        self.__btShowText=QToolButton(self)
        self.__btShowText.clicked.connect(self.__showNotePage)
        self.__btShowText.setToolTip(i18n('Text note'))
        self.__btShowText.setIcon(QIcon(':/images/btText'))
        self.__btShowText.setFocusPolicy(Qt.NoFocus)
        self.__btShowText.setAutoRaise(True)
        self.__btShowText.setCheckable(True)

        self.__btShowScratchpad=QToolButton(self)
        self.__btShowScratchpad.clicked.connect(self.__showNotePage)
        self.__btShowScratchpad.setToolTip(i18n('Handwritten note'))
        self.__btShowScratchpad.setIcon(QIcon(':/images/btDraw'))
        self.__btShowScratchpad.setFocusPolicy(Qt.NoFocus)
        self.__btShowScratchpad.setAutoRaise(True)
        self.__btShowScratchpad.setCheckable(True)

        self.__btShowBrushes=QToolButton(self)
        self.__btShowBrushes.clicked.connect(self.__showNotePage)
        self.__btShowBrushes.setToolTip(i18n('Brushes note'))
        self.__btShowBrushes.setIcon(QIcon(':/images/btBrushes'))
        self.__btShowBrushes.setFocusPolicy(Qt.NoFocus)
        self.__btShowBrushes.setAutoRaise(True)
        self.__btShowBrushes.setCheckable(True)

        self.__buttonGroup=QButtonGroup()
        self.__buttonGroup.addButton(self.__btShowText)
        self.__buttonGroup.addButton(self.__btShowScratchpad)
        self.__buttonGroup.addButton(self.__btShowBrushes)

        self.bottomBarAddWidget(self.__btShowText)
        self.bottomBarAddWidget(self.__btShowScratchpad)
        self.bottomBarAddWidget(self.__btShowBrushes)

        # -1 because note type start from 1 and page from 0
        self.__showNotePage(self.__note.selectedType()-1)

        self.__setCompact(self.__note.windowPostItCompact())
        self.__updateUi()

    def __applyCompactFactor(self, subResult):
        return f'font-size: {round(0.8*int(subResult.group(1)))}pt;'

    def __updatedNote(self, note, property):
        self.__updateUi()

    def changeEvent(self, event):
        """When toolbox become inactive deselect brush"""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.__brushesList.selectionModel().clearSelection()

    def showEvent(self, event):
        """Need to update treeview columns size..."""
        self.__brushesList.resizeColumns()

    def __setCompact(self, value):
        """Set post-it as compact"""
        self.__note.setWindowPostItCompact(value)

        if value:
            self.__textEdit.setHtml(re.sub(r"font-size\s*:\s*(\d+)pt;", self.__applyCompactFactor, self.__note.text()))
        else:
            self.__textEdit.setHtml(self.__note.text())
        self.__textEdit.setCompact(value)
        self.__brushesList.setCompact(value)

        if value:
            self.__brushesList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_COMPACT_CSS)
            self.__brushesList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_COMPACT_CSS)
        else:
            self.__brushesList.verticalScrollBar().setStyleSheet(BNNotePostIt.VSCROLLBAR_NORMAL_CSS)
            self.__brushesList.horizontalScrollBar().setStyleSheet(BNNotePostIt.HSCROLLBAR_NORMAL_CSS)

    def __updateUi(self):
        """Update UI content according to note content"""
        self.setTitle(self.__note.title())

        text=self.__note.text()
        if self.__note.windowPostItCompact():
            text=re.sub(r"font-size:\s*(\d+)pt;", self.__applyCompactFactor, text)

        # display buttons only if more than one button to display, otherwise all are hidden
        nb=0
        if self.__note.hasText():
            self.__textEdit.setHtml(text)
            nb+=1
        else:
            self.__textEdit.setHtml('')
        if self.__note.hasScratchpad():
            self.__scratchpadImg.setPixmap(QPixmap.fromImage(self.__note.scratchpadImage()))
            nb+=1
        else:
            self.__scratchpadImg.setPixmap(None)
        if self.__note.hasBrushes():
            nb+=1

        self.__btShowText.setVisible(self.__note.hasText() and nb>1)
        self.__btShowScratchpad.setVisible(self.__note.hasScratchpad() and nb>1)
        self.__btShowBrushes.setVisible(self.__note.hasBrushes() and nb>1)

        self.setColorIndex(self.__note.colorIndex())

    def __showNotePage(self, pageNumber=None):
        if isinstance(pageNumber, bool):
            # button clicked
            if self.__btShowText.isChecked():
                pageNumber=0
            elif self.__btShowScratchpad.isChecked():
                pageNumber=1
            if self.__btShowBrushes.isChecked():
                pageNumber=2

            # +1 because types start from 1 and pages from 0
            self.__note.setSelectedType(pageNumber+1)
        else:
            if pageNumber==0:
                self.__btShowText.setChecked(True)
            elif pageNumber==1:
                self.__btShowScratchpad.setChecked(True)
            elif pageNumber==2:
                self.__btShowBrushes.setChecked(True)

        self.__stackedWidgets.setCurrentIndex(pageNumber)

    def __updateNoteGeometry(self, value):
        """Update note geometry"""
        self.__note.setWindowPostItGeometry(value)

    def __brushesListIconSizeIndexChanged(self, index, size):
        """Icon size index has been changed"""
        self.__note.setWindowPostItBrushIconSizeIndex(index)

    def __brushesListSelectionChanged(self, selected, deselected):
        """Selection in brush list has changed"""
        selectedBrushes=self.__brushesList.selectedItems()
        if len(selectedBrushes)==1:
            selectedBrushes[0].toBrush()

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
        self.__parent=parent
        self.__moving=False
        self.__globalPos=None
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
            self.__globalPos=event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super(BNNotePostItText, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """If in drag mode, move current note window"""
        if self.__globalPos:
            if not self.__moving:
                self.__moving=True
                delta = QPoint(event.globalPos() - self.__globalPos)

                # -- the really dirty trick...
                # Don't really know why but without it, when moving window on my
                # secondary screen there's a really weird "shake" effect and
                # defined position sometime gets out of hand...
                #
                # having a 1ms timer is enough to fix the problem
                # suspecting something with too much event or something like that...
                BCTimer.sleep(1)
                # --

                self.__parent.move(self.__parent.x() + delta.x(), self.__parent.y() + delta.y())
                self.__globalPos = event.globalPos()
                self.__moving=False
        else:
            super(BNNotePostItText, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Exit drag mode"""
        if self.__globalPos:
            self.__globalPos=None
            self.setCursor(Qt.ArrowCursor)
        else:
            super(BNNotePostItText, self).mouseReleaseEvent(event)


class BNWLabelScratch(QLabel):
    """A label to display a streched pixmap that keep pixmap ratio"""
    def __init__(self, parent=None):
        super(BNWLabelScratch, self).__init__(parent)
        self.__pixmap=None
        self.__ratio=1
        self.setMinimumSize(1,1)
        self.setScaledContents(False)
        self.setStyleSheet("background-color: #ffffff;")

    def setPixmap(self, pixmap):
        """Set label pixmap"""
        self.__pixmap=pixmap
        if self.__pixmap:
            self.__ratio=self.__pixmap.width()/self.__pixmap.height()
            super(BNWLabelScratch, self).setPixmap(self.__scaledPixmap())
        else:
            super(BNWLabelScratch, self).setPixmap(None)

    def __height(self, width):
        """Calculate height according to width"""
        if self.__pixmap is None or self.__pixmap.width()==0:
            self.__nWidth=this.height()*self.__ratio
            return this.height()
        else:
            return self.__pixmap.height()*width/self.__pixmap.width()

    def __scaledPixmap(self):
        """Scale pixmap to current size"""
        return self.__pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def sizeHint(self):
        width = self.width()
        return QSize(width, self.__height(width))

    def resizeEvent(self, event):
        if not self.__pixmap is None:
            QLabel.setPixmap(self, self.__scaledPixmap())
            self.setContentsMargins(max(0, int((self.width()-self.height()*self.__ratio)/2)),0,0,0)

    def mousePressEvent(self, event):
        """Pick color on click"""
        if event.modifiers() & Qt.ControlModifier or event.buttons() & Qt.MidButton:
            return super(BNWLabelScratch, self).mousePressEvent(event)
        else:
            view=Krita.instance().activeWindow().activeView()
            color=QApplication.primaryScreen().grabWindow(self.winId()).toImage().pixelColor(event.pos().x(), event.pos().y())
            view.setForeGroundColor(ManagedColor.fromQColor(color, view.canvas()))
