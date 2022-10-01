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
# The wcodeeditor module provides a basic code editor widget
# - syntax highlighting
# - autocompletion
# - line number
# - ...
#
# Main class from this module
#
# - WCodeEditor:
#       Widget
#       The code editor
#
# - Other
#       used for gutter rendering, autocompletion, syntax highlighting...
#
# -----------------------------------------------------------------------------

# From Qt documentation example "Code Editor"
#  https://doc.qt.io/qtforpython-5.12/overviews/qtwidgets-widgets-codeeditor-example.html

from math import ceil
import re

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget,
        QPlainTextEdit,
        QToolTip
    )
from PyQt5.QtGui import (
        QSyntaxHighlighter,
        QTextCharFormat,
        QColor
    )
from ..modules.languagedef import LanguageDef
from ..modules.tokenizer import (
        TokenStyle,
        TokenType,
        Tokenizer,
        Token
    )

from .wsearchinput import SearchFromPlainTextEdit

from ..pktk import *


class WCodeEditor(QPlainTextEdit):
    """Extended editor with syntax highlighting, autocompletion, line number..."""

    cursorCoordinatesChanged = Signal(QPoint, QPoint, QPoint, int)  # cursor position, selection start position, selection end position, selection length
    overwriteModeChanged = Signal(bool)     # INS / OVR mode changed
    readOnlyModeChanged = Signal(bool)      # read-only mode changed
    autoCompletionChanged = Signal(str)     # auto completion item has changed

    KEY_INDENT = 'indent'
    KEY_DEDENT = 'dedent'
    KEY_TOGGLE_COMMENT = 'toggleComment'
    KEY_AUTOINDENT = 'autoIndent'
    KEY_COMPLETION = 'completion'
    KEY_INSERTOVERWRITE_MODE = 'insertOverwriteMode'

    CTRL_KEY_TRUE = True
    CTRL_KEY_FALSE = False

    def __init__(self, parent=None, languageDef=None):
        super(WCodeEditor, self).__init__(parent)

        self.__languageDef = None
        self.__highlighter = None

        # token currently under cursor
        self.__cursorToken = None
        # tokens currently from cursor's row position
        self.__cursorTokens = None

        # current cursor position
        self.__cursorCol = 0
        self.__cursorRow = 0
        self.__cursorRect = None

        self.__cursorSelColStart = 0
        self.__cursorSelRowStart = 0
        self.__cursorSelColEnd = 0
        self.__cursorSelRowEnd = 0
        self.__cursorSelLen = 0

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # ---- options ----
        # > TODO: need to define setters/getters

        # allows text with multiple lines
        self.__optionMultiLine = True

        self.__optionCommentChar = '#'

        # Gutter colors
        # maybe font size/type/style can be modified
        self.__optionGutterText = QTextCharFormat()
        self.__optionGutterText.setForeground(QColor('#4c5363'))
        self.__optionGutterText.setBackground(QColor('#282c34'))

        # editor current's selected line
        self.__optionColorHighlightedLine = QColor('#2d323c')

        # show line number
        self.__optionShowLineNumber = True

        # space indent width
        self.__optionIndentWidth = 4
        self.__optionShowIndentLevel = True

        # right limit properties
        self.__optionRightLimitVisible = True
        self.__optionRightLimitPosition = 80
        self.__optionRightLimitColor = QColor('#88555555')

        # spaces properties
        self.__optionShowSpaces = True
        self.__optionSpacesColor = QColor("#88666666")

        # autocompletion is automatic (True) or manual (False)
        self.__optionAutoCompletion = True

        # display auto completion help (True) or not (False)
        self.__optionAutoCompletionHelp = True

        # autocompletion popup max number of items
        self.__optionAutoCompletionMaxItems = 25

        # allows key bindings
        self.__optionWheelSetFontSize = True

        self.__shortCuts = {
            Qt.Key_Tab: {
                    WCodeEditor.CTRL_KEY_FALSE: WCodeEditor.KEY_INDENT
                },
            Qt.Key_Backtab: {
                    # SHIFT+TAB = BACKTAB
                    WCodeEditor.CTRL_KEY_FALSE: WCodeEditor.KEY_DEDENT
                },
            Qt.Key_Slash: {
                    WCodeEditor.CTRL_KEY_TRUE: WCodeEditor.KEY_TOGGLE_COMMENT
                },
            Qt.Key_Return: {
                    WCodeEditor.CTRL_KEY_FALSE: WCodeEditor.KEY_AUTOINDENT
                },
            Qt.Key_Space: {
                    WCodeEditor.CTRL_KEY_TRUE: WCodeEditor.KEY_COMPLETION
                },
            Qt.Key_Insert: {
                    WCodeEditor.CTRL_KEY_FALSE: WCodeEditor.KEY_INSERTOVERWRITE_MODE
                }
        }

        # ---- Set default font (monospace, 10pt)
        font = QFont()
        font.setFamily('DejaVu Sans Mono, Consolas, Courier New')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)

        palette = self.palette()
        palette.setColor(QPalette.Active, QPalette.Base, QColor('#282c34'))
        palette.setColor(QPalette.Inactive, QPalette.Base, QColor('#282c34'))

        # ---- instanciate line number area
        self.__lineNumberArea = WCELineNumberArea(self)

        # ---- initialise signals
        self.blockCountChanged.connect(self.__updateLineNumberAreaWidth)
        self.updateRequest.connect(self.__updateLineNumberArea)
        self.cursorPositionChanged.connect(self.__highlightCurrentLine)
        self.textChanged.connect(self.__updateCurrentPositionAndToken)
        self.selectionChanged.connect(self.__updateCurrentPositionAndToken)
        self.customContextMenuRequested.connect(self.__contextMenu)

        # ---- initialise completion list model
        self.__completerModel = WCECompleterModel()

        # set dictionary + syntax highlighter
        self.setLanguageDefinition(languageDef)

        # ---- initialise completer
        self.__completer = QCompleter()
        self.__completer.setModel(self.__completerModel)
        self.__completer.setWidget(self)
        self.__completer.setCompletionColumn(0)
        self.__completer.setCompletionRole(Qt.DisplayRole)
        self.__completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.__completer.setCompletionMode(QCompleter.PopupCompletion)
        self.__completer.setMaxVisibleItems(self.__optionAutoCompletionMaxItems)
        self.__completer.activated.connect(self.__insertCompletion)
        self.__completer.highlighted[QModelIndex].connect(self.__displayCompleterHint)
        self.__completer.highlighted[str].connect(lambda value: self.autoCompletionChanged.emit(value))

        # ---- initialise customized item rendering for completer
        self.__completer.popup().setFont(font)
        self.__completer.popup().setItemDelegate(WCECompleterView(self))

        self.__completerLastSelectedIndex = None

        # ---- search object
        self.__search = SearchFromPlainTextEdit(self)

        # default values
        self.__updateLineNumberAreaWidth()
        self.__highlightCurrentLine()
        self.__hideCompleterHint()

    def __updateCurrentPositionAndToken(self, force=True):
        """Calculate current cursor position and current token"""
        previousCol, previousRow = self.__cursorCol, self.__cursorRow

        cursor = self.textCursor()
        self.__cursorCol = cursor.columnNumber()
        self.__cursorRow = cursor.blockNumber()

        if not force and previousCol == self.__cursorCol and previousRow == self.__cursorRow:
            return

        if self.__languageDef is None or self.__highlighter is None:
            self.__cursorToken = None
            return

        if self.__cursorRow != previousRow or self.__cursorTokens is None or force:
            self.__cursorTokens = self.__languageDef.tokenizer().tokenize(cursor.block().text())

        # row is always 1 here as tokenized text is only current row
        self.__cursorToken = self.__cursorTokens.tokenAt(self.__cursorCol + 1, 1)

        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()

        self.__cursorSelLen = selectionEnd - selectionStart

        if self.__cursorSelLen == 0:
            self.__cursorSelColStart = self.__cursorCol
            self.__cursorSelRowStart = self.__cursorRow
            self.__cursorSelColEnd = self.__cursorCol
            self.__cursorSelRowEnd = self.__cursorRow
            self.cursorCoordinatesChanged.emit(QPoint(self.__cursorCol, self.__cursorRow),
                                               QPoint(self.__cursorCol, self.__cursorRow),
                                               QPoint(self.__cursorCol, self.__cursorRow),
                                               0)
        else:
            # determinate block numbers
            cursor.setPosition(selectionStart)
            self.__cursorSelColStart = cursor.columnNumber()+1
            self.__cursorSelRowStart = cursor.blockNumber()+1

            cursor.setPosition(selectionEnd)
            self.__cursorSelColEnd = cursor.columnNumber()+1
            self.__cursorSelRowEnd = cursor.blockNumber()+1

            self.cursorCoordinatesChanged.emit(QPoint(self.__cursorCol, self.__cursorRow),
                                               QPoint(self.__cursorSelColStart, self.__cursorSelRowStart),
                                               QPoint(self.__cursorSelColEnd, self.__cursorSelRowEnd),
                                               self.__cursorSelLen)

    def __hideCompleterHint(self):
        """Hide completer hint"""
        QToolTip.showText(self.mapToGlobal(QPoint()), '')
        QToolTip.hideText()
        self.__completerLastSelectedIndex = None
        self.__cursorRect = None

    def __displayCompleterHint(self, index=None):
        """Display completer hint"""
        if self.__cursorRect is None:
            self.__hideCompleterHint()
            return

        if index is None:
            index = self.__completerLastSelectedIndex

        if index is None:
            index = self.__completer.currentIndex()

        if index is None:
            self.__hideCompleterHint()
            return

        tooltipHelp = index.data(WCECompleterModel.DESCRIPTION)
        if tooltipHelp is None or tooltipHelp == '':
            self.__hideCompleterHint()
            return
        elif self.__optionAutoCompletionHelp:
            position = QPoint(self.__cursorRect.left() + self.__cursorRect.width(), self.__cursorRect.top() + self.__completer.popup().visualRect(index).top())
            # it's not possible to move a tooltip
            # need to set a different value to force tooltip being refreshed to new position
            QToolTip.showText(self.mapToGlobal(position), tooltipHelp+' ')
            QToolTip.showText(self.mapToGlobal(position), tooltipHelp, self, QRect(), 600000)  # 10minutes..
            self.__completerLastSelectedIndex = index

    def __insertCompletion(self, completion):
        """Text selected from auto completion list, insert it at cursor's place"""
        try:
            value = completion.replace(LanguageDef.SEP_SECONDARY_VALUE, '').split(LanguageDef.SEP_PRIMARY_VALUE)[1]
        except Exception:
            value = ''
        texts = completion.replace(LanguageDef.SEP_SECONDARY_VALUE, '').split(LanguageDef.SEP_PRIMARY_VALUE)[::2]

        token = self.cursorToken(False)
        if token is None:
            token = self.cursorToken()

        if token is None:
            moveRight = 0
        else:
            moveRight = token.length() - (self.__cursorCol - token.column() + 1)

        extra = (len(texts[0]) - len(self.__completer.completionPrefix()))

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, moveRight)
        cursor.insertText(texts[0][-extra:])

        if len(texts) > 1:
            p = cursor.anchor()

            self.moveCursor(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            if self.textCursor().selectedText().strip() == '':
                # if next character is space or there's no next character, full auto completion
                cursor.insertText(value+"".join(texts[1:]))
            cursor.setPosition(p, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)

    def __contextMenu(self):
        """Extend default context menu for editor"""
        standardMenu = self.createStandardContextMenu()

        # standardMenu.addSeparator()
        # standardMenu.addAction(u'Test', self.doAction)

        self.contextMenu(standardMenu)

        standardMenu.exec(QCursor.pos())

    def __updateLineNumberAreaWidth(self, dummy=None):
        """Called on signal blockCountChanged()

        Update viewport margins, taking in account (new) total number of lines
        """
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def __updateLineNumberArea(self, rect, deltaY):
        """Called on signal updateRequest()

        Invoked when the editors viewport has been scrolled

        The given `rect` is the part of the editing area that need to be updated (redrawn)
        The given `dy` holds the number of pixels the view has been scrolled vertically
        """
        if self.__optionShowLineNumber:
            if deltaY > 0:
                self.__lineNumberArea.scroll(0, deltaY)
            else:
                self.__lineNumberArea.update(0, rect.y(), self.__lineNumberArea.width(), rect.height())

            if rect.contains(self.viewport().rect()):
                self.__updateLineNumberAreaWidth(0)

    def __highlightCurrentLine(self):
        """When the cursor position changes, highlight the current line (the line containing the cursor)"""
        # manage
        extraSelections = self.extraSelections()

        # remove current selection from extra selection list
        # => can't clear selection as maybe, there's other extra selection
        for selection in extraSelections:
            if selection.format.boolProperty(QTextFormat.FullWidthSelection):
                # found, remove it and exit, no need to continue to search there's normaly only
                # one extra selection like this one
                extraSelections.remove(selection)
                break

        if self.__optionMultiLine and not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            selection.format.setBackground(self.__optionColorHighlightedLine)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()

            # insert at beginning, must be the first extra selection rendered
            # especially if there's extra selection from "search"
            extraSelections.insert(0, selection)

        self.setExtraSelections(extraSelections)
        self.__updateCurrentPositionAndToken(False)

    def __isEmptyBlock(self, blockNumber):
        """Check is line for current block is empty or not"""
        # get block text
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, n=blockNumber)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        text = cursor.selectedText()
        if text.strip() == "":
            return True
        else:
            return False

    def __calculateIndent(self, position):
        """Calculate indent to apply according to current position"""
        indentValue = ceil(position/self.__optionIndentWidth)*self.__optionIndentWidth - position
        if indentValue == 0:
            indentValue = self.__optionIndentWidth
        return indentValue

    def __calculateDedent(self, position):
        """calculate indent to apply according to current position"""
        if position > 0:
            dedentValue = position % self.__optionIndentWidth
            if dedentValue == 0:
                return self.__optionIndentWidth
            else:
                return dedentValue

        return 0

    # region: event overload ---------------------------------------------------

    def resizeEvent(self, event):
        """Code editor is resized

        Need to resize the line number area
        """
        super(WCodeEditor, self).resizeEvent(event)

        if self.__optionShowLineNumber:
            contentRect = self.contentsRect()
            self.__lineNumberArea.setGeometry(QRect(contentRect.left(), contentRect.top(), self.lineNumberAreaWidth(), contentRect.height()))

    def lineNumberAreaPaintEvent(self, event):
        """Paint gutter content"""
        # initialise painter on WCELineNumberArea
        painter = QPainter(self.__lineNumberArea)

        # set background
        painter.fillRect(event.rect(), self.__optionGutterText.background())

        # Get the top and bottom y-coordinate of the first text block,
        # and adjust these values by the height of the current text block in each iteration in the loop
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Loop through all visible lines and paint the line numbers in the extra area for each line.
        # Note: in a plain text edit each line will consist of one QTextBlock
        #       if line wrapping is enabled, a line may span several rows in the text edit’s viewport
        while block.isValid() and top <= event.rect().bottom():
            # Check if the block is visible in addition to check if it is in the areas viewport
            #   a block can, for example, be hidden by a window placed over the text edit
            if block.isVisible() and bottom >= event.rect().top():
                number = f"{blockNumber + 1}"
                painter.setPen(self.__optionGutterText.foreground().color())
                painter.drawText(0, top, self.__lineNumberArea.width(), self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def wheelEvent(self, event):
        """CTRL + wheel os used to zoom in/out font size"""
        if self.__optionWheelSetFontSize and event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta < 0:
                self.zoomOut()
            elif delta > 0:
                self.zoomIn()
        else:
            super(WCodeEditor, self).wheelEvent(event)

    def keyPressEvent(self, event):
        """Improve editor functionalities with some key bindings"""
        if self.__completer and self.__completer.popup().isVisible():
            # completion popup is visible, so keypressed is for popup
            if event.key() in (
                        Qt.Key_Enter,
                        Qt.Key_Return,
                        Qt.Key_Escape,
                        Qt.Key_Tab,
                        Qt.Key_Backtab):
                event.ignore()
                return

        if not self.__optionMultiLine and event.key() in (
                                                    Qt.Key_Enter,
                                                    Qt.Key_Return):
            event.ignore()
            return

        # retrieve action from current shortcut
        action = self.shortCut(event.key(), event.modifiers())

        if action is None:
            super(WCodeEditor, self).keyPressEvent(event)
            # if no action is defined and autocompletion is active, display
            # completer list automatically if key pressed is not an arrow key to move caret
            if self.__optionAutoCompletion and not event.key() in (Qt.Key_Insert,
                                                                   Qt.Key_Home,
                                                                   Qt.Key_End,
                                                                   Qt.Key_Left,
                                                                   Qt.Key_Right,
                                                                   Qt.Key_Up,
                                                                   Qt.Key_Down,
                                                                   Qt.Key_PageUp,
                                                                   Qt.Key_PageDown,
                                                                   Qt.Key_Shift,
                                                                   Qt.Key_Control,
                                                                   Qt.Key_Meta,
                                                                   Qt.Key_Alt):
                action = WCodeEditor.KEY_COMPLETION
        elif event.key() == Qt.Key_Return:
            super(WCodeEditor, self).keyPressEvent(event)

        self.doAction(action)

    def paintEvent(self, event):
        """Customize painting"""
        super(WCodeEditor, self).paintEvent(event)

        if not(self.__optionRightLimitVisible or self.__optionShowSpaces or self.__optionShowIndentLevel):
            return

        # initialise some metrics
        rect = event.rect()
        font = self.currentCharFormat().font()
        charWidth = QFontMetricsF(font).averageCharWidth()
        leftOffset = self.contentOffset().x() + self.document().documentMargin()

        # initialise painter to editor's viewport
        painter = QPainter(self.viewport())

        if self.__optionRightLimitVisible:
            # draw right limit
            position = round(charWidth * self.__optionRightLimitPosition) + leftOffset
            painter.setPen(self.__optionRightLimitColor)
            painter.drawLine(position, rect.top(), position, rect.bottom())

        if not(self.__optionShowSpaces or self.__optionShowIndentLevel):
            return

        # draw spaces and/or level indent
        block = self.firstVisibleBlock()

        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(self.__optionSpacesColor)
        previousIndent = 0

        while block.isValid() and top <= event.rect().bottom():
            # Check if the block is visible in addition to check if it is in the areas viewport
            #   a block can, for example, be hidden by a window placed over the text edit
            if block.isVisible() and bottom >= event.rect().top():
                result = re.search(r"(\s*)$", block.text())
                posSpacesRight = 0
                nbSpacesLeft = len(re.match(r"(\s*)", block.text()).groups()[0])
                nbSpacesRight = len(result.groups()[0])
                if nbSpacesRight > 0:
                    posSpacesRight = result.start()

                left = leftOffset

                if self.__optionShowSpaces:
                    # draw spaces
                    for i in range(nbSpacesLeft):
                        painter.drawText(left, top, charWidth, self.fontMetrics().height(), Qt.AlignLeft, '.')
                        left += charWidth

                    left = leftOffset + charWidth * posSpacesRight
                    for i in range(nbSpacesRight):
                        painter.drawText(left, top, charWidth, self.fontMetrics().height(), Qt.AlignLeft, '.')
                        left += charWidth

                if self.__optionShowIndentLevel:
                    # draw level indent
                    if nbSpacesLeft > 0 or previousIndent > 0:
                        # if spaces or previous indent, check if level indent have to be drawn
                        if len(block.text()) == 0:
                            # current block is empty (even no spaces)
                            # look forward for next block with level > 0
                            # if found, keep current indent otherwhise, no indent
                            nBlockText = block.next()
                            while nBlockText.blockNumber() > -1 and nBlockText.isVisible():
                                if nBlockText is None:
                                    break
                                if len(nBlockText.text()) > 0:
                                    nNbSpacesLeft = len(re.match(r"(\s*)", nBlockText.text()).groups()[0])
                                    if nNbSpacesLeft == 0:
                                        nbSpacesLeft = 0
                                    else:
                                        nbSpacesLeft = previousIndent
                                    break
                                nBlockText = nBlockText.next()
                        elif len(block.text().strip()) == 0:
                            # current block is only spaces, then draw level indent
                            nbSpacesLeft = max(previousIndent, nbSpacesLeft)
                        else:
                            previousIndent = nbSpacesLeft

                        left = leftOffset + round(charWidth*2/3, 0)
                        nbChar = 0
                        while nbChar < nbSpacesLeft:
                            position = round(charWidth * nbChar) + leftOffset
                            painter.drawLine(position, top, position, top + self.blockBoundingRect(block).height() - 1)
                            nbChar += self.__optionIndentWidth
                    elif len(block.text().strip()) > 0:
                        previousIndent = 0

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

    def setReadOnly(self, value):
        """Override method to implement signal readOnlyModeChanged"""
        ro = self.isReadOnly()
        super(WCodeEditor, self).setReadOnly(value)

        if value != ro:
            self.readOnlyModeChanged.emit(value)

    def insertFromMimeData(self, source):
        """Data from clipboad are being pasted

        replace tabs by spaces and paste content
        """
        if source.hasText():
            text = source.text()
            if not self.__optionMultiLine:
                # no multiline, replace linefeed by space...
                text = text.replace('\n', ' ')
            text = text.replace('\t', ' ' * self.__optionIndentWidth)
            cursor = self.textCursor()
            cursor.insertText(text)

    # endregion: event overload ------------------------------------------------

    def contextMenu(self, standardMenu):
        """Virtual: have to be overrided"""
        pass

    def lineNumberAreaWidth(self):
        """Calculate width for line number area

        Width is calculated according to number of lines
           X lines => 1 digit
          XX lines => 2 digits
         XXX lines => 3 digits
        XXXX lines => 4 digits
        ...
        """
        if self.__optionShowLineNumber:
            # start with 2digits (always have space for one digit more)
            digits = 2
            maxBlock = max(1, self.blockCount())
            while maxBlock >= 10:
                maxBlock /= 10
                digits += 1

            # width = (witdh for digit '9') * (number of digits) + 3pixels
            return 3 + self.fontMetrics().width('9') * digits
        return 0

    def doAction(self, action=None):
        """Execute given action"""
        if action is None:
            return
        elif action == WCodeEditor.KEY_INDENT:
            self.doIndent()
        elif action == WCodeEditor.KEY_DEDENT:
            self.doDedent()
        elif action == WCodeEditor.KEY_TOGGLE_COMMENT:
            self.doToggleComment()
        elif action == WCodeEditor.KEY_AUTOINDENT:
            self.doAutoIndent()
        elif action == WCodeEditor.KEY_COMPLETION:
            self.doCompletionPopup()
        elif action == WCodeEditor.KEY_INSERTOVERWRITE_MODE:
            self.doOverwriteMode()

    def shortCut(self, key, modifiers):
        """Return action for given key/modifier shortCut

        If nothing is defined, return None
        """
        if key in self.__shortCuts:
            ctrlModifier = (Qt.ControlModifier & modifiers == Qt.ControlModifier)
            if ctrlModifier in self.__shortCuts[key]:
                return self.__shortCuts[key][ctrlModifier]
        return None

    def setShortCut(self, key, modifiers, action):
        """Set action for given key/modifier"""
        if action not in (None,
                          WCodeEditor.KEY_INDENT,
                          WCodeEditor.KEY_DEDENT,
                          WCodeEditor.KEY_TOGGLE_COMMENT):
            raise EInvalidValue('Given `action` is not a valid value')

        if modifiers is None:
            modifiers = WCodeEditor.CTRL_KEY_FALSE

        if key not in self.__shortCuts:
            self.__shortCuts[key] = {}

        self.__shortCuts[key][modifiers] = action

    def actionShortCut(self, action):
        """Return shortcut for given action

        If nothing is defined or action doesn't exists, return None
        If found, Shortcut is returned as a tuple (key, modifiers)
        """
        for key in self.__shortCuts:
            for modifiers in self.__shortCuts[key]:
                if self.__shortCuts[key][modifiers] == action:
                    return (key, modifiers)
        return None

    def doAutoIndent(self):
        """Indent current line to match indent of previous line

        if no previous exists, then, no indent...
        """

        cursor = self.textCursor()

        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()

        # determinate block numbers
        cursor.setPosition(selectionStart)
        startBlock = cursor.blockNumber()

        cursor.setPosition(selectionEnd)
        endBlock = cursor.blockNumber()

        cursor.movePosition(QTextCursor.Start)

        indentSize = 0
        if startBlock > 0:
            cursor.movePosition(QTextCursor.NextBlock, n=startBlock-1)
            # calculate indentation of previous block
            indentSize = len(cursor.block().text()) - len(cursor.block().text().lstrip())
            cursor.movePosition(QTextCursor.NextBlock)
        else:
            cursor.movePosition(QTextCursor.NextBlock, n=startBlock)

        # determinate if spaces have to be added or removed
        nbChar = indentSize - (len(cursor.block().text()) - len(cursor.block().text().lstrip()))

        cursor.movePosition(QTextCursor.StartOfLine)
        if nbChar > 0:
            cursor.insertText(" " * nbChar)
        else:
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, -nbChar)
            cursor.removeSelectedText()

    def doIndent(self):
        """Indent current line or current selection"""

        cursor = self.textCursor()

        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()

        if selectionStart == selectionEnd:
            # No selection: just insert spaces
            # Note:
            #   Editor don't add a number of 'indent' spaces, but insert spaces
            #   to match to column position
            #
            #   Example: indent space = 4
            #            columns: 4, 8, 12, 16, 20, ...
            #
            #            x = cursor position
            #            o = cursor position after tab
            #            ...|...|...|...|...
            #            x  o
            #                x  o
            #                          xo

            # calculate position relative to start of line
            cursorSol = self.textCursor()
            cursorSol.movePosition(QTextCursor.StartOfLine)
            positionSol = (selectionStart - cursorSol.selectionStart())

            cursor.insertText(" " * self.__calculateIndent(positionSol))
            return

        # determinate block numbers
        cursor.setPosition(selectionStart)
        startBlock = cursor.blockNumber()

        cursor.setPosition(selectionEnd)
        endBlock = cursor.blockNumber()

        # determinate if last block have to be processed
        # exemple:
        #
        #   +-- Start of selection
        #   V
        #   *   Line 1
        #       Line 2
        #   *   Line 3
        #   ^
        #   +-- End of selection
        #
        #   In this case, only the first 2 lines are processed, not the last (nothing selected on last line)
        #
        #
        #   +-- Start of selection
        #   V
        #   *   Line 1
        #       Line 2
        #       Li*e 3
        #         ^
        #         +-- End of selection
        #
        #   In this case, the 3 lines are processed
        #
        processLastBlock = cursor.selectionStart()
        cursor.movePosition(QTextCursor.StartOfLine)
        processLastBlock -= cursor.selectionStart()
        if processLastBlock > 0:
            processLastBlock = 1

        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, n=startBlock)

        for blockNumber in range(startBlock, endBlock+processLastBlock):
            if not self.__isEmptyBlock(blockNumber):
                # empty lines are not indented
                nbChar = len(cursor.block().text()) - len(cursor.block().text().lstrip())
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.insertText(" " * self.__calculateIndent(nbChar))

            cursor.movePosition(QTextCursor.NextBlock)

    def doDedent(self):
        """Dedent current line or current selection"""
        cursor = self.textCursor()

        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()

        # determinate block numbers
        cursor.setPosition(selectionStart)
        startBlock = cursor.blockNumber()

        cursor.setPosition(selectionEnd)
        endBlock = cursor.blockNumber()

        processLastBlock = cursor.selectionStart()
        cursor.movePosition(QTextCursor.StartOfLine)
        processLastBlock -= cursor.selectionStart()
        if processLastBlock > 0 or selectionStart == selectionEnd:
            processLastBlock = 1

        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, n=startBlock)

        for blockNumber in range(startBlock, endBlock + processLastBlock):
            nbChar = self.__calculateDedent(len(cursor.block().text()) - len(cursor.block().text().lstrip()))
            if nbChar > 0:
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, nbChar)
                cursor.removeSelectedText()

            cursor.movePosition(QTextCursor.NextBlock)

    def doToggleComment(self):
        """Toggle comment for current line or selected lines"""
        cursor = self.textCursor()

        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()

        # determinate block numbers
        cursor.setPosition(selectionStart)
        startBlock = cursor.blockNumber()

        cursor.setPosition(selectionEnd)
        endBlock = cursor.blockNumber()

        processLastBlock = cursor.selectionStart()
        cursor.movePosition(QTextCursor.StartOfLine)
        processLastBlock -= cursor.selectionStart()
        if processLastBlock > 0 or selectionStart == selectionEnd:
            processLastBlock = 1

        # True = COMMENT
        # False = UNCOMMENT
        hasUncommented = False

        # Work with 2 pass
        # Pass #1
        #    Look all blocks
        #       if at least one block is not commented, then active COMMENT
        #       if ALL block are commented, then active UNCOMMENT
        # Pass #2
        #    Apply COMMENT/UNCOMMENT

        # Pass 1
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, n=startBlock)

        for blockNumber in range(startBlock, endBlock + processLastBlock):
            blockText = cursor.block().text()

            if re.match(r'^\s*'+re.escape(self.__optionCommentChar), blockText) is None:
                hasUncommented = True
                # dont' need to continue to look content, we know that we have to comment selected text
                break
            cursor.movePosition(QTextCursor.NextBlock)

        # Pass 2
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.NextBlock, n=startBlock)

        for blockNumber in range(startBlock, endBlock + processLastBlock):
            blockText = cursor.block().text()

            commentPosition = len(blockText) - len(blockText.lstrip())
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, commentPosition)

            if hasUncommented:
                # Comment
                cursor.insertText(self.__optionCommentChar+' ')
            else:
                # Uncomment
                # Remove hashtag and all following spaces
                hashtag = re.search(fr'({re.escape(self.__optionCommentChar)}+[\s]*)', blockText)

                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(hashtag.groups()[0]))
                cursor.removeSelectedText()

            cursor.movePosition(QTextCursor.NextBlock)

    def doCompletionPopup(self):
        """Display autocompletion popup"""
        def popupHide():
            self.__hideCompleterHint()
            self.__completer.popup().hide()
            return False

        if self.__languageDef is None or self.__highlighter is None:
            return popupHide()

        currentToken = None
        displayPopup = False
        minLength = 0

        currentToken = self.cursorToken(False)

        if not currentToken:
            # no token, try from highlight syntaxing
            currentToken = self.__highlighter.currentCursorToken()

        refToken = currentToken
        srcText = ""

        # Determinate current text
        if currentToken is None:
            # try with last processed token
            currentToken = self.__highlighter.lastCursorToken()
        else:
            srcText = currentToken.text()

        if currentToken is None:
            #  or len(currentToken.rule().autoCompletion()) == 0
            # no text and/or current token type don't provide autoCompletion
            return popupHide()

        text = currentToken.text()
        if len(text) < 1:
            # if current text is less than one character, do not display popup
            return popupHide()

        # try to determinate text
        while True:
            if currentToken.previous() is None:
                break

            if not currentToken.type() in (TokenType.SPACE, TokenType.UNKNOWN) and currentToken.previous().type() != currentToken.type():
                break

            currentToken = currentToken.previous()
            if currentToken.type() == TokenType.SPACE:
                text = " " + text
            else:
                text = currentToken.text() + text

        proposals = self.__languageDef.getTextProposal(text)
        if len(proposals) == 0:
            # if we can't found completion values from current text, use initial text
            text = srcText
            proposals = self.__languageDef.getTextProposal(text)
            if len(proposals) == 0 or len(proposals) == 1 and proposals[0] == text:
                return popupHide()
        elif len(proposals) == 1 and proposals[0] == text:
            # if we only found current text, do not display popup
            return popupHide()

        if len(text) < 1:
            # if current text is less than one character, do not display popup
            return popupHide()

        if text != self.__completer.completionPrefix():
            self.__completer.setCompletionPrefix(text)
            popup = self.__completer.popup()
            popup.setCurrentIndex(self.__completer.completionModel().index(0, 0))
            displayPopup = True

        self.__cursorRect = self.cursorRect()
        self.__cursorRect.setWidth(self.__completer.popup().sizeHintForColumn(0) + self.__completer.popup().verticalScrollBar().sizeHint().width())
        self.__completer.complete(self.__cursorRect)
        self.__displayCompleterHint()

        return displayPopup

    def doOverwriteMode(self, mode=None):
        """Change current insert/overwrite mode

        If mode is None, switch current mode
        Otherwise given `mode` is a boolean:
        - False = insert
        - True = overwrite
        """
        changed = False

        if mode is None:
            mode = not self.overwriteMode()

        changed = (mode != self.overwriteMode())
        if changed:
            self.setOverwriteMode(mode)
            self.overwriteModeChanged.emit(mode)

    def languageDefinition(self):
        """Return current language definition"""
        return self.__languageDef

    def setLanguageDefinition(self, languageDef):
        """Set current language definition"""
        if not (languageDef is None or isinstance(languageDef, LanguageDef)):
            raise EInvalidType('Given `languageDef` must be <LanguageDef> type')

        self.__completerModel.clear()

        if languageDef is not None:
            self.__languageDef = languageDef
            self.__highlighter = WCESyntaxHighlighter(self.document(), self.__languageDef, self)

            for rule in self.__languageDef.tokenizer().rules():
                for autoCompletion in rule.autoCompletion():
                    self.__completerModel.add(autoCompletion[0], rule.type(),  self.__languageDef.style(rule), autoCompletion[1], rule.autoCompletionChar())
            self.__completerModel.sort()
        else:
            if isinstance(self.__highlighter, QSyntaxHighlighter):
                self.__highlighter.setDocument(None)
            self.__highlighter = None

            cursor = self.textCursor()
            cursor.select(QTextCursor.Document)
            cursor.setCharFormat(QTextCharFormat())
            cursor.clearSelection()

    def optionMultiLine(self):
        """Return if editor accept multine line or not"""
        return self.__optionMultiLine

    def setOptionMultiLine(self, value):
        """Set if editor accept multine line or not"""
        if isinstance(value, bool) and value != self.__optionMultiLine:
            self.__optionMultiLine = value
            if value:
                self.setHeight()
            else:
                self.setHeight(1)
            self.__highlightCurrentLine()
            self.update()

    def optionCommentCharacter(self):
        """Return comment character (for toggle comment action)"""
        return self.__optionCommentChar

    def setOptionCommentCharacter(self, value):
        """Set comment character (for toggle comment action)"""
        if isinstance(value, str) and value != self.__optionCommentChar:
            self.__optionCommentChar = value

    def optionGutterText(self):
        """Return current gutter (line number) style (QTextCharFormat)"""
        return self.__optionGutterText

    def setOptionGutterText(self, value):
        """Set current gutter (line number) style (QTextCharFormat)"""
        if isinstance(value, QTextCharFormat):
            self.__optionGutterText = value
            self.update()

    def optionHighlightedLineColor(self):
        """Return current color for highlighted line"""
        return self.__optionColorHighlightedLine

    def setOptionHighlightedLineColor(self, value):
        """Set current color for highlighted line (QColor)"""
        if isinstance(value, QColor):
            self.__optionColorHighlightedLine = value
            self.__highlightCurrentLine()
            self.update()

    def optionShowLineNumber(self):
        """Return if line numbers are visible or not"""
        return self.__optionShowLineNumber

    def setOptionShowLineNumber(self, value):
        """Set if line numbers are visible or not"""
        if isinstance(value, bool) and value != self.__optionShowLineNumber:
            self.__optionShowLineNumber = value
            if value:
                self.__lineNumberArea = WCELineNumberArea(self)
            else:
                self.__lineNumberArea.disconnect()
                self.__lineNumberArea = None

            self.__updateLineNumberAreaWidth()
            self.update()

    def optionShowIndentLevel(self):
        """Return if indent level are visible or not"""
        return self.__optionShowIndentLevel

    def setOptionShowIndentLevel(self, value):
        """Set if indent level are visible or not"""
        if isinstance(value, bool) and value != self.__optionShowIndentLevel:
            self.__optionShowIndentLevel = value
            self.update()

    def optionIndentWidth(self):
        """Return indent width"""
        return self.__optionIndentWidth

    def setOptionIndentWidth(self, value):
        """Set indent width"""
        if isinstance(value, int) and value != self.__optionIndentWidth and self.__optionIndentWidth > 0:
            self.__optionIndentWidth = value
            self.update()

    def optionShowRightLimit(self):
        """Return if right limit is visible or not"""
        return self.__optionRightLimitVisible

    def setOptionShowRightLimit(self, value):
        """Set if indent level are visible or not"""
        if isinstance(value, bool) and value != self.__optionRightLimitVisible:
            self.__optionRightLimitVisible = value
            self.update()

    def optionRightLimitColor(self):
        """Return right limit color"""
        return self.__optionRightLimitColor

    def setOptionRightLimitColor(self, value):
        """Set right limit color"""
        if isinstance(value, QColor) and value != self.__optionRightLimitColor:
            self.__optionRightLimitColor = value
            self.update()

    def optionRightLimitPosition(self):
        """Return right limit position"""
        return self.__optionRightLimitPosition

    def setOptionRightLimitPosition(self, value):
        """Set right limit position"""
        if isinstance(value, int) and value != self.__optionRightLimitPosition and self.__optionRightLimitPosition > 0:
            self.__optionRightLimitPosition = value
            self.update()

    def optionShowSpaces(self):
        """Return if spaces is visible or not"""
        return self.__optionShowSpaces

    def setOptionShowSpaces(self, value):
        """Set if spaces is visible or not"""
        if isinstance(value, bool) and value != self.__optionShowSpaces:
            self.__optionShowSpaces = value
            self.update()

    def optionSpacesColor(self):
        """Return spaces color"""
        return self.__optionSpacesColor

    def setOptionSpacesColor(self, value):
        """Set spaces color"""
        if isinstance(value, QColor) and value != self.__optionSpacesColor:
            self.__optionSpacesColor = value
            self.update()

    def optionAutoCompletion(self):
        """Return if autoCompletion is manual or automatic"""
        return self.__optionAutoCompletion

    def setOptionAutoCompletion(self, value):
        """Set if autoCompletion is manual or automatic"""
        if isinstance(value, bool) and value != self.__optionAutoCompletion:
            self.__optionAutoCompletion = value
            self.update()

    def optionAutoCompletionHelp(self):
        """Return if help is displayed with auto completion or not"""
        return self.__optionAutoCompletionHelp

    def setOptionAutoCompletionHelp(self, value):
        """Set if help is displayed with auto completion or not"""
        if isinstance(value, bool) and value != self.__optionAutoCompletionHelp:
            self.__optionAutoCompletionHelp = value
            if not self.__optionAutoCompletionHelp:
                self.__hideCompleterHint()

    def optionAutoCompletionMaxItems(self):
        """Return if autoCompletion is manual or automatic"""
        return self.__optionAutoCompletionMaxItems

    def setOptionAutoCompletionMaxItems(self, value):
        """Set if autoCompletion is manual or automatic"""
        if isinstance(value, int) and value != self.__optionAutoCompletionMaxItems and value > 1:
            self.__optionAutoCompletionMaxItems = value
            self.__completer.setMaxVisibleItems(self.__optionAutoCompletionMaxItems)

    def optionAllowWheelSetFontSize(self):
        """Return if CTRL+WHEEL allows to change font size"""
        return self.__optionWheelSetFontSize

    def setOptionAllowWheelSetFontSize(self, value):
        """Set if CTRL+WHEEL allows to change font size"""
        if isinstance(value, bool) and value != self.__optionWheelSetFontSize:
            self.__optionWheelSetFontSize = value

    def setHeight(self, numberOfRows=None):
        """Set height according to given number of rows"""

        if numberOfRows is None:
            self.setminimumHeight(0)
            self.setMaximumHeight(16777215)
        elif isinstance(numberOfRows, int) and numberOfRows > 0:
            if not self.__optionMultiLine:
                numberOfRows = 1

            doc = self.document()
            fontMetrics = QFontMetrics(doc.defaultFont())
            margins = self.contentsMargins()

            self.setFixedHeight(fontMetrics.lineSpacing() * numberOfRows + (doc.documentMargin() + self.frameWidth()) * 2 + margins.top() + margins.bottom())

    def cursorPosition(self, fromZero=False):
        """Return current cursor position information

        Returned row/col start from 1, except if given `fromZero` parameter is True (from 0 in this case)

        Return a tuple:
            QPoint() current position
            QPoint() selection start
            QPoint() selection end
            int      selection length

        """
        # cursor = self.textCursor()
        if fromZero:
            return (QPoint(self.__cursorCol, self.__cursorRow),
                    QPoint(self.__cursorSelColStart-1, self.__cursorSelRowStart-1),
                    QPoint(self.__cursorSelColEnd-1, self.__cursorSelRowEnd-1),
                    self.__cursorSelLen)
        else:
            return (QPoint(self.__cursorCol+1, self.__cursorRow+1),
                    QPoint(self.__cursorSelColStart, self.__cursorSelRowStart),
                    QPoint(self.__cursorSelColEnd, self.__cursorSelRowEnd),
                    self.__cursorSelLen)

    def cursorToken(self, starting=True):
        """Return token currently under cursor

        If cursor is on first character of token, by default return current token
        But if option `starting` is False, in this case consider that we want the previous token

        Note: token position is relative to current line (row position=1, positionStart is relative to start of row)
        """
        if self.__cursorToken:
            if starting is False and self.__cursorToken.column() == (self.__cursorCol+1):
                return self.__cursorToken.previous()

        return self.__cursorToken

    def tokenCursor(self):
        """Return a QTextCursor matching current token on which cursor is"""
        token = self.cursorToken()

        if not isinstance(token, Token):
            return None

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
        if self.__cursorRow > 0:
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, self.__cursorRow)
        if token.column() > 1:
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, token.column()-1)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, token.length())

        return cursor

    def insertLanguageText(self, text, replaceSelection=True):
        """If given text use 'completion' format (ie: use of \x01 character to mark informational values and cursor position), insert it at cursor's place"""
        texts = text.replace(LanguageDef.SEP_SECONDARY_VALUE, '').split(LanguageDef.SEP_PRIMARY_VALUE)[::2]

        cursor = self.textCursor()
        selectedText = cursor.selectedText()

        cursor.insertText(texts[0])

        if not replaceSelection and selectedText != '':
            cursor.insertText(selectedText)

            if len(texts) > 1:
                p = cursor.anchor()
                cursor.insertText("".join(texts[1:]))
                cursor.setPosition(p, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)

    def replaceTokenText(self, text, token=None):
        """Replace given `token` with given `text`

        If no token is provided, replace current token
        """
        if token is None:
            token = self.cursorToken()

        if not isinstance(token, Token):
            raise EInvalidType('Given `token` must be None or a <Token>')

        cursor = self.tokenCursor()
        cursor.insertText(text)

        cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(text))
        self.setTextCursor(cursor)

    def scrollToLine(self, lineNumber, centered=True, nearest=True):
        """Scroll to given `lineNumber`

        If line number is not valid, scroll to top/bottom of document if `nearest` is True
        Otherwise, does nothing
        """
        # first block start to 0, but editor start from 1
        lineNumber -= 1

        if lineNumber < 0:
            if nearest:
                block = self.document().firstBlock()
            else:
                return None
        elif lineNumber >= self.blockCount():
            if nearest:
                block = self.document().lastBlock()
            else:
                return None
        else:
            block = self.document().findBlockByNumber(lineNumber)

        cursor = QTextCursor(block)

        self.setTextCursor(cursor)
        if centered:
            self.centerCursor()
        else:
            self.ensureCursorVisible()

    def selection(self, fromRow, fromCol=None, toRow=None, toCol=None):
        """Convenience method to select text in code editor

        Given `fromRow` is mandatory and must be valid <int> values

        fromRow   fromCol  -  toRow  toCol  -   Result
        -------   -------     -----  -----      -------------------------------------------------------------------------
        <int>     None        None   None       move cursor to start of given `fromRow`
        <int>     <int>       None   None       move cursor to given `fromCol` of `fromRow`
        <int>     None        <int>  None       select rows from `fromRow` to `toRow`
        <int>     <int>       <int>  None       select text from given `fromCol` of `fromRow` to end of `toRow`
        <int>     <int>       <int>  <int>      select text from given `fromCol` of `fromRow` to given `toCol` of `toRow`

        if ` fromRow`/`toRow` is not valid:
        - <0        ==> forced to 0
        - >nbrows   ==> forced to nbrows

        if ` fromCol`/`toCol` is not valid:
        - <0            ==> forced to 0
        - >row length   ==> forced to row length

        return a QTextCursor matching the selection
        """
        pass

    def search(self):
        """Return search object"""
        return self.__search


