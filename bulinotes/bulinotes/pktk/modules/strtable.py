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
# String utility: tables
# -----------------------------------------------------------------------------

import os
import re

from .strutils import strToMaxLength
from ..pktk import *



class TextTableSettingsText(object):
    """Define settings to render a table"""
    MIN_WIDTH = 1
    MAX_WIDTH = 512

    BORDER_NONE = 0
    BORDER_BASIC = 1
    BORDER_SIMPLE = 2
    BORDER_DOUBLE = 3

    def __init__(self):
        self.__border = TextTableSettingsText.BORDER_DOUBLE
        self.__headerActive = True
        self.__minWidthActive = True
        self.__minWidthValue = 80
        self.__maxWidthActive = False
        self.__maxWidthValue = 120

        self.__columnsAlignment = []

    def border(self):
        return self.__border

    def setBorder(self, border):
        if border in [TextTableSettingsText.BORDER_NONE,
                      TextTableSettingsText.BORDER_BASIC,
                      TextTableSettingsText.BORDER_SIMPLE,
                      TextTableSettingsText.BORDER_DOUBLE]:
            self.__border = border

    def headerActive(self):
        return self.__headerActive

    def setHeaderActive(self, headerActive):
        if isinstance(headerActive, bool):
            self.__headerActive = headerActive

    def minWidthActive(self):
        return self.__minWidthActive

    def setMinWidthActive(self, minWidthActive):
        if isinstance(minWidthActive, bool):
            self.__minWidthActive = minWidthActive

    def maxWidthActive(self):
        return self.__maxWidthActive

    def setMaxWidthActive(self, maxWidthActive):
        if isinstance(maxWidthActive, bool):
            self.__maxWidthActive = maxWidthActive

    def minWidth(self):
        return self.__minWidthValue

    def setMinWidth(self, minWidth):
        if isinstance(minWidth, int) and minWidth >= TextTableSettingsText.MIN_WIDTH and minWidth <= TextTableSettingsText.MAX_WIDTH:
            self.__minWidthValue = minWidth

    def maxWidth(self):
        return self.__maxWidthValue

    def setMaxWidth(self, maxWidth):
        if isinstance(maxWidth, int) and maxWidth >= TextTableSettingsText.MIN_WIDTH and maxWidth <= TextTableSettingsText.MAX_WIDTH:
            self.__maxWidthValue = maxWidth

    def columnAlignment(self, columnIndex):
        if columnIndex < len(self.__columnsAlignment):
            return self.__columnsAlignment[columnIndex]
        else:
            # by default return LEFT aligment (0)
            return 0

    def columnsAlignment(self):
        return self.__columnsAlignment

    def setColumnsAlignment(self, alignments):
        self.__columnsAlignment = alignments


class TextTableSettingsTextCsv(object):
    """Define settings to render a table as CSV"""

    def __init__(self):
        self.__border = TextTableSettingsText.BORDER_DOUBLE
        self.__headerActive = True
        self.__enclosedField = False
        self.__separator = ','

    def separator(self):
        return self.__separator

    def setSeparator(self, separator):
        self.__separator = separator

    def headerActive(self):
        return self.__headerActive

    def setHeaderActive(self, headerActive):
        if isinstance(headerActive, bool):
            self.__headerActive = headerActive

    def enclosedField(self):
        return self.__enclosedField

    def setEnclosedField(self, enclosedField):
        if isinstance(enclosedField, bool):
            self.__enclosedField = enclosedField


class TextTableSettingsTextMarkdown(object):
    """Define settings to render a table in mardkown"""

    def __init__(self):
        self.__columnsFormatting = []

    def columnFormatting(self, columnIndex):
        if columnIndex < len(self.__columnsFormatting):
            return self.__columnsFormatting[columnIndex]
        else:
            # by default return LEFT aligment (0)
            return None

    def columnsFormatting(self):
        return self.__columnsFormatting

    def setColumnsFormatting(self, formatting):
        """Set column content formatting

        Given `formatting` is a list tuple or None

        Each tuple item is a markup '{text}' formatted in markdown

        Example:
            Format in italic+bold
                setColumnsFormatting( ('*{text}*', '**{text}**') )

            Format in code
                setColumnsFormatting( ('`{text}`', ) )
        """

        if not(isinstance(formatting, list) or formatting is None):
            raise EInvalidType("Given `formatting` must be a <tuple>")

        self.__columnsFormatting = formatting


