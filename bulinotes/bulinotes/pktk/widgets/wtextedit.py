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

import os

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QVBoxLayout,
        QWidget
    )
from .wcolorbutton import WColorButton


class WTextEditDialog(QDialog):
    """A simple dialog box to edit formatted text"""

    def __init__(self, parent):
        super(WTextEditDialog, self).__init__(parent)

        self.setSizeGripEnabled(True)
        self.setModal(True)

        self.__editor = WTextEdit(self)

        dbbxOkCancel = QDialogButtonBox(self)
        dbbxOkCancel.setOrientation(Qt.Horizontal)
        dbbxOkCancel.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dbbxOkCancel.accepted.connect(self.accept)
        dbbxOkCancel.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__editor)
        layout.addWidget(dbbxOkCancel)

    def toPlainText(self):
        """Return current text as plain text"""
        return self.__editor.toPlainText()

    def setPlainText(self, text):
        """Set current text as plain text"""
        self.__editor.setPlainText(text)

    def toHtml(self):
        """Return current text as HTML text"""
        return self.__editor.toHtml()

    def setHtml(self, text):
        """Set current text as HTML text"""
        self.__editor.setHtml(text)

    @staticmethod
    def edit(title, text, textColor=None, textBackgroundColor=None):
        """Open a dialog box to edit text"""
        dlgBox = WTextEditDialog(None)
        dlgBox.setHtml(text)
        dlgBox.setWindowTitle(title)

        if not textColor is None:
            dlgBox.__editor.setTextColor(textColor)

        if not textBackgroundColor is None:
            dlgBox.__editor.setTextBackgroundColor(textBackgroundColor)

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.toHtml()
        else:
            return None