class WCELineNumberArea(QWidget):
    """Gutter area for line number

    # From example documentation
    We paint the line numbers on this widget, and place it over the WCodeEditor's viewport() 's left margin area.

    We need to use protected functions in QPlainTextEdit while painting the area.
    So to keep things simple, we paint the area in the CodeEditor class.
    The area also asks the editor to calculate its size hint.

    Note that we could simply paint the line numbers directly on the code editor, and drop the WCELineNumberArea class.
    However, the QWidget class helps us to scroll() its contents.
    Also, having a separate widget is the right choice if we wish to extend the editor with breakpoints or other code editor features.
    The widget would then help in the handling of mouse events.
    """

    def __init__(self, codeEditor):
        super(WCELineNumberArea, self).__init__(codeEditor)
        self.__codeEditor = codeEditor

    def sizeHint(self):
        if self.__codeEditor:
            return QSize(self.__codeEditor.lineNumberAreaWidth(), 0)
        return QSize(0, 0)

    def paintEvent(self, event):
        """It Invokes the draw method(lineNumberAreaPaintEvent) in CodeEditor"""
        if self.__codeEditor:
            self.__codeEditor.lineNumberAreaPaintEvent(event)

    def disconnect(self):
        """Disconnect area from editor"""
        self.__codeEditor = None


