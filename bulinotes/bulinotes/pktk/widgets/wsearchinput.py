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

import html
import re

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )


from ..modules.utils import replaceLineEditClearButton
from ..modules.imgutils import buildIcon
from .wseparator import WVLine


class SearchOptions:
    REGEX =               0b0000000000000001
    CASESENSITIVE =       0b0000000000000010
    WHOLEWORD =           0b0000000000000100
    BACKWARD =            0b0000000000001000
    HIGHLIGHT =           0b0000000000010000


class WSearchInput(QWidget):
    """A LineEdit combined with some buttons to provide a ready-to-use search bar tool

    If not OPTION_SHOW_REPLACE set:
        -> OPTION_SHOW_BUTTON_ALL is ignored (search/replace all buttons are not available)

        +-----------------------------------------------------------------------  search text entry
        |
        |                             +-----------------------------------------  OPTION_SHOW_BUTTON_SEARCH
        |                             |
        |                             |     +-----------------------------------  OPTION_SHOW_BUTTON_REGEX
        |                             |     |
        |                             |     |     +-----------------------------  OPTION_SHOW_BUTTON_CASESENSITIVE
        |                             |     |     |
        |                             |     |     |     +-----------------------  OPTION_SHOW_BUTTON_WHOLEWORD
        |                             |     |     |     |
        |                             |     |     |     |     +-----------------  OPTION_SHOW_BUTTON_BACKWARD
        |                             |     |     |     |     |
        |                             |     |     |     |     |     +-----------  OPTION_SHOW_BUTTON_HIGHLIGHTALL
        |                             |     |     |     |     |     |
        |                             |     |     |     |     |     |     +-----  OPTION_SHOW_BUTTON_SHOWHIDE
        |                             |     |     |     |     |     |     |
        |                             |     |     |     |     |     |     |
        V                             V     V     V     V     V     V     V
    +-----------------------------+ +---+ +---+ +---+ +---+ +---+ +---+ +---+
    | xxxx                        | |   | |   | |   | |   | |   | |   | |   |
    +-----------------------------+ +---+ +---+ +---+ +---+ +---+ +---+ +---+

                                    \_________________________________/
                                                     |
                                                     +--------------------------  Buttons visibles according to OPTION_STATE_BUTTONSHOW value



    If OPTION_SHOW_REPLACE set:
        -> OPTION_SHOW_BUTTON_SEARCH is ignored (search/replace buttons are always visible)
        -> OPTION_SHOW_BUTTON_SHOWHIDE & OPTION_STATE_BUTTONSHOW are ignored (option buttons are always visible)


        +---------------------------------------------------------------------------  search text entry
        |
        |      +---------------------+----------------------------------------------  information about current search
        |      |                     |
        |      |                     |            +---------------------------------  OPTION_SHOW_BUTTON_REGEX
        |      |                     |            |
        |      |                     |            |     +---------------------------  OPTION_SHOW_BUTTON_CASESENSITIVE
        |      |                     |            |     |
        |      |                     |            |     |     +---------------------  OPTION_SHOW_BUTTON_WHOLEWORD
        |      |                     |            |     |     |
        |      |                     |            |     |     |     +---------------  OPTION_SHOW_BUTTON_BACKWARD
        |      |                     |            |     |     |     |
        |      |                     |            |     |     |     |     +---------  OPTION_SHOW_BUTTON_HIGHLIGHTALL
        |      |                     |            |     |     |     |     |
        |      |                     |            |     |     |     |     |
        |      |                     |            |     |     |     |     |
        |      |                     |            |     |     |     |     |
        |      V                     V            V     V     V     V     V
        |                                       +---+ +---+ +---+ +---+ +---+
        |  xxxxxxxxxxx         xxxxxxxxxxxxxx   |   | |   | |   | |   | |   |
        V                                       +---+ +---+ +---+ +---+ +---+
    +-----------------------------------------------+ +---------+ +---------+
    | xxxx                                          | | Search  | | S.All   |<-+----  OPTION_SHOW_BUTTON_ALL
    +-----------------------------------------------+ +---------+ +---------+  |
    +-----------------------------------------------+ +---------+ +---------+  |
    | xxxx                                          | | Replace | | R.All   |<-/
    +-----------------------------------------------+ +---------+ +---------+
        ^
        |
        +---------------------------------------------------------------------------  replace text entry


    """
    searchOptionModified = Signal(str, int)         # when at least one search option has been modified value has been modified
    searchActivated = Signal(str, int, bool)        # when RETURN key has been pressed
    searchModified = Signal(str, int)               # when search value has been modified
    replaceActivated = Signal(str, str, int, bool)  # when RETURN key has been pressed
    replaceModified = Signal(str, str, int)         # when replace value has been modified

    # reserved                          0b000000000000000000000000000XXXXX

    OPTION_SHOW_BUTTON_SEARCH =         0b00000000000000000000000100000000  # display SEARCH button                     ==> taken in account without OPTION_SHOW_REPLACE option only (OPTION_SHOW_REPLACE implies SEARCH button)
    OPTION_SHOW_BUTTON_REGEX =          0b00000000000000000000001000000000  # display REGULAR EXPRESSION option button
    OPTION_SHOW_BUTTON_CASESENSITIVE =  0b00000000000000000000010000000000  # display CASE SENSITIVE option button
    OPTION_SHOW_BUTTON_WHOLEWORD =      0b00000000000000000000100000000000  # display WHOLE WORD option button
    OPTION_SHOW_BUTTON_BACKWARD =       0b00000000000000000001000000000000  # display BACKWARD option button
    OPTION_SHOW_BUTTON_HIGHLIGHTALL =   0b00000000000000000010000000000000  # display HIGHLIGHT ALL option button
    OPTION_SHOW_BUTTON_SHOWHIDE =       0b00000000000000000100000000000000  # display SHOW/HIDE OPTIONS button          ==> taken in account without OPTION_SHOW_REPLACE option only
    OPTION_SHOW_BUTTON_ALL =            0b00000000000000001000000000000000  # display SEARCH ALL/REPLACE ALL buttons    ==> taken in account with OPTION_SHOW_REPLACE option only

    OPTION_SHOW_REPLACE =               0b00000000000000010000000000000000  # display REPLACE text entry and button

    OPTION_STATE_BUTTONSHOW =           0b10000000000000000000000000000000  # without OPTION_SHOW_REPLACE option only

    OPTION_ALL_BUTTONS =                0b00000000000000001111111100000000
    OPTION_ALL_SEARCH =                 0b00000000000000000000000000011111
    OPTION_ALL =                        0b10000000000000011111111100011111

    def __init__(self, options=None, parent=None):
        super(WSearchInput, self).__init__(parent)

        font=self.font()
        font.setStyleHint(QFont.Monospace)
        font.setFamily("Monospace")

        # entries
        self.__leSearch=QLineEdit()
        self.__leSearch.returnPressed.connect(self.applySearch)
        self.__leSearch.textChanged.connect(self. __searchTextModified)
        self.__leSearch.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.__leSearch.setClearButtonEnabled(True)
        replaceLineEditClearButton(self.__leSearch)
        self.__leSearch.setFont(font)


        self.__leReplace=QLineEdit()
        self.__leReplace.returnPressed.connect(self.applyReplace)
        self.__leReplace.textChanged.connect(self. __replaceTextModified)
        self.__leReplace.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.__leReplace.setClearButtonEnabled(True)
        replaceLineEditClearButton(self.__leReplace)
        self.__leReplace.setFont(font)

        # buttons
        self.__btSearch=QToolButton()
        self.__btSearch.setAutoRaise(True)
        self.__btSearch.setToolTip(i18n('Search'))
        self.__btSearch.setIcon(buildIcon("pktk:search"))

        self.__btSRSearch=QPushButton(i18n('Search'))
        self.__btSRSearch.setToolTip(i18n('Search next occurence'))

        self.__btSRSearchAll=QPushButton(i18n('Search All'))
        self.__btSRSearchAll.setToolTip(i18n('Search all occurences'))

        self.__btSRReplace=QPushButton(i18n('Replace'))
        self.__btSRReplace.setToolTip(i18n('Replace next occurence'))
        self.__btSRReplaceAll=QPushButton(i18n('Replace All'))
        self.__btSRReplaceAll.setToolTip(i18n('Replace all occurences'))

        # options button
        self.__vlN1=WVLine()
        self.__vlN2=WVLine()

        self.__btRegEx=QToolButton()
        self.__btCaseSensitive=QToolButton()
        self.__btWholeWord=QToolButton()
        self.__btBackward=QToolButton()
        self.__btHighlightAll=QToolButton()

        self.__btRegEx.setAutoRaise(True)
        self.__btCaseSensitive.setAutoRaise(True)
        self.__btWholeWord.setAutoRaise(True)
        self.__btBackward.setAutoRaise(True)
        self.__btHighlightAll.setAutoRaise(True)

        self.__btRegEx.setCheckable(True)
        self.__btCaseSensitive.setCheckable(True)
        self.__btWholeWord.setCheckable(True)
        self.__btBackward.setCheckable(True)
        self.__btHighlightAll.setCheckable(True)

        self.__btRegEx.setToolTip(i18n('Search from regular expression'))
        self.__btCaseSensitive.setToolTip(i18n('Search with case sensitive'))
        self.__btWholeWord.setToolTip(i18n('Search for whole words only'))
        self.__btBackward.setToolTip(i18n('Search in backward direction'))
        self.__btHighlightAll.setToolTip(i18n('Highlight all occurences found'))

        self.__btRegEx.setIcon(buildIcon("pktk:filter_regex"))
        self.__btCaseSensitive.setIcon(buildIcon("pktk:filter_case"))
        self.__btWholeWord.setIcon(buildIcon("pktk:filter_wholeword"))
        self.__btBackward.setIcon(buildIcon("pktk:filter_backward"))
        self.__btHighlightAll.setIcon(buildIcon("pktk:filter_highlightall"))

        self.__wOptionButtons=QWidget()
        self.__lOptionButtons=QHBoxLayout()
        self.__lOptionButtons.addWidget(self.__vlN1)
        self.__lOptionButtons.addWidget(self.__btRegEx)
        self.__lOptionButtons.addWidget(self.__btCaseSensitive)
        self.__lOptionButtons.addWidget(self.__btWholeWord)
        self.__lOptionButtons.addWidget(self.__btBackward)
        self.__lOptionButtons.addWidget(self.__btHighlightAll)
        self.__lOptionButtons.addWidget(self.__vlN2)

        self.__lOptionButtons.setContentsMargins(0, 0, 0, 0)
        self.__lOptionButtons.setSpacing(3)

        self.__wOptionButtons.setLayout(self.__lOptionButtons)

        self.__btShowHide=QToolButton()
        self.__btShowHide.setAutoRaise(True)
        self.__btShowHide.setCheckable(True)
        self.__btShowHide.setToolTip(i18n('Show/Hide search options'))
        self.__btShowHide.setIcon(buildIcon("pktk:tune"))


        # informations
        font=self.font()
        font.setPointSizeF(font.pointSizeF()*0.9)

        self.__foundResultsInfo=QLabel()
        self.__foundResultsInfo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.__foundResultsInfo.setFont(font)

        self.__optionsInfo=QLabel()
        self.__optionsInfo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__optionsInfo.setFont(font)

        self.__wSRInfo=QWidget()
        self.__lSRInfo=QHBoxLayout()
        self.__lSRInfo.addWidget(self.__foundResultsInfo)
        self.__lSRInfo.addWidget(self.__optionsInfo)
        self.__lSRInfo.addWidget(self.__wOptionButtons)

        self.__lSRInfo.setContentsMargins(0, 0, 0, 0)
        self.__lSRInfo.setSpacing(3)

        self.__wSRInfo.setLayout(self.__lSRInfo)


        # manage signals
        self.__btSRSearch.clicked.connect(self.applySearch)
        self.__btSRSearchAll.clicked.connect(self.applySearchAll)
        self.__btSRReplace.clicked.connect(self.applyReplace)
        self.__btSRReplaceAll.clicked.connect(self.applyReplaceAll)

        self.__btSearch.clicked.connect(self.applySearch)

        self.__btRegEx.toggled.connect(self.__searchOptionChanged)
        self.__btCaseSensitive.toggled.connect(self.__searchOptionChanged)
        self.__btWholeWord.toggled.connect(self.__searchOptionChanged)
        self.__btBackward.toggled.connect(self.__searchOptionChanged)
        self.__btHighlightAll.toggled.connect(self.__searchOptionChanged)
        self.__btShowHide.toggled.connect(self.__updateInterface)

        # layout option Search
        self.__layout=None
        self.__currentLayoutId=None

        self.__options=0
        if options is None:
            options=WSearchInput.OPTION_ALL_BUTTONS|WSearchInput.OPTION_STATE_BUTTONSHOW

        self.__btShowHide.setChecked(self.__options&WSearchInput.OPTION_STATE_BUTTONSHOW==WSearchInput.OPTION_STATE_BUTTONSHOW)
        self.setOptions(options)


    def __updateInterface(self, visible=None):
        """Update user interface"""
        # search option group is not empty if at least one button is defined as available in options
        groupNotEmpty=(WSearchInput.OPTION_SHOW_BUTTON_REGEX|
                       WSearchInput.OPTION_SHOW_BUTTON_CASESENSITIVE|
                       WSearchInput.OPTION_SHOW_BUTTON_WHOLEWORD|
                       WSearchInput.OPTION_SHOW_BUTTON_BACKWARD|
                       WSearchInput.OPTION_SHOW_BUTTON_HIGHLIGHTALL)!=0

        #search option group buttons are visible if button is defined as available in options
        self.__btRegEx.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_REGEX==WSearchInput.OPTION_SHOW_BUTTON_REGEX)
        self.__btCaseSensitive.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_CASESENSITIVE==WSearchInput.OPTION_SHOW_BUTTON_CASESENSITIVE)
        self.__btWholeWord.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_WHOLEWORD==WSearchInput.OPTION_SHOW_BUTTON_WHOLEWORD)
        self.__btBackward.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_BACKWARD==WSearchInput.OPTION_SHOW_BUTTON_BACKWARD)
        self.__btHighlightAll.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_HIGHLIGHTALL==WSearchInput.OPTION_SHOW_BUTTON_HIGHLIGHTALL)

        self.__btRegEx.setChecked(self.__options&SearchOptions.REGEX==SearchOptions.REGEX)
        self.__btCaseSensitive.setChecked(self.__options&SearchOptions.CASESENSITIVE==SearchOptions.CASESENSITIVE)
        self.__btWholeWord.setChecked(self.__options&SearchOptions.WHOLEWORD==SearchOptions.WHOLEWORD)
        self.__btBackward.setChecked(self.__options&SearchOptions.BACKWARD==SearchOptions.BACKWARD)
        self.__btHighlightAll.setChecked(self.__options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT)


        if self.__options&WSearchInput.OPTION_SHOW_REPLACE==WSearchInput.OPTION_SHOW_REPLACE:
            # search and replace UI
            self.__vlN1.setVisible(False)
            self.__vlN2.setVisible(False)

            self.__btSearch.setVisible(False)
            self.__btShowHide.setVisible(False)

            # search option group is visible if not empty
            self.__wOptionButtons.setVisible(groupNotEmpty)
        else:
            # search only UI
            self.__vlN1.setVisible(True)
            self.__vlN2.setVisible(True)

            self.__btSearch.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_SEARCH==WSearchInput.OPTION_SHOW_BUTTON_SEARCH)
            self.__btShowHide.setVisible(self.__options&WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE==WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE)

            if visible is None:
                # use value from __options (called from setOption() method)
                self.__btShowHide.setChecked(self.__options&WSearchInput.OPTION_STATE_BUTTONSHOW==WSearchInput.OPTION_STATE_BUTTONSHOW)
            else:
                # use value from parameter visible (called from signal emitted when button is toggled)
                self.__btShowHide.setChecked(visible)

            # search option group is visible if not empty AND:
            # - button show/hide is not visible
            # OR
            # - button show/hide is visible AND checked
            self.__wOptionButtons.setVisible(groupNotEmpty and ((not (self.__options&WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE==WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE)) or self.__btShowHide.isChecked()))


    def __searchOptionChanged(self):
        """Search option has been changed, emit signal"""
        self.searchOptionModified.emit(self.__leSearch.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH)

        if self.__currentLayoutId==WSearchInput.OPTION_SHOW_REPLACE:
            optionsInfo=[]

            if self.__options&SearchOptions.REGEX==SearchOptions.REGEX:
                optionsInfo.append(i18n('Regular expression'))

            if self.__options&SearchOptions.CASESENSITIVE==SearchOptions.CASESENSITIVE:
                optionsInfo.append(i18n('Case sensitive'))
            else:
                optionsInfo.append(i18n('Case insensitive'))

            if self.__options&SearchOptions.WHOLEWORD==SearchOptions.WHOLEWORD:
                optionsInfo.append(i18n('Whole words'))

            if self.__options&SearchOptions.BACKWARD==SearchOptions.BACKWARD:
                optionsInfo.append(i18n('Backward direction'))

            if self.__options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT:
                optionsInfo.append(i18n('Highlight all found occurences'))

            self.__optionsInfo.setText(i18n('Finding with options: <i>')+', '.join(optionsInfo)+'</i>')


    def __searchTextModified(self):
        """Search value has been modified, emit signal"""
        self.searchModified.emit(self.__leSearch.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH)


    def __replaceTextModified(self):
        """Replace value has been modified, emit signal"""
        self.replaceModified.emit(self.__leSearch.text(), self.__leReplace.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH)


    def options(self):
        """Return current options flags"""
        currentSearch=0
        if self.__btRegEx.isChecked():
            currentSearch|=SearchOptions.REGEX

        if self.__btCaseSensitive.isChecked():
            currentSearch|=SearchOptions.CASESENSITIVE

        if self.__btWholeWord.isChecked():
            currentSearch|=SearchOptions.WHOLEWORD

        if self.__btBackward.isChecked():
            currentSearch|=SearchOptions.BACKWARD

        if self.__btHighlightAll.isChecked():
            currentSearch|=SearchOptions.HIGHLIGHT

        if self.__btShowHide.isChecked() or (self.__options&WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE!=WSearchInput.OPTION_SHOW_BUTTON_SHOWHIDE):
            currentSearch|=WSearchInput.OPTION_STATE_BUTTONSHOW

        self.__options=(self.__options&(WSearchInput.OPTION_ALL_BUTTONS|WSearchInput.OPTION_SHOW_REPLACE))|currentSearch

        return self.__options


    def setOptions(self, options):
        """Set current options flags"""
        if isinstance(options, int):
            self.__options=options&WSearchInput.OPTION_ALL

            if self.__currentLayoutId!=(self.__options&WSearchInput.OPTION_SHOW_REPLACE):
                self.__currentLayoutId=self.__options&WSearchInput.OPTION_SHOW_REPLACE
                if self.__layout:
                    while self.__layout.count():
                        item=self.__layout.takeAt(0)
                        widget=item.widget()
                        if widget is not None:
                            widget.setParent(None)

                    del self.__layout
                    self.__layout=None

                if self.__currentLayoutId==WSearchInput.OPTION_SHOW_REPLACE:
                    self.__layout=QGridLayout()
                    self.__layout.addWidget(self.__wSRInfo, 0, 0, 1, -1)
                    self.__layout.addWidget(self.__leSearch, 1, 0)
                    self.__layout.addWidget(self.__btSRSearch, 1, 1)
                    self.__layout.addWidget(self.__btSRSearchAll, 1, 2)
                    self.__layout.addWidget(self.__leReplace, 2, 0)
                    self.__layout.addWidget(self.__btSRReplace, 2, 1)
                    self.__layout.addWidget(self.__btSRReplaceAll, 2, 2)
                    self.__layout.setColumnStretch(0, 8)
                    self.__layout.setColumnStretch(1, 1)
                    self.__layout.setColumnStretch(2, 1)
                    self.__layout.setSpacing(4)
                else:
                    self.__layout=QHBoxLayout()
                    self.__layout.addWidget(self.__leSearch)
                    self.__layout.addWidget(self.__btSearch)
                    self.__layout.addWidget(self.__wOptionButtons)
                    self.__layout.addWidget(self.__btShowHide)
                    self.__layout.setSpacing(3)

                self.__layout.setContentsMargins(0, 0, 0, 0)

                self.setLayout(self.__layout)

            self.__updateInterface()


    def applySearch(self):
        """Search button clicked or Return key pressed, emit signal"""
        self.searchActivated.emit(self.__leSearch.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH, False)


    def applyReplace(self):
        """Replace button clicked or Return key pressed, emit signal"""
        self.replaceActivated.emit(self.__leSearch.text(), self.__leReplace.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH, False)


    def applySearchAll(self):
        """Search All button clicked or Return key pressed, emit signal"""
        self.searchActivated.emit(self.__leSearch.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH, True)


    def applyReplaceAll(self):
        """Replace All button clicked or Return key pressed, emit signal"""
        self.replaceActivated.emit(self.__leSearch.text(), self.__leReplace.text(), self.options()&WSearchInput.OPTION_ALL_SEARCH, True)


    def searchText(self):
        """Return current search text"""
        return self.__leSearch.text()


    def setSearchText(self, text):
        """Set current search text"""
        self.__leSearch.setText(text)


    def replaceText(self):
        """Return current replace text"""
        return self.__leReplace.text()


    def setReplaceText(self, text):
        """Set current replace text"""
        self.__leReplace.setText(text)

    def setResultsInformation(self, text):
        self.__foundResultsInfo.setText(text)


