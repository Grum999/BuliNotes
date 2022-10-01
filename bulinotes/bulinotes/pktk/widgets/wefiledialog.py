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
# The wefiledialog module provides an extended file dialog with image preview
#
# Main class from this module
#
# - WEFileDialog:
#       The main file dialog
#
# -----------------------------------------------------------------------------
from PyQt5.Qt import *
from PyQt5.QtWidgets import QFileDialog

import os.path


class WEFileDialog(QFileDialog):
    """A file dialog with image preview"""

    PREVIEW_WIDTH = 250

    def __init__(self, caption=None, directory=None, filter=None, message=None, withImagePreview=True):
        QFileDialog.__init__(self, None, caption, directory, filter)

        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setMaximumSize(0xffffff, 0xffffff)

        self.__box = QVBoxLayout()

        self.__withImagePreview = withImagePreview

        if self.__withImagePreview:
            self.__lblSize = QLabel(self)
            font = self.__lblSize.font()
            font.setPointSize(8)
            self.__lblSize.setFont(font)
            self.__lblSize.setAlignment(Qt.AlignCenter)
            self.__lblSize.setStyleSheet('font-style: italic')

            self.__lblPreview = QLabel(i18n("Preview"), self)
            self.__lblPreview.setAlignment(Qt.AlignCenter)
            self.__lblPreview.setMinimumSize(WEFileDialog.PREVIEW_WIDTH, 0)

            self.__box.addWidget(self.__lblPreview)

        offsetRow = 0
        self.__teMessage = None
        self.__message = None
        if not(message is None or message == ''):
            offsetRow = 1
            self.__message = message

            self.__teMessage = QTextEdit(self)
            self.__teMessage.setReadOnly(True)
            self.__teMessage.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding))
            self.__teMessage.setHtml(message)

            self.__msgBox = QVBoxLayout(self)
            self.__msgBox.addWidget(self.__teMessage)

            # the dirty way to reorganize layout...
            # in synthesis: QGridLayout doesn't allows to INSERT rows
            # solution: 1) take all items from layout (until there's no item in layout)
            #           2) append message
            #           3) append taken item in initial order, with row offset + 1
            rows = {}
            itemIndex = 0
            while self.layout().count():
                # take all items
                position = self.layout().getItemPosition(itemIndex)
                if not position[0] in rows:
                    rows[position[0]] = []
                rows[position[0]].append((itemIndex, position, self.layout().takeAt(itemIndex)))

            # append message
            self.layout().addLayout(self.__msgBox, 0, 0, 1, -1)

            # appends taken items
            for row in list(rows.keys()):
                for itemNfo in rows[row]:
                    self.layout().addItem(itemNfo[2], itemNfo[1][0]+1, itemNfo[1][1], itemNfo[1][2], itemNfo[1][3])

        if self.__withImagePreview:
            self.layout().addWidget(self.__lblPreview, 1+offsetRow, 3, Qt.AlignLeft)
            self.layout().addWidget(self.__lblSize, 2+offsetRow, 3, Qt.AlignCenter)

            self.currentChanged.connect(self.__changed)
            self.fileSelected.connect(self.__fileSelected)
            self.filesSelected.connect(self.__filesSelected)

        self.__fileSelected = ''
        self.__filesSelected = []

    def showEvent(self, event):
        if self.__teMessage is not None:
            # Ideal size can't be applied until widgets are shown because document
            # size (especially height) can't be known unless QTextEdit widget is visible
            self.__applyMessageIdealSize(self.__message)
            # calculate QDialog size according to content
            self.adjustSize()
            # and finally, remove constraint for QTextEdit size (let user resize dialog box if needed)
            self.__teMessage.setMinimumSize(0, 0)

        self.resize(self.width() + round(1.5*WEFileDialog.PREVIEW_WIDTH), self.height())

    def __applyMessageIdealSize(self, message):
        """Try to calculate and apply ideal size for dialog box"""
        # get primary screen (screen on which dialog is displayed) size
        rect = QGuiApplication.primaryScreen().size()
        # and determinate maximum size to apply to dialog box when displayed
        # => note, it's not the maximum window size (user can increase size with grip),
        #    but the maximum we allow to use to determinate window size at display
        # => factor are arbitrary :)
        maxW = rect.width() * 0.5 if rect.width() > 1920 else rect.width() * 0.7 if rect.width() > 1024 else rect.width() * 0.9
        maxH = rect.height() * 0.5 if rect.height() > 1080 else rect.height() * 0.7 if rect.height() > 1024 else rect.height() * 0.9
        # let's define some minimal dimension for dialog box...
        minW = 320
        minH = 200

        # an internal document used to calculate ideal width
        # (ie: using no-wrap for space allows to have an idea of maximum text width)
        document = QTextDocument()
        document.setDefaultStyleSheet("p { white-space: nowrap; }")
        document.setHtml(message)

        # then define our QTextEdit width taking in account ideal size, maximum and minimum allowed width on screen
        self.__teMessage.setMinimumWidth(max(minW, min(maxW, document.idealWidth())))

        # now QTextEdit widget has a width defined, we can retrieve height of document
        # (ie: document's height = as if we don't have scrollbars)
        # add a security margin of +25 pixels
        height = max(minH, min(maxH, self.__teMessage.document().size().height()+25))

        self.__teMessage.setMinimumHeight(height)

    def __changed(self, path):
        """File has been changed"""

        if not os.path.isdir(path):
            pixmap = QPixmap(path)

            if pixmap.isNull():
                self.__lblPreview.setText("Can't read file")
                self.__lblSize.setText('')
            else:
                self.__lblPreview.setPixmap(pixmap.scaled(self.__lblPreview.width(), self.__lblPreview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.__lblSize.setText(f'{pixmap.width()}x{pixmap.height()}')
        else:
            self.__lblPreview.setText("No preview")
            self.__lblSize.setText('')

    def __fileSelected(self, file):
        self.__fileSelected = file

    def __filesSelected(self, files):
        self.__filesSelected = files

    def file(self):
        """return selected file name"""
        return self.__fileSelected

    def files(self):
        """return list of selected files"""
        return self.__filesSelected