class WCECompleterModel(QAbstractListModel):
    """Dedicated model used to list completion values"""

    VALUE = Qt.UserRole + 1
    TYPE = Qt.UserRole + 2
    STYLE = Qt.UserRole + 3
    DESCRIPTION = Qt.UserRole + 4
    CHAR = Qt.UserRole + 5

    def __init__(self, parent=None):
        """Initialise list"""
        super().__init__(parent)
        self.__items = []

    def __repr__(self):
        return f'<WCECompleterModel({self.__items})>'

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        row = index.row()
        if role in (WCECompleterModel.VALUE, Qt.DisplayRole):
            return self.__items[row]["value"]
        if role == WCECompleterModel.TYPE:
            return self.__items[row]["type"]
        if role == WCECompleterModel.STYLE:
            return self.__items[row]["style"]
        if role == WCECompleterModel.DESCRIPTION:
            return self.__items[row]["description"]
        if role == WCECompleterModel.CHAR:
            return self.__items[row]["char"]

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows"""
        return len(self.__items)

    def roleNames(self):
        return {
            WCECompleterModel.VALUE: b'value',
            WCECompleterModel.TYPE: b'type',
            WCECompleterModel.STYLE: b'style',
            WCECompleterModel.DESCRIPTION: b'description',
            WCECompleterModel.CHAR: b'char'
        }

    @pyqtSlot(str, int)
    def add(self, value, type, style, description, char):
        """Add an item to model"""
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.__items.append({'value': value, 'type': type, 'style': style, 'description': description, 'char': char})
        self.endInsertRows()

    @pyqtSlot(int, str, int)
    def edit(self, row, value, type, style, description, char):
        """Modify an item from model"""
        ix = self.index(row, 0)
        self.__items[row] = {'value': value, 'type': type, 'style': style, 'description': description, 'char': char}
        self.dataChanged.emit(ix, ix, self.roleNames())

    @pyqtSlot(int)
    def delete(self, row):
        """Remove an item from model"""
        self.beginRemoveColumns(QModelIndex(), row, row)
        del self.__items[row]
        self.endRemoveRows()

    def clear(self):
        """Clear model"""
        self.beginRemoveColumns(QModelIndex(), 0, len(self.__items))
        self.__items = []
        self.endRemoveRows()

    def sort(self):
        """Sort list content"""
        def sortKey(v):
            return f'{v["char"]}-{v["value"].lower()}'
        self.__items.sort(key=sortKey)


class WCECompleterView(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build an improved QCompleter list that
    list completion value with improved style
    """
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(WCECompleterView, self).__init__(parent)

    def paint(self, painter, option, index):
        """Paint list item:
        - completion type ('F'=flow, 'a'=action, 'v'=variable...)
        - completion value, using editor's style
        """
        self.initStyleOption(option, index)

        # retrieve style from token
        style = index.data(WCECompleterModel.STYLE)

        # memorize curent state
        painter.save()
        currentFontName = painter.font().family()
        currentFontSize = painter.font().pointSizeF()
        color = style.foreground().color()

        # -- completion type
        rect = QRect(option.rect.left(), option.rect.top(), 2 * option.rect.height(), option.rect.height())
        if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
            painter.fillRect(rect, QBrush(color.darker(200)))
        else:
            painter.fillRect(rect, QBrush(color.darker(300)))
        font = style.font()
        font.setFamily('DejaVu Sans Mono, Consolas, Courier New')
        font.setBold(True)
        font.setPointSizeF(currentFontSize * 0.65)

        painter.setFont(font)
        painter.setPen(QPen(color.lighter(300)))

        painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, index.data(WCECompleterModel.CHAR))

        # -- completion value
        font = style.font()
        font.setFamily(currentFontName)
        font.setPointSizeF(currentFontSize)

        painter.setFont(font)
        painter.setPen(QPen(color))

        lPosition = option.rect.left() + 2 *  option.rect.height() + 5
        # print(option.state)
        if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
            rect = QRect(option.rect.left() + 2 * option.rect.height(), option.rect.top(), option.rect.width(), option.rect.height())
            painter.fillRect(rect, option.palette.color(QPalette.AlternateBase))

        texts = index.data(WCECompleterModel.VALUE).replace(LanguageDef.SEP_SECONDARY_VALUE, LanguageDef.SEP_PRIMARY_VALUE).split(LanguageDef.SEP_PRIMARY_VALUE)
        for index, text in enumerate(texts):
            if index % 2 == 1:
                # odd text ("optionnal" information) are written smaller, with darker color
                drawingFont = QFont(font)
                drawingFont.setBold(False)
                drawingFont.setItalic(True)
                drawingFont.setPointSizeF(font.pointSizeF()*0.85)
                painter.setOpacity(0.7)
            else:
                drawingFont = font
                painter.setOpacity(1)

            painter.setFont(drawingFont)
            fontMetrics = QFontMetrics(drawingFont)

            rect = QRect(lPosition, option.rect.top(), option.rect.width(), option.rect.height())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, text)

            if text[-1] == ' ':
                lPosition += fontMetrics.horizontalAdvance(text[0:-1]+'_')
            else:
                lPosition += fontMetrics.horizontalAdvance(text)

        painter.restore()

    def sizeHint(self, option, index):
        """Caclulate size for rendered completion item"""
        size = super(WCECompleterView, self).sizeHint(option, index)
        size.setWidth(size.width() + 2 * size.height() + 5)
        return size


class WCESyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter"""

    def __init__(self, parent, languageDef, editor):
        """When subclassing the QSyntaxHighlighter class you must pass the parent parameter to the base class constructor.

        The parent is the text document upon which the syntax highlighting will be applied.

        Given `languageDef` is a LanguageDef object that define language
        """
        super(WCESyntaxHighlighter, self).__init__(parent)

        self.__languageDef = languageDef
        self.__cursorLastToken = None
        self.__cursorToken = None
        self.__editor = editor

    def highlightBlock(self, text):
        """Highlight given text according to the type"""
        if self.__languageDef is None:
            return
        tokens = self.__languageDef.tokenizer().tokenize(text)
        self.__cursorToken = None
        self.__cursorPreviousToken = None

        # determinate if current processed block is current line
        notCurrentLine = (self.currentBlock().firstLineNumber() != self.__editor.textCursor().block().firstLineNumber())

        cursor = self.__editor.textCursor()
        cursorPosition = cursor.selectionEnd()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursorPosition -= cursor.selectionEnd()

        while not (token := tokens.next()) is None:
            if cursorPosition <= token.positionEnd():
                self.__cursorLastToken = token

            if token.isUnknown() and notCurrentLine or not token.isUnknown():
                # highlight unknown token only if leave current line, otherwise apply style
                self.setFormat(token.positionStart(), token.length(), self.__languageDef.style(token))

            if not notCurrentLine and self.__cursorToken is None and cursorPosition >= token.positionStart() and cursorPosition <= token.positionEnd():
                self.__cursorPreviousToken = self.__cursorToken
                self.__cursorToken = token

    def currentCursorToken(self):
        """Return token on which cursor is"""
        return self.__cursorToken

    def lastCursorToken(self):
        """Return last token processed before current token on which cursor is"""
        return self.__cursorLastToken