class TextTableSettingsTextHtml(object):
    """Define settings to render a table as HTML"""

    def __init__(self):
        self.__style = ''

    def style(self):
        return self.__style

    def setStyle(self, style):
        if isinstance(style, str):
            self.__style = style


# NOTE: **started** to implement cell properties
#       all properties are not functional/not available on all export method...
#       need to finish it

class TextTableCell(object):
    """A really basic HTML cell definition"""
    def __init__(self, content, colspan=None, rowspan=None, bgColor=None, alignH=None, alignV=None):
        self.__content=content
        self.__colspan=colspan
        self.__rowspan=rowspan
        self.__bgColor=bgColor
        self.__alignH=alignH
        self.__alignV=alignV

    def content(self):
        return self.__content

    def colspan(self):
        return self.__colspan

    def rowspan(self):
        return self.__rowspan

    def bgColor(self):
        return self.__bgColor

    def alignH(self):
        return self.__alignH

    def alignV(self):
        return self.__alignV



class TextTable(object):
    """An object to store data in a table that can easily be exported as text"""
    __BORDER_TEXT_CHARS_TL=0
    __BORDER_TEXT_CHARS_TM=1
    __BORDER_TEXT_CHARS_TCA=2
    __BORDER_TEXT_CHARS_TCB=3
    __BORDER_TEXT_CHARS_TC=4
    __BORDER_TEXT_CHARS_TR=5
    __BORDER_TEXT_CHARS_BL=6
    __BORDER_TEXT_CHARS_BM=7
    __BORDER_TEXT_CHARS_BCA=8
    __BORDER_TEXT_CHARS_BCB=9
    __BORDER_TEXT_CHARS_BC=10
    __BORDER_TEXT_CHARS_BR=11
    __BORDER_TEXT_CHARS_RL=12
    __BORDER_TEXT_CHARS_RM=13
    __BORDER_TEXT_CHARS_RCA=14
    __BORDER_TEXT_CHARS_RCB=15
    __BORDER_TEXT_CHARS_RC=16
    __BORDER_TEXT_CHARS_RR=17
    __BORDER_TEXT_CHARS_SL=18
    __BORDER_TEXT_CHARS_SM=19
    __BORDER_TEXT_CHARS_SCA=20
    __BORDER_TEXT_CHARS_SCB=21
    __BORDER_TEXT_CHARS_SC=22
    __BORDER_TEXT_CHARS_SR=23
    __BORDER_TEXT_CHARS_HL=24
    __BORDER_TEXT_CHARS_HM=25
    __BORDER_TEXT_CHARS_HCA=26
    __BORDER_TEXT_CHARS_HCB=27
    __BORDER_TEXT_CHARS_HC=28
    __BORDER_TEXT_CHARS_HR=29

    __BORDER_TEXT_TYPE_SEP = 0
    __BORDER_TEXT_TYPE_HSEP = 1
    __BORDER_TEXT_TYPE_TOP = 2
    __BORDER_TEXT_TYPE_BOTTOM = 3

    __BORDER_CHARS={
            # TextTableSettingsText.BORDER_NONE
            0: [
                    '', '', '', '', '', '',             # tl, tm, tca, tcb, tc, tr
                    '', '', '', '', '', '',             # bl, bm, bca, bcb, bc, br
                    '', '', '', '', ' ', '',            # rl, rm, rca, rcb, rc, rr
                    '', '', '', '', '', '',             # sl, sm, sca, scb, sc, sr
                    '', '', '', '', '', ''              # hl, hm, hca, hcb, hc, hr
                ],
            # TextTableSettingsText.BORDER_BASIC
            1: [
                    '+', '=', '+', '+', '+', '+',       # tl, tm, tca, tcb, tc, tr
                    '+', '=', '+', '+', '+', '+',       # bl, bm, bca, bcb, bc, br
                    '|', ' ', '|', '|', '|', '|',       # rl, rm, rca, rcb, rc, rr
                    '+', '-', '+', '+', '+', '+',       # sl, sm, sca, scb, sc, sr
                    '+', '=', '+', '+', '+', '+'        # hl, hm, hca, hcb, hc, hr
                ],
            # TextTableSettingsText.BORDER_SIMPLE
            2: [
                    '┌', '─', '┬', '┬', '┬', '┐',       # tl, tm, tca, tcb, tc, tr
                    '└', '─', '┴', '┴', '┴', '┘',       # bl, bm, bca, bcb, bc, br
                    '│', ' ', '│', '│', '│', '│',       # rl, rm, rca, rcb, rc, rr
                    '├', '─', '┴', '┬', '┼', '┤',       # sl, sm, sca, scb, sc, sr
                    '├', '─', '┴', '┬', '┼', '┤'        # hl, hm, hca, hcb, hc, hr
                ],
            # TextTableSettingsText.BORDER_DOUBLE
            3: [
                    '╔', '═', '╤', '╤', '╤', '╗',       # tl, tm, tca, tcb, tc, tr
                    '╚', '═', '╧', '╧', '╧', '╝',       # bl, bm, bca, bcb, bc, br
                    '║', ' ', '│', '│', '│', '║',       # rl, rm, rca, rcb, rc, rr
                    '╟', '─', '┴', '┬', '┼', '╢',       # sl, sm, sca, scb, sc, sr
                    '╠', '═', '╧', '╤', '╪', '╣'        # hl, hm, hca, hcb, hc, hr

                ]
        }

    def __init__(self):
        self.__nbRows = 0
        self.__nbCols = 0
        self.__header = []
        self.__rows = []
        self.__colSize = []
        self.__currentWidth = 0

        self.__title = ''

    def __repr__(self):
        return f"<TextTable()>"


    def addRow(self, rowContent):
        """Add a row to table

        A row can be:
        - a string (ie: one column)
        - an array of string; if number of columns is bigger than current columns
          count number, then this will define new columns count
          For rows with a number of columns less than total number of column, the
          first (or last, according to table configuration) will b e merged to
          extent colum size
        """
        if isinstance(rowContent, str):
            self.__rows.append([TextTableCell(rowContent)])
        elif isinstance(rowContent, list):
            self.__rows.append([TextTableCell(cellContent) if isinstance(cellContent, str) else cellContent for cellContent in rowContent])

    def addSeparator(self):
        """Add a separator in table"""
        self.__rows.append(0x01)

    def setHeader(self, headerContent):
        """Set a header to table

        A header can be:
        - a string (ie: one column)
        - an array of string; if number of columns is bigger than current columns
          count number, then this will define new columns count
        """
        if isinstance(headerContent, str):
            self.__header = [TextTableCell(headerContent)]
        elif isinstance(headerContent, list):
            self.__header = [TextTableCell(cellContent) if isinstance(cellContent, str) else cellContent for cellContent in headerContent]

    def setTitle(self, title=None):
        """Set current table title"""
        if isinstance(title, str) and title.strip()!='':
            self.__title = title
        else:
            self.__title = None

    def asText(self, settings):
        """Return current table as a string, ussing given settings (TextTableSettingsText)"""
        def columnsWidth(row, ref=None):
            # calculate columns width
            returned = [0] * self.__nbColumns
            for index, column in enumerate(row):
                if column is None:
                    returned[index] = 0
                else:
                    # ensure that column content is text
                    asText=str(column.content())
                    if os.linesep in asText:
                        sizeText=0
                        for line in asText.split(os.linesep):
                            if len(line)>sizeText:
                                sizeText=len(line)
                    else:
                        sizeText=len(asText)

                    returned[index] = sizeText

            if not ref is None:
                for index in range(len(ref)):
                    if returned[index] < ref[index]:
                        returned[index] = ref[index]
            return returned

        def buildSep(columnsAbove=None, columnsBelow=None, sepType=None):
            # return a separator string, taking in account:
            # - columns above
            # - columns below
            # - render mode
            returned = ''
            headerOffset=0

            if columnsAbove is None:
                columnsAbove = 0
            if columnsBelow is None:
                columnsBelow = 0

            if sepType == TextTable.__BORDER_TEXT_TYPE_TOP:
                headerOffset=-18
            elif sepType == TextTable.__BORDER_TEXT_TYPE_BOTTOM:
                headerOffset=-12
            elif sepType == TextTable.__BORDER_TEXT_TYPE_HSEP:
                headerOffset=6

            if settings.border() == TextTableSettingsText.BORDER_NONE:
                # doesn't take in account above and below rows
                returned = '-' * self.__currentWidth
            else:
                returned = TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_SL+headerOffset]

                for index in range(self.__nbCols):
                    returned += TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_SM+headerOffset] * self.__colSize[index]
                    if index < (self.__nbCols - 1):
                        # add columns separator
                        offset = 0
                        if (index + 1) < columnsAbove:
                            offset += 0b01
                        if (index + 1) < columnsBelow:
                            offset += 0b10
                        returned += TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_SM + offset + headerOffset]

                returned += TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_SR + headerOffset]

            return [returned]

        def buildRow(columnsContent, columnsSize=None):
            # return a separator string, taking in account:
            # - columns content
            # - columns sizes
            # - render mode
            returned = []

            if columnsSize is None:
                columnsSize = self.__colSize

            nbRows=0
            colsContent=[]

            for index, column in enumerate(columnsContent):
                fmtRow=strToMaxLength(column.content(), columnsSize[index], True, settings.columnAlignment(index)==0).split(os.linesep)
                colsContent.append(fmtRow)

                nbFmtRows=len(fmtRow)
                if nbFmtRows > nbRows:
                    nbRows = nbFmtRows

            lastColIndex = len(columnsContent) -1
            for rowIndex in range(nbRows):
                returnedRow=TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_RL]

                for colIndex, column in enumerate(colsContent):
                    if rowIndex < len(column):
                        returnedRow+=column[rowIndex]
                    else:
                        returnedRow+=strToMaxLength(' ', columnsSize[colIndex], True, settings.columnAlignment(colIndex)==0)

                    if colIndex < lastColIndex:
                        returnedRow+=TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_RC]

                returnedRow+=TextTable.__BORDER_CHARS[settings.border()][TextTable.__BORDER_TEXT_CHARS_RR]
                returned.append(returnedRow)

            return returned

        def buildTitle():
            """Add a title to generated table"""
            return [self.__title]

        def buildHeader():
            returned=[]

            if len(self.__header) == 0 or not settings.headerActive():
                # no header
                if len(self.__rows) == 0:
                    # no rows...
                    return returned

                returned+=buildSep(None, len(self.__rows[0]), TextTable.__BORDER_TEXT_TYPE_TOP)
            else:
                returned+=buildSep(None, len(self.__header), TextTable.__BORDER_TEXT_TYPE_TOP)
                returned+=buildRow(self.__header)

                if len(self.__rows) == 0:
                    # no rows...
                    returned+=buildSep(len(self.__header), None, TextTable.__BORDER_TEXT_TYPE_BOTTOM)
                else:
                    returned+=buildSep(len(self.__header), len(self.__rows[0]), TextTable.__BORDER_TEXT_TYPE_HSEP)

            return returned

        if not isinstance(settings, TextTableSettingsText):
            raise EInvalidType("Given `settings` must be <TextTableSettingsText>")


        maxWidth = settings.maxWidth()
        if not settings.maxWidthActive():
            maxWidth = 0

        minWidth = settings.minWidth()
        if not settings.minWidthActive():
            minWidth = 1


        # one text row = one buffer row
        buffer=[]

        # 1. calculate number of columns
        # ------------------------------
        self.__nbColumns = len(self.__header)
        for row in self.__rows:
            if isinstance(row, list) and len(row) > self.__nbColumns:
                self.__nbColumns = len(row)

        # 2. calculate columns width
        # --------------------------
        self.__colSize = columnsWidth(self.__header)
        for row in self.__rows:
            if isinstance(row, list):
                self.__colSize = columnsWidth(row, self.__colSize)
        self.__nbCols=len(self.__colSize)

        # 3. Adjust columns width according to min/max table width
        # --------------------------------------------------------
        if settings.border() == TextTableSettingsText.BORDER_NONE:
            # no external borders
            extBorderSize = -1
        else:
            # 2 external borders
            extBorderSize = 1
        self.__currentWidth = sum(self.__colSize) + self.__nbColumns + extBorderSize

        expectedWidth=None
        if maxWidth > 0 and self.__currentWidth > maxWidth:
            # need to reduce columns sizes
            expectedWidth=maxWidth
        elif minWidth > 0 and self.__currentWidth < minWidth:
            # need to increase columns sizes
            expectedWidth=minWidth

        if not expectedWidth is None:
            # need to apply factor size to columns width
            factor = expectedWidth / self.__currentWidth
            fixedWidth = 0

            for index in range(self.__nbColumns - 1):
                self.__colSize[index]=int(round(self.__colSize[index] * factor, 0))
                fixedWidth+=self.__colSize[index]

            self.__colSize[-1]=expectedWidth - fixedWidth - (self.__nbColumns + extBorderSize)
            self.__currentWidth = expectedWidth

        # 4. Generate table
        # --------------------------------------------------------
        lastRowIndex = len(self.__rows) - 1

        if self.__title.strip() != '':
            buffer+=buildTitle()
        buffer+=buildHeader()

        prevColCount = None
        nextColCount = None
        lastIndex = len(self.__rows) - 1
        for index, row in enumerate(self.__rows):
            nextIndex = index + 1
            while nextIndex < (len(self.__rows) - 1 ) and isinstance(self.__rows[nextIndex], int):
                nextIndex+=1

            if nextIndex > (len(self.__rows) - 1 ) or nextIndex < (len(self.__rows) - 1 ) and isinstance(self.__rows[nextIndex], int):
                nextRow = None
            else:
                nextRow = self.__rows[nextIndex]

            if row == 0x01:
                if not nextRow is None:
                    nextColCount = len(nextRow)
                else:
                    nextColCount = None
                buffer+=buildSep(prevColCount, nextColCount)
            else:
                buffer+=buildRow(row)
                prevColCount=len(row)

        buffer+=buildSep(prevColCount, None, TextTable.__BORDER_TEXT_TYPE_BOTTOM)

        return os.linesep.join(buffer)

    def asTextCsv(self, settings):
        """Return current table as CSV formatted string, using given settings (TextTableSettingsTextCsv)"""

        def buildRow(columnsContent):
            if enclosed:
                sep = f'"{separator}"'
                returned = f'"{sep.join([columnContent.content() for columnContent in columnsContent])}"'
            else:
                returned = separator.join([columnContent.content() for columnContent in columnsContent])

            return [returned]

        def buildHeader():
            returned=[]

            if len(self.__header) == 0 or not settings.headerActive():
                return returned
            else:
                returned=buildRow(self.__header)

            return returned

        if not isinstance(settings, TextTableSettingsTextCsv):
            raise EInvalidType("Given `settings` must be <TextTableSettingsTextCsv>")

        # one text row = one buffer row
        buffer=[]

        separator = settings.separator()
        enclosed = settings.enclosedField()

        # 1. Generate table
        # --------------------------------------------------------
        buffer=buildHeader()

        for row in self.__rows:
            if row != 0x01:
                # ignore separators for CSV file :)
                buffer+=buildRow(row)

        return os.linesep.join(buffer)

    def asTextMarkdown(self, settings):
        """Return current table as Markdown (GitHub flavored version) formatted string, using given settings (TextTableSettingsTextMarkdown)"""

        def buildRow(columnsContent, format):
            def escape(text):
                if text == '':
                    return text

                text = text.replace("\\", r"\\")
                text = text.replace(r"`", r"\`")
                text = text.replace(r"*", r"\*")
                text = text.replace(r"_", r"\_")
                text = text.replace(r"{", r"\{")
                text = text.replace(r"}", r"\}")
                text = text.replace(r"[", r"\[")
                text = text.replace(r"]", r"\]")
                text = text.replace(r"(", r"\(")
                text = text.replace(r")", r"\)")
                text = text.replace(r"#", r"\#")
                text = text.replace(r"+", r"\+")
                text = text.replace(r"-", r"\-")
                text = text.replace(r".", r"\.")
                text = text.replace(r"!", r"\!")
                return text

            def formatItem(text, formatting):
                returned = text
                if isinstance(formatting, tuple) and text!='':
                    canEscape=True
                    for format in formatting:
                        if re.match("`[^`]+`", format):
                            canEscape=False
                            break
                    if canEscape:
                        returned = escape(returned)

                    for format in formatting:
                        returned = format.replace('{text}', returned)
                return returned

            if format:
                return [' | '.join([formatItem(column.content(), settings.columnFormatting(index)) for index, column in enumerate(columnsContent)])]
            else:
                return [' | '.join([escape(column.content()) for column in columnsContent])]

        def buildHeader():
            returned=[]

            header = []
            maxColNumber = 0
            for row in self.__rows:
                if row==0x01:
                    # ignore separator
                    continue
                rowLen = len(row)
                if rowLen > maxColNumber:
                    maxColNumber = rowLen

            if len(self.__header) == 0 and maxColNumber > 0:
                # no header!?
                # github flavored markdown table NEED header..
                # build one :)
                header = ['?'] * maxColNumber
            elif len(self.__header) > 0:
                header = self.__header

                if len(header) < maxColNumber:
                    # not enough cell in header... add missing cells
                    header += ['?'] * (maxColNumber - len(header))

            if len(header) == 0:
                # no header AND no data
                # return nothing
                return returned

            headerSep = ['--'] * len(header)
            returned=buildRow(header, False)
            returned+=[' | '.join(headerSep)]

            if len(self.__rows) == 0:
                # there's an header, but no data....?
                # create an empty row as data to display at least, the header
                returned=+buildRow([' '] * len(header), False)

            return returned

        def buildTitle():
            """Add a title to generated table"""
            return [self.__title]

        if not isinstance(settings, TextTableSettingsTextMarkdown):
            raise EInvalidType("Given `settings` must be <TextTableSettingsTextMarkdown>")

        # one text row = one buffer row
        buffer=[]

        if self.__title.strip() != '':
            buffer+=buildTitle()
        buffer+=buildHeader()

        if len(buffer) == 0:
            # nothing to format...
            return ''

        for row in self.__rows:
            if row != 0x01:
                # ignore separators for CSV file :)
                buffer+=buildRow(row, True)

        return os.linesep.join(buffer)

    def asHtml(self, settings):
        """Return current table as an HTML string, ussing given settings (TextTableSettingsTextHtml)"""

        def buildRow(columnsContent, cellType='td'):
            returned=[]
            for column in columnsContent:
                fmt=''
                if column.colspan():
                    fmt+=f' colspan={column.colspan()}'

                if column.bgColor():
                    fmt+=f' bgcolor={column.bgColor()}'


                returned.append(f"<{cellType}{fmt}>{column.content()}</{cellType}>")

            returned="\n".join(returned)

            return [f"<tr>{returned}</tr>"]

        def buildSep():
            return [f"<tr><td colspan={self.__nbCols}>&nbsp;</td></tr>"]

        def buildHeader():
            returned=[]

            header = []
            maxColNumber = 0
            for row in self.__rows:
                if row==0x01:
                    # ignore separator
                    continue
                rowLen = len(row)
                if rowLen > maxColNumber:
                    maxColNumber = rowLen

            if len(self.__header) > 0:
                header = self.__header

                if len(header) < maxColNumber:
                    # not enough cell in header... add missing cells
                    header += ['?'] * (maxColNumber - len(header))
            else:
                # no header, return nothing
                return returned

            return buildRow(header, 'th')

        if not isinstance(settings, TextTableSettingsTextHtml):
            raise EInvalidType("Given `settings` must be <TextTableSettingsTextHtml>")

        # one text row = one buffer row
        buffer=[]

        buffer+=buildHeader()

        for row in self.__rows:
            if row == 0x01:
                buffer+=buildSep()
            else:
                buffer+=buildRow(row)

        if len(buffer)>0:
            return f"<table width=100%>{os.linesep.join(buffer)}</table>"
        else:
            return ''
