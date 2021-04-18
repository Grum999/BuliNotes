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
import re

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal,
        pyqtSlot
    )
from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QVBoxLayout,
        QWidget
    )
from .wcolorselector import WColorPicker
from .wcolorbutton import (
                        WColorButton,
                        QEColor
                    )

from pktk.modules.imgutils import buildIcon

class WTextEditDialog(QDialog):
    """A simple dialog box to edit formatted text"""

    def __init__(self, parent):
        super(WTextEditDialog, self).__init__(parent)

        self.setSizeGripEnabled(True)
        self.setModal(True)

        self.editor = WTextEdit(self)

        dbbxOkCancel = QDialogButtonBox(self)
        dbbxOkCancel.setOrientation(Qt.Horizontal)
        dbbxOkCancel.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dbbxOkCancel.accepted.connect(self.accept)
        dbbxOkCancel.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        layout.addWidget(dbbxOkCancel)

    def toPlainText(self):
        """Return current text as plain text"""
        return self.editor.toPlainText()

    def setPlainText(self, text):
        """Set current text as plain text"""
        self.editor.setPlainText(text)

    def toHtml(self):
        """Return current text as HTML text"""
        return self.editor.toHtml()

    def setHtml(self, text):
        """Set current text as HTML text"""
        self.editor.setHtml(text)

    @staticmethod
    def edit(title, text, textColor=None, textBackgroundColor=None, toolbarBtns=None):
        """Open a dialog box to edit text"""
        dlgBox = WTextEditDialog(None)
        dlgBox.setHtml(text)
        dlgBox.setWindowTitle(title)

        if isinstance(toolbarBtns, int):
            dlgBox.editor.setToolbarButtons(toolbarBtns)

        if not textColor is None:
            dlgBox.editor.setTextColor(textColor)

        if not textBackgroundColor is None:
            dlgBox.editor.setTextBackgroundColor(textBackgroundColor)

        returned = dlgBox.exec()

        if returned == QDialog.Accepted:
            return dlgBox.toHtml()
        else:
            return None


class WTextEditBtBarOption:
    UNDOREDO =             0b0000000000000001
    COPYPASTE =            0b0000000000000010
    FONT =                 0b0000000000000100
    STYLE_BOLD =           0b0000000000001000
    STYLE_ITALIC =         0b0000000000010000
    STYLE_UNDERLINE =      0b0000000000100000
    STYLE_STRIKETHROUGH =  0b0000000001000000
    STYLE_COLOR_FG =       0b0000000010000000
    STYLE_COLOR_BG =       0b0000000100000000
    ALIGNMENT =            0b0000001000000000

    MODE_SET =             0x01
    MODE_ADD =             0x02
    MODE_REMOVE =          0x03