class SearchFromPlainTextEdit:
    """Provide high level method to search ocurences in a QPlainTextEdit"""

    COLOR_SEARCH_ALL = 0
    COLOR_SEARCH_CURRENT_BG = 'highlightSearchCurrent.bg'
    COLOR_SEARCH_CURRENT_FG = 'highlightSearchCurrent.fg'

    def __init__(self, plainTextEdit):
        if not isinstance(plainTextEdit, QPlainTextEdit):
            raise EInvalidType("Given `plainTextEdit` must be a <QPlainTextEdit>")

        self.__plainTextEdit=plainTextEdit

        # search results
        self.__extraSelectionsFoundAll=[]
        self.__extraSelectionsFoundCurrent=None
        self.__lastFound=None

        self.__searchColors={
                SearchFromPlainTextEdit.COLOR_SEARCH_ALL:           QColor("#77ffc706"),
                SearchFromPlainTextEdit.COLOR_SEARCH_CURRENT_BG:    QColor("#9900b86f"),
                SearchFromPlainTextEdit.COLOR_SEARCH_CURRENT_FG:    QColor("#ffff00")
            }


    def __highlightedSelections(self):
        """Build extra selection for highlighting"""
        foundCurrentAdded=False
        if self.__extraSelectionsFoundCurrent is None:
            returned=self.__extraSelectionsFoundAll
        else:
            returned=[]
            for cursorFromAll in self.__extraSelectionsFoundAll:
                if cursorFromAll.cursor==self.__extraSelectionsFoundCurrent.cursor:
                    returned.append(self.__extraSelectionsFoundCurrent)
                    foundCurrentAdded=True
                else:
                    returned.append(cursorFromAll)

        if not foundCurrentAdded and not self.__extraSelectionsFoundCurrent is None:
            returned.append(self.__extraSelectionsFoundCurrent)

        return returned

    def clearCurrent(self):
        """Clear current found selection"""
        if self.__extraSelectionsFoundCurrent:
            extraSelections=self.__plainTextEdit.extraSelections()
            for extraSelection in extraSelections:
                if extraSelection.format.boolProperty(0x01):
                    extraSelections.remove(extraSelection)
                    break
            self.__extraSelectionsFoundCurrent=None


    def searchAll(self, text, options=0):
        """Search all occurences of `text` in console

        If `text` is None or empty string, and option SEARCH_OPTION_HIGHLIGHT is set,
        it will clear all current selected items

        Options is combination of SearchOptions flags:
            HIGHLIGHT =       highlight the found occurences in console
            REGEX =           consider text as a regular expression
            WHOLEWORD =       search for while words only
            CASESENSITIVE =   search with case sensitive

        Return list of cursors
        """
        extraSelectionsFoundAll=[]

        if (text is None or text=='') and options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT:
            # clear current selections
            self.__extraSelectionsFoundAll=[]
            self.__plainTextEdit.setExtraSelections(self.__highlightedSelections())
            return self.__extraSelectionsFoundAll

        findFlags=0
        if options&SearchOptions.WHOLEWORD==SearchOptions.WHOLEWORD:
            findFlags|=QTextDocument.FindWholeWords
        if options&SearchOptions.CASESENSITIVE==SearchOptions.CASESENSITIVE:
            findFlags|=QTextDocument.FindCaseSensitively
        if options&SearchOptions.REGEX==SearchOptions.REGEX:
            text=QRegularExpression(text)


        cursor=self.__plainTextEdit.document().find(text, 0, QTextDocument.FindFlags(findFlags))
        while cursor.position()>0:
            extraSelection=QTextEdit.ExtraSelection()

            extraSelection.cursor=cursor
            extraSelection.format.setBackground(QBrush(self.__searchColors[SearchFromPlainTextEdit.COLOR_SEARCH_ALL]))

            extraSelectionsFoundAll.append(extraSelection)
            cursor=self.__plainTextEdit.document().find(text, cursor, QTextDocument.FindFlags(findFlags))

        if options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT:
            self.__extraSelectionsFoundAll=extraSelectionsFoundAll
        else:
            self.__extraSelectionsFoundAll=[]

        self.__plainTextEdit.setExtraSelections(self.__highlightedSelections())

        return extraSelectionsFoundAll


    def searchNext(self, text, options=0, fromCursor=None):
        """Search for next occurence of `text`

        If `text` is None or empty string, and option SEARCH_OPTION_HIGHLIGHT is set,
        it will clear all current selected items

        Options is combination of SearchOptions flags:
            HIGHLIGHT =       highlight the found occurences in editor
            REGEX =           consider text as a regular expression
            WHOLEWORD =       search for while words only
            CASESENSITIVE =   search with case sensitive
            BACKWARD =        search in backward direction, otherwise search in forward direction

        Return a cursor or None
        """
        if (text is None or text=='') and options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT:
            self.__extraSelectionsFoundCurrent=None
            self.__plainTextEdit.setExtraSelections(self.__highlightedSelections())
            return self.__extraSelectionsFoundCurrent

        findFlags=0
        if options&SearchOptions.WHOLEWORD==SearchOptions.WHOLEWORD:
            findFlags|=QTextDocument.FindWholeWords
        if options&SearchOptions.CASESENSITIVE==SearchOptions.CASESENSITIVE:
            findFlags|=QTextDocument.FindCaseSensitively
        if options&SearchOptions.BACKWARD==SearchOptions.BACKWARD:
            findFlags|=QTextDocument.FindBackward

        if options&SearchOptions.REGEX==SearchOptions.REGEX:
            text=QRegularExpression(text)

        if not isinstance(fromCursor, (int, QTextCursor)):
            if self.__extraSelectionsFoundCurrent is None:
                cursor=self.__plainTextEdit.textCursor().position()
            else:
                cursor=self.__extraSelectionsFoundCurrent.cursor
        else:
            cursor=fromCursor

        found=self.__plainTextEdit.document().find(text, cursor, QTextDocument.FindFlags(findFlags))
        loopNumber=0
        while loopNumber<=1:
            # check found occurence
            if found is None or found.position()==-1:
                loopNumber+=1

                # nothing found: may be we need to loop
                if options&SearchOptions.BACKWARD==SearchOptions.BACKWARD:
                    cursor=self.__plainTextEdit.document().characterCount()
                else:
                    cursor=0

                found=self.__plainTextEdit.document().find(text, cursor, QTextDocument.FindFlags(findFlags))

                if not found is None and found.position()==-1:
                    found=None


            if found and not found.block().isVisible():
                # something found, but not visible
                found=self.__plainTextEdit.document().find(text, found, QTextDocument.FindFlags(findFlags))
            elif found:
                break

        if options&SearchOptions.HIGHLIGHT==SearchOptions.HIGHLIGHT and not found is None:
            self.__extraSelectionsFoundCurrent=QTextEdit.ExtraSelection()
            self.__extraSelectionsFoundCurrent.format.setBackground(QBrush(self.__searchColors[SearchFromPlainTextEdit.COLOR_SEARCH_CURRENT_BG]))
            self.__extraSelectionsFoundCurrent.format.setForeground(QBrush(self.__searchColors[SearchFromPlainTextEdit.COLOR_SEARCH_CURRENT_FG]))
            self.__extraSelectionsFoundCurrent.format.setProperty(0x01, True)
            self.__extraSelectionsFoundCurrent.cursor=found
        else:
            self.__extraSelectionsFoundCurrent=None

        self.__plainTextEdit.setExtraSelections(self.__highlightedSelections())

        if not self.__extraSelectionsFoundCurrent is None:
            cursor=QTextCursor(self.__extraSelectionsFoundCurrent.cursor)
            cursor.clearSelection()
            self.__plainTextEdit.setTextCursor(cursor)
            self.__plainTextEdit.centerCursor()

        return found


    def replaceNext(self, searchText, replaceText, options=0):
        """Search for next occurence of `searchText` and replace it with `replaceText`

        If `searchText` is None or empty string, does nothing

        Options is combination of SearchOptions flags:
            HIGHLIGHT =       highlight the found occurences in console
            REGEX =           consider text as a regular expression
            WHOLEWORD =       search for while words only
            CASESENSITIVE =   search with case sensitive
            BACKWARD =        search in backward direction, otherwise search in forward direction

        Return True if something has been replaced, otherwise False
        """
        if self.__extraSelectionsFoundCurrent is None:
            self.searchNext(searchText, options)

        if self.__extraSelectionsFoundCurrent is None:
            # nothing to change
            return False

        cursor=self.__extraSelectionsFoundCurrent.cursor


        text=cursor.block().text()

        selStart=cursor.selectionStart()-cursor.block().position()
        selEnd=cursor.selectionEnd()-cursor.block().position()

        replaceRegEx=options&SearchOptions.REGEX==SearchOptions.REGEX
        replaceWithValue=replaceText

        if replaceRegEx:
            if reResult:=re.search(searchText, text[selStart:selEnd]):
                for index, replace in enumerate(reResult.groups()):
                    replaceWithValue=replaceWithValue.replace(f'${index+1}', replace)

        cursor.insertText(replaceWithValue)
        self.searchNext(searchText, options)
        return True


    def replaceAll(self, searchText, replaceText, options=0):
        """Search all occurences of `searchText` and replace it with `replaceText`

        If `searchText` is None or empty string, does nothing

        Options is combination of SearchOptions flags:
            HIGHLIGHT =       highlight the found occurences in console
            REGEX =           consider text as a regular expression
            WHOLEWORD =       search for while words only
            CASESENSITIVE =   search with case sensitive
            BACKWARD =        search in backward direction, otherwise search in forward direction

        return number of occurences replaced
        """
        cursor=self.__plainTextEdit.textCursor()
        returned=0
        found=self.searchNext(searchText, options&(WSearchInput.OPTION_ALL^SearchOptions.HIGHLIGHT), 0)

        if found is None:
            # nothing to change
            return returned

        replaceRegEx=options&SearchOptions.REGEX==SearchOptions.REGEX
        found.beginEditBlock()
        lastPosition=found.selectionEnd()
        while True:
            text=found.block().text()

            selStart=found.selectionStart()-found.block().position()
            selEnd=found.selectionEnd()-found.block().position()

            replaceWithValue=replaceText

            if replaceRegEx:
                if reResult:=re.search(searchText, text[selStart:selEnd]):
                    for index, replace in enumerate(reResult.groups()):
                        replaceWithValue=replaceWithValue.replace(f'${index+1}', replace)

            found.insertText(replaceWithValue)
            returned+=1
            lastPosition=found.selectionEnd()

            nextFound=self.searchNext(searchText, options&(WSearchInput.OPTION_ALL^SearchOptions.HIGHLIGHT), lastPosition)
            if nextFound is None or nextFound.position()<=lastPosition:
                # none found, or restarted from start of document
                break

            found.setPosition(nextFound.selectionStart(), QTextCursor.MoveAnchor)
            found.setPosition(nextFound.selectionEnd(), QTextCursor.KeepAnchor)



        found.endEditBlock()
        self.__plainTextEdit.setTextCursor(cursor)
        return returned