class WTextEdit(QWidget):
    """A small text editor widget with a basic formatting toolbar"""

    def __init__(self, parent=None):
        super(WTextEdit, self).__init__(parent)

        self.__toolBarItems = {}
        self.__textEdit = QTextEdit()
        self.__toolBar = QWidget()

        self.__formattingWidgets=[]

        self.__fgColor = None
        self.__bgColor = None

        self.__initTextEdit()
        self.__initToolBar()

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(QMargins(0,0,0,0))
        layout.addWidget(self.__toolBar)
        layout.addWidget(self.__textEdit)

        self.setLayout(layout)


    def __initTextEdit(self):
        """Initialise text edit widget"""
        self.__textEdit.setAutoFormatting(QTextEdit.AutoAll)
        self.__textEdit.cursorPositionChanged.connect(self.__updateToolbar)

        font = QFont('Sans serif', 10)
        self.__textEdit.setFont(font)
        self.__textEdit.setFontPointSize(10)


    def __initToolBar(self):
        """Initialise toolbar widget

        [Copy] [Cut] [paste] | [Font name] [Font size] [Bold] [Italic] [Underline] [Color] | [Left alignment] [Center alignment] [Right alignment] [Justfied alignment]

        """
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(QMargins(0,0,0,0))

        items = [
            {'type':            'button',
             'id':              'undo',
             'tooltip':         i18n('Undo last action'),
             'icon':            QIcon.fromTheme('edit-undo'),
             'action':          self.__textEdit.undo,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'redo',
             'tooltip':         i18n('Redo last action'),
             'icon':            QIcon.fromTheme('edit-redo'),
             'action':          self.__textEdit.redo,
             'checkable':       False
            },
            {'type':            'separator'},
            {'type':            'button',
             'id':              'copy',
             'tooltip':         i18n('Copy selection to clipboard'),
             'icon':            QIcon.fromTheme('edit-copy'),
             'action':          self.__textEdit.copy,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'cut',
             'tooltip':         i18n('Cut selection to clipboard'),
             'icon':            QIcon.fromTheme('edit-cut'),
             'action':          self.__textEdit.cut,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'paste',
             'tooltip':         i18n('Paste from clipboard'),
             'icon':            QIcon.fromTheme('edit-paste'),
             'action':          self.__textEdit.paste,
             'checkable':       False
            },
            {'type':            'separator'},
            {'type':            'fontComboBox',
             'id':              'fontName',
             'tooltip':         i18n('Applied font'),
             'action':          self.__updateSelectedTextFontFamily,
             'isFormatting':    True
            },
            {'type':            'comboBox',
             'id':              'fontSize',
             'tooltip':         i18n('Applied font size'),
             'list':            [str(value) for value in [6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 28, 36, 48, 64, 72, 96, 144]],
             'validator':       QDoubleValidator(0.25, 512, 2),
             'editable':        True,
             'action':          self.__updateSelectedTextFontSize,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontBold',
             'tooltip':         i18n('Set current font style <b>Bold</b>'),
             'icon':            QIcon.fromTheme('format-text-bold'),
             'action':          (lambda value: self.__textEdit.setFontWeight(QFont.Bold if value else QFont.Normal)),
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontItalic',
             'tooltip':         i18n('Set current font style <i>Italic</i>'),
             'icon':            QIcon.fromTheme('format-text-italic'),
             'action':          self.__textEdit.setFontItalic,
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontUnderline',
             'tooltip':         i18n('Set current font style <u>Underline</u>'),
             'icon':            QIcon.fromTheme('format-text-underline'),
             'action':          self.__textEdit.setFontUnderline,
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'cbutton',
             'id':              'fontColor',
             'tooltip':         i18n('Set current font color'),
             'icon':            QIcon(':/images/format_text_color'),
             'action':          self.__updateSelectedTextFontColor,
             'checkable':       False,
             'isFormatting':    True
            },
            {'type':            'separator'},
            {'type':            'button',
             'id':              'textAlignLeft',
             'tooltip':         i18n('Set Left text alignment'),
             'icon':            QIcon.fromTheme('format-justify-left'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignLeft)),
             'group':           'text-align',
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignCenter',
             'tooltip':         i18n('Set Centered text alignment'),
             'icon':            QIcon.fromTheme('format-justify-center'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignCenter)),
             'group':           'text-align',
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignRight',
             'tooltip':         i18n('Set Right text alignment'),
             'icon':            QIcon.fromTheme('format-justify-right'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignRight)),
             'group':           'text-align',
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignJustify',
             'tooltip':         i18n('Set Justified text alignment'),
             'icon':            QIcon.fromTheme('format-justify-fill'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignJustify)),
             'group':           'text-align',
             'checkable':       True,
             'isFormatting':    True
            }
        ]

        groups = {}

        for item in items:
            if item['type'] in ('button','cbutton'):
                policy = QSizePolicy()
                policy.setHorizontalPolicy(QSizePolicy.Maximum)

                if item['type'] == 'cbutton':
                    qItem = WColorButton(self.__toolBar)

                    qItem.setIcon(item['icon'])
                    qItem.setAutoRaise(True)
                    qItem.colorChanged.connect(item['action'])
                else:
                    qItem = QToolButton(self.__toolBar)

                    qItem.setIcon(item['icon'])
                    qItem.setCheckable(item['checkable'])
                    qItem.setAutoRaise(True)
                    if item['checkable']:
                        qItem.toggled.connect(item['action'])
                    else:
                        qItem.clicked.connect(item['action'])

                qItem.setSizePolicy(policy)

                if 'group' in item:
                    if not item['group'] in groups:
                        groups[item['group']]=QButtonGroup(self)
                        groups[item['group']].setExclusive(True)
                    groups[item['group']].addButton(qItem)
            elif item['type'] == 'separator':
                qItem = QFrame(self.__toolBar)
                qItem.setFrameShape(QFrame.VLine)
                qItem.setFrameShadow(QFrame.Sunken)
                qItem.setLineWidth(1)
                qItem.setMidLineWidth(0)
            elif item['type'] == 'fontComboBox':
                sizePolicy=QSizePolicy()
                policy.setHorizontalPolicy(QSizePolicy.Preferred)
                qItem = QFontComboBox(self.__toolBar)
                qItem.currentFontChanged.connect(item['action'])
                qItem.setSizePolicy(policy)
            elif item['type'] == 'comboBox':
                sizePolicy=QSizePolicy()
                policy.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
                qItem = QComboBox(self.__toolBar)
                qItem.addItems(item['list'])
                qItem.setEditable(item['editable'])
                if 'validator' in item:
                    qItem.setValidator(item['validator'])
                qItem.currentTextChanged.connect(item['action'])
                qItem.setSizePolicy(policy)
            if 'tooltip' in item:
                qItem.setToolTip(item['tooltip'])
            if 'id' in item:
                qItem.setObjectName(item['id'])
            if 'isFormatting' in item and item['isFormatting']:
                self.__formattingWidgets.append(qItem)

            if 'id' in item:
                self.__toolBarItems[item['id']]=qItem
            layout.addWidget(qItem)

        self.__toolBar.setLayout(layout)


    def __blockSignals(self, blocked):
        """Block (True) or Unblock(False) signals for formatting widgets"""
        for widget in self.__formattingWidgets:
            widget.blockSignals(blocked)


    def __updateSelectedTextFontColor(self, color):
        """Open a color dialog-box and set color"""
        self.__textEdit.setTextColor(color)


    def __updateSelectedTextFontSize(self, value):
        """Update text size if given value is valid"""
        toFloat = QLocale().toFloat(value)
        if toFloat[1]:
            self.__textEdit.setFontPointSize(toFloat[0])


    def __updateSelectedTextFontFamily(self, font):
        """Update font familly for editor"""
        # the QFontComboBox signal 'currentFontChanged' gives a QFont
        # but we just want to change font family
        self.__textEdit.setFontFamily(font.family())


    def __updateToolbar(self):
        """update toolbar buttons according to current selected text"""
        # Disable current signals on formatting items
        self.__blockSignals(True)

        fValue = float(self.__textEdit.fontPointSize())
        if (fValue%1)==0:
            # no decimal part
            self.__toolBarItems['fontSize'].setCurrentText(str(int(fValue)))
        else:
            self.__toolBarItems['fontSize'].setCurrentText(str(round(fValue, 2)))

        self.__toolBarItems['fontName'].setCurrentFont(self.__textEdit.currentFont())

        self.__toolBarItems['fontBold'].setChecked(self.__textEdit.fontWeight() == QFont.Bold)
        self.__toolBarItems['fontItalic'].setChecked(self.__textEdit.fontItalic())
        self.__toolBarItems['fontUnderline'].setChecked(self.__textEdit.fontUnderline())

        self.__toolBarItems['fontColor'].setColor(self.__textEdit.textColor())

        self.__toolBarItems['textAlignLeft'].setChecked(self.__textEdit.alignment() == Qt.AlignLeft)
        self.__toolBarItems['textAlignCenter'].setChecked(self.__textEdit.alignment() == Qt.AlignCenter)
        self.__toolBarItems['textAlignRight'].setChecked(self.__textEdit.alignment() == Qt.AlignRight)
        self.__toolBarItems['textAlignJustify'].setChecked(self.__textEdit.alignment() == Qt.AlignJustify)

        self.__blockSignals(False)


    def __updateStyleSheet(self):
        """Update bc editstyle sheet acoording to given colors"""
        style = ''
        if not self.__fgColor is None:
            style+=f'color: {self.__fgColor.name()}; '

        if not self.__bgColor is None:
            style+=f'background-color: {self.__bgColor.name()};'
            if self.__bgColor.value() >= 128:
                self.__textEdit.setTextColor(Qt.black)
            else:
                self.__textEdit.setTextColor(Qt.white)

        self.__textEdit.setStyleSheet(style)


    def toHtml(self):
        """Return current text as html"""
        return self.__textEdit.toHtml()


    def setHtml(self, text):
        """set html text"""
        return self.__textEdit.setHtml(text)


    def plainText(self):
        """Return text as plain text"""
        return self.__textEdit.toPlainText()


    def setPlainText(self, text):
        """set plain text"""
        return self.__textEdit.setPlainText(text)


    def textColor(self):
        """Return current text color"""
        return self.__fgColor()


    def setTextColor(self, color):
        """Set current text color"""
        self.__fgColor = color
        self.__updateStyleSheet()


    def textBackgroundColor(self):
        """Return current text background color"""
        return self.__bgColor


    def setTextBackgroundColor(self, color):
        """Set current text background color"""
        self.__bgColor = color
        self.__updateStyleSheet()