class WTextEdit(QWidget):
    """A small text editor widget with a basic formatting toolbar"""
    colorMenuUiChanged = Signal(list)       # layout for fg/bg color menu has been modified

    DEFAULT_TOOLBAR=(WTextEditBtBarOption.UNDOREDO|
                         WTextEditBtBarOption.COPYPASTE|
                         WTextEditBtBarOption.FONT|
                         WTextEditBtBarOption.STYLE_BOLD|
                         WTextEditBtBarOption.STYLE_ITALIC|
                         WTextEditBtBarOption.STYLE_UNDERLINE|
                         WTextEditBtBarOption.STYLE_COLOR_FG|
                         WTextEditBtBarOption.ALIGNMENT)


    def __init__(self, parent=None):
        super(WTextEdit, self).__init__(parent)


        self.__toolBarItems = {}
        self.__textEdit = QTextEdit()
        self.__toolBar = QWidget()

        # default button bar
        self.__toolbarBtn = WTextEdit.DEFAULT_TOOLBAR

        self.__formattingWidgets=[]

        self.__fgColor = None
        self.__bgColor = None

        self.__ignoreColorMenuUpdate=False

        # define toolbar items
        self.__itemsDef = [
            {'type':            'button',
             'id':              'undo',
             'tooltip':         i18n('Undo last action'),
             'icon':            buildIcon('pktk:edit_undo'),
             'action':          self.__textEdit.undo,
             'visibility':      WTextEditBtBarOption.UNDOREDO,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'redo',
             'tooltip':         i18n('Redo last action'),
             'icon':            buildIcon('pktk:edit_redo'),
             'action':          self.__textEdit.redo,
             'visibility':      WTextEditBtBarOption.UNDOREDO,
             'checkable':       False
            },
            {'type':            'separator'},
            {'type':            'button',
             'id':              'copy',
             'tooltip':         i18n('Copy selection to clipboard'),
             'icon':            buildIcon('pktk:copy'),
             'action':          self.__textEdit.copy,
             'visibility':      WTextEditBtBarOption.COPYPASTE,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'cut',
             'tooltip':         i18n('Cut selection to clipboard'),
             'icon':            buildIcon('pktk:cut'),
             'action':          self.__textEdit.cut,
             'visibility':      WTextEditBtBarOption.COPYPASTE,
             'checkable':       False
            },
            {'type':            'button',
             'id':              'paste',
             'tooltip':         i18n('Paste from clipboard'),
             'icon':            buildIcon('pktk:paste'),
             'action':          self.__textEdit.paste,
             'visibility':      WTextEditBtBarOption.COPYPASTE,
             'checkable':       False
            },
            {'type':            'separator'},
            {'type':            'fontComboBox',
             'id':              'fontName',
             'tooltip':         i18n('Applied font'),
             'action':          self.__updateSelectedTextFontFamily,
             'visibility':      WTextEditBtBarOption.FONT,
             'isFormatting':    True
            },
            {'type':            'comboBox',
             'id':              'fontSize',
             'tooltip':         i18n('Applied font size'),
             'list':            [str(value) for value in [6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 28, 36, 48, 64, 72, 96, 144]],
             'validator':       QDoubleValidator(0.25, 512, 2),
             'editable':        True,
             'action':          self.__updateSelectedTextFontSize,
             'visibility':      WTextEditBtBarOption.FONT,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontBold',
             'tooltip':         i18n('Set current font style <b>Bold</b> (CTRL+B)'),
             'icon':            buildIcon('pktk:format_text_bold'),
             'action':          (lambda value: self.__textEdit.setFontWeight(QFont.Bold if value else QFont.Normal)),
             'visibility':      WTextEditBtBarOption.STYLE_BOLD,
             'shortcut':        QKeySequence("CTRL+B"),
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontItalic',
             'tooltip':         i18n('Set current font style <i>Italic</i> (CTRL+I)'),
             'icon':            buildIcon('pktk:format_text_italic'),
             'action':          self.__textEdit.setFontItalic,
             'visibility':      WTextEditBtBarOption.STYLE_ITALIC,
             'shortcut':        QKeySequence("CTRL+I"),
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontUnderline',
             'tooltip':         i18n('Set current font style <u>Underline</u> (CTRL+U)'),
             'icon':            buildIcon('pktk:format_text_underline'),
             'action':          self.__textEdit.setFontUnderline,
             'visibility':      WTextEditBtBarOption.STYLE_UNDERLINE,
             'shortcut':        QKeySequence("CTRL+U"),
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'fontStrikethrough',
             'tooltip':         i18n('Set current font style <s>Strikethrough</s> (CTRL+T)'),
             'icon':            buildIcon('pktk:format_text_strikethrough'),
             'action':          self.__setFontStrikethrough,
             'visibility':      WTextEditBtBarOption.STYLE_STRIKETHROUGH,
             'shortcut':        QKeySequence("CTRL+T"),
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'cbutton',
             'id':              'fontColor',
             'tooltip':         i18n('Set current font color'),
             'icon':            buildIcon('pktk:format_text_fgcolor'),
             'action':          self.__updateSelectedTextFontColor,
             'visibility':      WTextEditBtBarOption.STYLE_COLOR_FG,
             'checkable':       False,
             'isFormatting':    True
            },
            {'type':            'cbutton',
             'id':              'bgColor',
             'tooltip':         i18n('Set current background color'),
             'icon':            buildIcon('pktk:format_text_bgcolor'),
             'action':          self.__updateSelectedTextBackgroundColor,
             'visibility':      WTextEditBtBarOption.STYLE_COLOR_BG,
             'checkable':       False,
             'isFormatting':    True
            },
            {'type':            'separator'},
            {'type':            'button',
             'id':              'textAlignLeft',
             'tooltip':         i18n('Set Left text alignment'),
             'icon':            buildIcon('pktk:format_text_align-left'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignLeft)),
             'group':           'text-align',
             'visibility':      WTextEditBtBarOption.ALIGNMENT,
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignCenter',
             'tooltip':         i18n('Set Centered text alignment'),
             'icon':            buildIcon('pktk:format_text_align-center'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignCenter)),
             'group':           'text-align',
             'visibility':      WTextEditBtBarOption.ALIGNMENT,
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignRight',
             'tooltip':         i18n('Set Right text alignment'),
             'icon':            buildIcon('pktk:format_text_align-right'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignRight)),
             'group':           'text-align',
             'visibility':      WTextEditBtBarOption.ALIGNMENT,
             'checkable':       True,
             'isFormatting':    True
            },
            {'type':            'button',
             'id':              'textAlignJustify',
             'tooltip':         i18n('Set Justified text alignment'),
             'icon':            buildIcon('pktk:format_text_align-justify'),
             'action':          (lambda: self.__textEdit.setAlignment(Qt.AlignJustify)),
             'group':           'text-align',
             'visibility':      WTextEditBtBarOption.ALIGNMENT,
             'checkable':       True,
             'isFormatting':    True
            }
        ]


        self.__undoAvailable=False
        self.__redoAvailable=False

        self.__initTextEdit()
        self.__initToolBar()

        self.__textEdit.undoAvailable.connect(self.__undoAvailableChanged)
        self.__textEdit.redoAvailable.connect(self.__redoAvailableChanged)
        self.__textEdit.selectionChanged.connect(self.__selectionChanged)

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

        [Copy] [Cut] [paste] | [Font name] [Font size] [Bold] [Italic] [Underline] [Strikethrough] [Fg Color] [Bg Color] | [Left alignment] [Center alignment] [Right alignment] [Justfied alignment]

        """
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(QMargins(0,0,0,0))

        groups = {}

        for item in self.__itemsDef:
            if item['type'] in ('button','cbutton'):
                policy = QSizePolicy()
                policy.setHorizontalPolicy(QSizePolicy.Maximum)

                if item['type'] == 'cbutton':
                    qItem = WColorButton(self.__toolBar)

                    qItem.colorChanged.connect(item['action'])
                    qItem.setNoneColor(True)
                    qItem.colorPicker().setOptionShowColorRGB(False)
                    qItem.colorPicker().setOptionShowColorCMYK(False)
                    qItem.colorPicker().setOptionShowColorHSV(False)
                    qItem.colorPicker().setOptionShowColorHSL(False)
                    qItem.colorPicker().setOptionShowColorAlpha(False)
                    qItem.colorPicker().setOptionShowCssRgb(False)
                    qItem.colorPicker().setOptionShowColorCombination(False)
                    qItem.colorPicker().setOptionShowColorPalette(True)
                    qItem.colorPicker().setOptionShowColorWheel(False)
                    qItem.colorPicker().setOptionCompactUi(False)
                    qItem.colorPicker().setOptionMenu(WColorPicker.OPTION_MENU_ALL&~WColorPicker.OPTION_MENU_ALPHA)
                else:
                    qItem = QToolButton(self.__toolBar)

                    if item['checkable']:
                        qItem.toggled.connect(item['action'])
                    else:
                        qItem.clicked.connect(item['action'])

                qItem.setIcon(item['icon'])
                qItem.setAutoRaise(True)
                qItem.setCheckable(item['checkable'])
                qItem.setSizePolicy(policy)

                if 'shortcut' in item:
                    qItem.setShortcut(item['shortcut'])

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


        if 'fontColor' in self.__toolBarItems and 'bgColor' in self.__toolBarItems:
            # when both menu are available, they should provide the same layout
            # each layout modification made on one has to be reported on other
            self.__toolBarItems['fontColor'].colorPicker().uiChanged.connect(self.__fgColorLayoutChanged)
            self.__toolBarItems['bgColor'].colorPicker().uiChanged.connect(self.__bgColorLayoutChanged)


        self.__updateToolbarBtnVisibility()
        self.__selectionChanged()
        self.__toolBar.setLayout(layout)


    def __fgColorLayoutChanged(self):
        """Layout for fg color menu has been modified"""
        if self.__ignoreColorMenuUpdate:
            return
        self.__ignoreColorMenuUpdate=True
        self.__toolBarItems['bgColor'].colorPicker().setOptionLayout(self.__toolBarItems['fontColor'].colorPicker().optionLayout())
        self.__ignoreColorMenuUpdate=False
        self.colorMenuUiChanged.emit(self.__toolBarItems['bgColor'].colorPicker().optionLayout())


    def __bgColorLayoutChanged(self):
        """Layout for bg color menu has been modified"""
        if self.__ignoreColorMenuUpdate:
            return
        self.__ignoreColorMenuUpdate=True
        self.__toolBarItems['fontColor'].colorPicker().setOptionLayout(self.__toolBarItems['bgColor'].colorPicker().optionLayout())
        self.__ignoreColorMenuUpdate=False
        self.colorMenuUiChanged.emit(self.__toolBarItems['fontColor'].colorPicker().optionLayout())


    def __updateToolbarBtnVisibility(self):
        """Update buttons visibility according to current configuration"""
        for item in self.__itemsDef:
            if 'visibility' in item:
                self.__toolBarItems[item['id']].setVisible((self.__toolbarBtn&item['visibility'])==item['visibility'])


    def __blockSignals(self, blocked):
        """Block (True) or Unblock(False) signals for formatting widgets"""
        for widget in self.__formattingWidgets:
            widget.blockSignals(blocked)


    def __undoAvailableChanged(self, value):
        """State for undo has been changed"""
        self.__undoAvailable=value
        self.__toolBarItems['undo'].setEnabled(self.__undoAvailable)


    def __redoAvailableChanged(self, value):
        """State for redo has been changed"""
        self.__redoAvailable=value
        self.__toolBarItems['redo'].setEnabled(self.__redoAvailable)


    def __selectionChanged(self):
        """Selection changed"""
        textCursor=self.__textEdit.textCursor()
        haveSelection=(textCursor.selectionStart()!=textCursor.selectionEnd())
        self.__toolBarItems['copy'].setEnabled(haveSelection)
        self.__toolBarItems['cut'].setEnabled(haveSelection)
        self.__toolBarItems['paste'].setEnabled(self.__textEdit.canPaste())


    def __processFragment(self, fragment, cStart, cEnd):
        """Return if fragment have to be processed """
        fs=fragment.position()
        fe=fs+fragment.length()
        return fs<=cStart and cStart < fe or fs<cEnd and cEnd < fe or fs >= cStart and fe <= cEnd

    def __updateSelectedTextFontColor(self, color):
        """Update font color

        Given `color` is a QEColor object
        """
        if color.isNone():
            cursor=self.__textEdit.textCursor()

            # original cursor selection start/end
            cStart=cursor.selectionStart()
            cEnd=cursor.selectionEnd()

            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, cEnd)
            lastBlock=cursor.block()

            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, cStart)
            currentBlock=cursor.block()


            cursor.beginEditBlock()
            while currentBlock.isValid():

                # iterate all fragments
                blockIterator = QTextBlock(currentBlock).begin()
                while not blockIterator.atEnd():
                    fragment = blockIterator.fragment()
                    if fragment.isValid():
                        if self.__processFragment(fragment, cStart, cEnd):
                            # process fragment only if impacted by selection

                            # get current format
                            fmt=fragment.charFormat()
                            # clear color
                            fmt.clearForeground()

                            # apply selection matching to fragment on original block
                            startPosition=max(fragment.position(), cStart)
                            endPosition=min(fragment.position() + fragment.length(), cEnd)

                            cursor.clearSelection()
                            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, startPosition)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, endPosition - startPosition)

                            # and apply format
                            cursor.setCharFormat(fmt)

                            if cursor.selectionEnd()>=cEnd:
                                # All selection processed, no need to continue
                                cursor.endEditBlock()
                                return
                        elif fragment.position()+fragment.length()>=cEnd:
                            # all processed, , no need to continue
                            # (should not occurs?)
                            cursor.endEditBlock()
                            return

                    blockIterator+=1

                if currentBlock==lastBlock:
                    # was last block...
                    # (should not occurs)
                    cursor.endEditBlock()
                    return
                currentBlock=currentBlock.next()

            cursor.endEditBlock()
        else:
            # else just apply color
            self.__textEdit.setTextColor(color)


    def __updateSelectedTextBackgroundColor(self, color):
        """Open a color dialog-box and set editor's background color"""
        """Update font color

        Given `color` is a QEColor object
        """
        if color.isNone():
            cursor=self.__textEdit.textCursor()

            # original cursor selection start/end
            cStart=cursor.selectionStart()
            cEnd=cursor.selectionEnd()

            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, cEnd)
            lastBlock=cursor.block()

            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, cStart)
            currentBlock=cursor.block()

            cursor.beginEditBlock()
            while currentBlock.isValid():

                # iterate all fragments
                blockIterator = QTextBlock(currentBlock).begin()
                while not blockIterator.atEnd():
                    fragment = blockIterator.fragment()
                    if fragment.isValid():
                        if self.__processFragment(fragment, cStart, cEnd):
                            # process fragment only if impacted by selection

                            # get current format
                            fmt=fragment.charFormat()
                            # clear color
                            fmt.clearBackground()

                            # apply selection matching to fragment on original block
                            startPosition=max(fragment.position(), cStart)
                            endPosition=min(fragment.position() + fragment.length(), cEnd)

                            cursor.clearSelection()
                            cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, startPosition)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, endPosition - startPosition)

                            # and apply format
                            cursor.setCharFormat(fmt)

                            if cursor.selectionEnd()>=cEnd:
                                # All selection processed, no need to continue
                                cursor.endEditBlock()
                                return
                        elif fragment.position()+fragment.length()>=cEnd:
                            # all processed, , no need to continue
                            # (should not occurs?)
                            cursor.endEditBlock()
                            return

                    blockIterator+=1

                if currentBlock==lastBlock:
                    # was last block...
                    # (should not occurs)
                    cursor.endEditBlock()
                    return
                currentBlock=currentBlock.next()

            cursor.endEditBlock()
        else:
            # else just apply color
            self.__textEdit.setTextBackgroundColor(color)


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
        self.__toolBarItems['fontStrikethrough'].setChecked(self.__isFontStrikethrough())

        self.__toolBarItems['fontColor'].setColor(self.__textEdit.textColor())
        self.__toolBarItems['bgColor'].setColor(self.__textEdit.textBackgroundColor())

        fg=self.__textEdit.textColor()
        bg=self.__textEdit.textBackgroundColor()

        self.__toolBarItems['textAlignLeft'].setChecked(self.__textEdit.alignment() == Qt.AlignLeft)
        self.__toolBarItems['textAlignCenter'].setChecked(self.__textEdit.alignment() == Qt.AlignCenter)
        self.__toolBarItems['textAlignRight'].setChecked(self.__textEdit.alignment() == Qt.AlignRight)
        self.__toolBarItems['textAlignJustify'].setChecked(self.__textEdit.alignment() == Qt.AlignJustify)

        self.__toolBarItems['undo'].setEnabled(self.__undoAvailable)
        self.__toolBarItems['redo'].setEnabled(self.__redoAvailable)

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


    def __isFontStrikethrough(self):
        """return if text under cursor is strikethrough or not"""
        cursor=self.__textEdit.textCursor()
        text=cursor.charFormat()
        return text.fontStrikeOut()


    def __setFontStrikethrough(self):
        """Change current selection to striketrhough"""
        cursor=self.__textEdit.textCursor()
        text=cursor.charFormat()
        text.setFontStrikeOut(not text.fontStrikeOut())
        cursor.mergeCharFormat(text)


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


    def toolbarButtons(self):
        """Return toolbar buttons visiblity"""
        return self.__toolbarBtn


    def setToolbarButtons(self, value, mode=None):
        """Define buttons visible in toolbar

        `value`=toolbar options combination
        `mode`=how to apply option
            When WTextEditBtBarOption.MODE_SET (default): apply defined buttons
            When WTextEditBtBarOption.MODE_ADD: add given buttons
            When WTextEditBtBarOption.MODE_REMOVE: removed given buttons
        """
        if not isinstance(value, int):
            raise EInvalidType('Given `value` must be an <int>')

        if mode is None:
            mode=WTextEditBtBarOption.MODE_SET

        if not mode in (WTextEditBtBarOption.MODE_SET, WTextEditBtBarOption.MODE_ADD, WTextEditBtBarOption.MODE_REMOVE):
            raise EInvalidValue('Given `value` is not valid')

        if mode==WTextEditBtBarOption.MODE_SET:
            self.__toolbarBtn=value
        elif mode==WTextEditBtBarOption.MODE_ADD:
            self.__toolbarBtn|=value
        elif mode==WTextEditBtBarOption.MODE_REMOVE:
            self.__toolbarBtn&=(self.__toolbarBtn^value)

        self.__updateToolbarBtnVisibility()


    def setColorPickerLayout(self, layout):
        """Set layout for fg/bg color picker"""
        if 'fontColor' in self.__toolBarItems:
            self.__toolBarItems['fontColor'].colorPicker().setOptionLayout(layout)
        elif 'bgColor' in self.__toolBarItems:
            self.__toolBarItems['bgColor'].colorPicker().setOptionLayout(layout)


    def colorPickerLayout(self):
        """Return layout for fg/bg color picker"""
        if 'fontColor' in self.__toolBarItems:
            return self.__toolBarItems['fontColor'].colorPicker().optionLayout()
        elif 'bgColor' in self.__toolBarItems:
            return self.__toolBarItems['return'].colorPicker().optionLayout()
        else:
            return []


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