class BCWSmallTextEdit(QFrame):
    """A small widget that allows to open a WTextEditDialog"""
    textChanged = Signal()

    def __init__(self, parent):
        super(BCWSmallTextEdit, self).__init__(parent)

        self.__title = ""

        palette = QApplication.palette()
        self.__paletteBase = QPalette(palette)
        self.__paletteBase.setColor(QPalette.Window, self.__paletteBase.color(QPalette.Base))

        self.__html = ""
        self.__plainText = ""

        self.__fgColor = None
        self.__bgColor = None

        self.setPalette(self.__paletteBase)
        self.setAutoFillBackground(True)
        self.setFrameShape(self.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.__document = QTextDocument(self)

        self.__lePreview = QLineEdit(self)
        self.__lePreview.setFrame(False)
        self.__lePreview.setReadOnly(True)

        self.__btnEdit = QToolButton(self)
        self.__btnEdit.setAutoRaise(True)
        self.__btnEdit.setIcon(QIcon.fromTheme('document-edit'))
        self.__btnEdit.setToolTip("Edit text")
        self.__btnEdit.clicked.connect(self.__editText)

        sp = self.__btnEdit.sizePolicy()
        sp.setVerticalPolicy(sp.Maximum)
        sp.setHorizontalPolicy(sp.Maximum)
        self.__btnEdit.setSizePolicy(sp)

        layout.addWidget(self.__lePreview)
        layout.addWidget(self.__btnEdit)

    def __editText(self):
        returned = WTextEditDialog.edit(self.__title, self.__html, self.__fgColor, self.__bgColor)
        if not returned is None:
            self.setHtml(returned)
            self.textChanged.emit()

    def __updateStyleSheet(self):
        """Update bc editstyle sheet acoording to given colors"""
        style = 'white-space: pre; padding: 4px; '
        if not self.__fgColor is None:
            style+=f'color: {self.__fgColor.name()}; '

        if not self.__bgColor is None:
            style+=f'background-color: {self.__bgColor.name()}; '

        if style != '':
            self.setStyleSheet(f"QToolTip {{ {style} }}")
        else:
            self.setStyleSheet('')

    def textColor(self):
        """Return current text color"""
        return self.__fgColor

    def setTextColor(self, color):
        """Set current text color"""
        self.__fgColor = QColor(color)
        self.__updateStyleSheet()

    def textBackgroundColor(self):
        """Return current text background color"""
        return self.__bgColor

    def setTextBackgroundColor(self, color):
        """Set current text background color"""
        self.__bgColor = QColor(color)
        self.__updateStyleSheet()

    def title(self):
        return self.__title

    def setTitle(self, title):
        self.__title = title

    def toPlainText(self):
        return self.__plainText

    def toHtml(self):
        return self.__html

    def setHtml(self, value):
        self.__document.setHtml(value)
        self.__html = value
        self.__plainText = self.__document.toPlainText()

        rows = self.__plainText.split(os.linesep, 1)
        if len(rows) > 1:
            self.__lePreview.setText(f"{rows[0]} ../..")
        else:
            self.__lePreview.setText(rows[0])
        self.setToolTip(value)
