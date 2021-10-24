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

from enum import Enum
import re
import html

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from .wsearchinput import SearchFromPlainTextEdit


class WConsoleType(Enum):
    """Define type of new line append in console

    By default, NORMAL type is applied, and standard rendering is applied to
    console line content

    If type is not NORMAL:
    - A colored bullet is drawn in gutter
      NORMAL:   none
      VALID:    green
      INFO:     cyan
      WARNING:  yellow
      ERROR:    red
    - Background style is colored

    Style (bullet, background, text) can be defined on console
    """
    NORMAL = 0
    VALID = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

    @staticmethod
    def toStr(value):
        values={
                WConsoleType.VALID: 'valid',
                WConsoleType.INFO: 'info',
                WConsoleType.WARNING: 'warning',
                WConsoleType.ERROR: 'error'
            }
        if value in values:
            return values[value]
        return 'normal'

    @staticmethod
    def fromStr(value):
        values={
                'valid': WConsoleType.VALID,
                'info': WConsoleType.INFO,
                'warning': WConsoleType.WARNING,
                'error': WConsoleType.ERROR
            }
        if value in values:
            return values[value]
        return WConsoleType.NORMAL



class WConsole(QPlainTextEdit):
    """A console output (no input...)"""

    __TYPE_COLOR_ALPHA=30

    @staticmethod
    def escape(text):
        """Escape characters used to format data in console:
            '*'
            '#'

        """
        return re.sub(r'([\*\$#])', r'$\1', text)

    def unescape(text):
        """unescape characters used to format data in console:
            '*'
            '#'
        """
        return re.sub(r'(?:\$([\*\$#]))', r'\1', text)


    def __init__(self, parent=None):
        super(WConsole, self).__init__(parent)

        self.setReadOnly(True)

        self.__typeColors={
                WConsoleType.VALID: QColor('#39b54a'),
                WConsoleType.INFO: QColor('#006fb8'),
                WConsoleType.WARNING: QColor('#ffc706'),
                WConsoleType.ERROR: QColor('#de382b')
            }

        self.__styleColors={
                'r':  QColor("#de382b"),
                'g':  QColor("#39b54a"),
                'b':  QColor("#006fb8"),
                'c':  QColor("#2cb5e9"),
                'm':  QColor("#762671"),
                'y':  QColor("#ffc706"),
                'k':  QColor("#000000"),
                'w':  QColor("#cccccc"),
                'lr': QColor("#ff0000"),
                'lg': QColor("#00ff00"),
                'lb': QColor("#0000ff"),
                'lc': QColor("#00ffff"),
                'lm': QColor("#ff00ff"),
                'ly': QColor("#ffff00"),
                'lk': QColor("#808080"),
                'lw': QColor("#ffffff")
            }


        # Gutter colors
        # maybe font size/type/style can be modified
        self.__optionGutterText=QTextCharFormat()
        self.__optionGutterText.setBackground(QColor('#282c34'))

        # show gutter with Warning/Error/... message type
        self.__optionShowGutter=True

        # allows key bindings
        self.__optionWheelSetFontSize=True

        # filtered
        self.__optionFilteredTypes=[]

        # search object
        self.__search=SearchFromPlainTextEdit(self)

        # ---- Set default font (monospace, 10pt)
        font = QFont()
        font.setFamily("Monospace")
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)

        # ---- instanciate gutter area
        self.__gutterArea = WConsoleGutterArea(self)

        # ---- initialise signals
        self.updateRequest.connect(self.__updateGutterArea)

        # default values
        self.__updateGutterAreaWidth()


        self.setStyleSheet(f"WConsole {{ background: {self.__styleColors['k'].name()}; color: {self.__styleColors['w'].name()};}}")


    def __updateGutterArea(self, rect, deltaY):
        """Called on signal updateRequest()

        Invoked when the editors viewport has been scrolled

        The given `rect` is the part of the editing area that need to be updated (redrawn)
        The given `dy` holds the number of pixels the view has been scrolled vertically
        """
        if self.__optionShowGutter:
            if deltaY>0:
                self.__gutterArea.scroll(0, deltaY)
            else:
                self.__gutterArea.update(0, rect.y(), self.__gutterArea.width(), rect.height())

            if rect.contains(self.viewport().rect()):
                self.__updateGutterAreaWidth(0)


    def __updateGutterAreaWidth(self, dummy=None):
        """Update viewport margins, taking in account gutter visibility"""
        self.setViewportMargins(self.gutterAreaWidth(), 0, 0, 0)


    def __formatText(self, text):
        """Return a HTML formatted text from a markdown like text

        Allows use of some 'Markdown':
        **XXX**     => bold
        *XXX*       => italic

        #r#XXX#     => RED
        #g#XXX#     => GREEN
        #b#XXX#     => BLUE
        #c#XXX#     => CYAN
        #m#XXX#     => MAGENTA
        #y#XXX#     => YELLOW
        #k#XXX#     => BLACK
        #w#XXX#     => WHITE

        #lr#XXX#    => LIGHT RED
        #lg#XXX#    => LIGHT GREEN
        #lb#XXX#    => LIGHT BLUE
        #lc#XXX#    => LIGHT CYAN
        #lm#XXX#    => LIGHT MAGENTA
        #ly#XXX#    => LIGHT YELLOW
        #lk#XXX#    => LIGHT BLACK (GRAY)
        #lw#XXX#    => LIGHT WHITE

        #xxxxxx#XXX# => Color #xxxxxx



        [c:nn]XXX[/c] => color 'nn'
        """
        def replaceColor(regResult):
            colorCode=regResult.groups()[0]
            if colorCode in self.__styleColors:
                color=self.__styleColors[colorCode].name()
            else:
                try:
                    color=QColor(f'#{colorCode}').name()
                except Exception as e:
                    color=None
            if color is None:
                return regResult.groups()[1]
            else:
                return f'<span style="color: {color}">{regResult.groups()[1]}</span>'

        def asBold(regResult):
            return f'<b>{WConsole.unescape(regResult.groups()[0])}</b>'

        def asItalic(regResult):
            return f'<i>{WConsole.unescape(regResult.groups()[0])}</i>'

        def formatText(text):
            text=re.sub(r'(?<!\$)\*\*(([^*]|\$\*)+)(?<!\$)\*\*', r'<b>\1</b>', text)
            text=re.sub(r'(?<!\$)\*(([^*]|\$\*)+)(?<!\$)\*', r'<i>\1</i>', text)
            text=re.sub(r'(?<!\$)#(l?[rgbcmykw]|[A-F0-9]{6})(?<!\$)#(([^#]|\$#)+)(?<!\$)#', replaceColor, text)
            return WConsole.unescape(text)

        texts=text.split("\n")
        returned=[]
        for text in texts:
            returned.append(formatText(text))

        return returned


    def __getFontMarkup(self, text, formatOptions):
        """Return an html formatted `text`, taking in account `formatOptions`"""
        options=[]
        text=html.escape(text)

        if formatOptions & WConsoleTextStyle.FONT_BOLD == WConsoleTextStyle.FONT_BOLD:
            options+='font-weight: bold;'
        if formatOptions & WConsoleTextStyle.FONT_ITALIC == WConsoleTextStyle.FONT_ITALIC:
            options+='font-style: italic;'
        if formatOptions & 0xFF != WConsoleTextStyle.COLOR_DEFAULT:
            color='#00ffff'
            options+=f'color: {color};'

        if len(options)>0:
            fmtOptions=''.join(options)
            return f'<span style="{fmtOptions}">{text}</span>'
        else:
            return text


    def __isTypeFiltered(self, type):
        """Return True if given `type` is filtered"""
        return (type in self.__optionFilteredTypes)


    def __updateFilteredTypes(self):
        """Update current filtered types"""
        block = self.document().firstBlock()

        while block.isValid():
            colorLevel=WConsoleType.NORMAL

            blockData=block.userData()
            if blockData:
                colorLevel=block.userData().type()

            block.setVisible(not self.__isTypeFiltered(colorLevel))
            block = block.next()

        self.update()


    # region: event overload ---------------------------------------------------

    def resizeEvent(self, event):
        """Console is resized

        Need to resize the gutter area
        """
        super(WConsole, self).resizeEvent(event)

        if self.__optionShowGutter:
            contentRect = self.contentsRect()
            self.__gutterArea.setGeometry(QRect(contentRect.left(), contentRect.top(), self.gutterAreaWidth(), contentRect.height()))


    def gutterAreaPaintEvent(self, event):
        """Paint gutter content"""
        # initialise painter on WCELineNumberArea
        painter=QPainter(self.__gutterArea)
        painter.setRenderHint(QPainter.Antialiasing)

        # set background
        rect=event.rect()
        painter.fillRect(rect, self.__optionGutterText.background())

        painter.setPen(QPen(Qt.transparent))

        # Get the top and bottom y-coordinate of the first text block,
        # and adjust these values by the height of the current text block in each iteration in the loop
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()

        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        dx=self.__gutterArea.width()//2
        dy=self.fontMetrics().height()//2
        radius=(dy - 4)//2

        # Loop through all visible lines and paint the line numbers in the extra area for each line.
        # Note: in a plain text edit each line will consist of one QTextBlock
        #       if line wrapping is enabled, a line may span several rows in the text edit’s viewport
        while block.isValid() and top <= event.rect().bottom():
            # Check if the block is visible in addition to check if it is in the areas viewport
            #   a block can, for example, be hidden by a window placed over the text edit
            if block.isVisible() and bottom >= event.rect().top():
                colorLevel=WConsoleType.NORMAL

                blockData=block.userData()
                if blockData:
                    colorLevel=block.userData().type()

                if colorLevel!=WConsoleType.NORMAL:
                    color=QColor(self.__typeColors[colorLevel])
                    center=QPoint(dx, top+dx)
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(center, radius, radius)

                    h=bottom - center.y() - dy
                    if h>dy:
                        painter.drawRoundedRect(dx-2, center.y(), 4, h, 2, 2)

                    color.setAlpha(WConsole.__TYPE_COLOR_ALPHA)
                    painter.fillRect(QRect(rect.left(), top, rect.width(), self.blockBoundingRect(block).height()), QBrush(color))


            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber+=1


    def wheelEvent(self, event):
        """CTRL + wheel os used to zoom in/out font size"""
        if self.__optionWheelSetFontSize and event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta < 0:
                self.zoomOut()
            elif delta > 0:
                self.zoomIn()
        else:
            super(WConsole, self).wheelEvent(event)


    def paintEvent(self, event):
        """Customize painting for block types"""

        # initialise some metrics
        rect = event.rect()
        font = self.currentCharFormat().font()
        charWidth = QFontMetricsF(font).averageCharWidth()
        leftOffset = self.contentOffset().x() + self.document().documentMargin()

        # initialise painter to editor's viewport
        painter = QPainter(self.viewport())


        block = self.firstVisibleBlock()

        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            # Check if the block is visible in addition to check if it is in the areas viewport
            #   a block can, for example, be hidden by a window placed over the text edit
            if block.isVisible() and bottom >= event.rect().top():

                colorLevel=WConsoleType.NORMAL

                blockData=block.userData()
                if blockData:
                    colorLevel=block.userData().type()

                if colorLevel!=WConsoleType.NORMAL:
                    color=QColor(self.__typeColors[colorLevel])
                    color.setAlpha(WConsole.__TYPE_COLOR_ALPHA)
                    painter.fillRect(QRect(rect.left(), top, rect.width(), self.blockBoundingRect(block).height()), QBrush(color))

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

        super(WConsole, self).paintEvent(event)


    # endregion: event overload ------------------------------------------------


    def gutterAreaWidth(self):
        """Calculate width for gutter area

        Width is calculated according to gutter visibility
        """
        if self.__optionShowGutter:
            digits = 2
            # width = (witdh for digit '9') * (number of digits) + 3pixels
            return 3 + self.fontMetrics().width('9') * 2
        return 0


    def optionShowGutter(self):
        """Return if gutter is visible or not"""
        return self.__optionShowGutter


    def setOptionShowGutter(self, value):
        """Set if gutter is visible or not"""
        if isinstance(value, bool) and value != self.__optionShowGutter:
            self.__optionShowGutter=value
            if value:
                self.__gutterArea = WConsoleGutterArea(self)
            else:
                self.__gutterArea.disconnect()
                self.__gutterArea = None

            self.__updateGutterAreaWidth()
            self.update()


    def optionAllowWheelSetFontSize(self):
        """Return if CTRL+WHEEL allows to change font size"""
        return self.__optionWheelSetFontSize


    def setOptionAllowWheelSetFontSize(self, value):
        """Set if CTRL+WHEEL allows to change font size"""
        if isinstance(value, bool) and value != self.__optionWheelSetFontSize:
            self.__optionWheelSetFontSize=value


    def setHeight(self, numberOfRows=None):
        """Set height according to given number of rows"""

        if numberOfRows is None:
            self.setminimumHeight(0)
            self.setMaximumHeight(16777215)
        elif isinstance(numberOfRows, int) and numberOfRows>0:
            doc = self.document()
            fontMetrics=QFontMetrics(doc.defaultFont())
            margins = self.contentsMargins()

            self.setFixedHeight(fontMetrics.lineSpacing() * numberOfRows + (doc.documentMargin() + self.frameWidth()) * 2 + margins.top () + margins.bottom())


    def optionBufferSize(self):
        """Return maximum buffer size for console"""
        return self.maximumBlockCount()


    def setOptionBufferSize(self, value):
        """Set maximum buffer size for console"""
        return self.setMaximumBlockCount(value)


    def optionFilteredTypes(self):
        """Return list of filtered types"""
        return self.__optionFilteredTypes


    def setOptionFilteredTypes(self, filteredTypes):
        """Set list of filtered types"""
        if isinstance(filteredTypes, list):
            self.__optionFilteredTypes=[]
            self.setOptionAddFilteredTypes(filteredTypes)


    def setOptionAddFilteredTypes(self, filteredTypes):
        """Add filtered types

        Given `filteredTypes` can be a <WConsoleType> or a <list>
        """
        if isinstance(filteredTypes, WConsoleType):
            filteredTypes=[filteredTypes]

        if isinstance(filteredTypes, list):
            for filteredType in filteredTypes:
                if isinstance(filteredType, WConsoleType) and not filteredType in self.__optionFilteredTypes:
                    self.__optionFilteredTypes.append(filteredType)

            self.__updateFilteredTypes()


    def setOptionRemoveFilteredTypes(self, filteredTypes):
        """Remove filtered types

        Given `filteredTypes` can be a <WConsoleType> or a <list>
        """
        if isinstance(filteredTypes, WConsoleType):
            filteredTypes=[filteredTypes]

        if isinstance(filteredTypes, list):
            current=self.__optionFilteredTypes
            self.__optionFilteredTypes=[]
            for filteredType in current:
                if not filteredType in filteredTypes:
                    self.__optionFilteredTypes.append(filteredType)

            self.__updateFilteredTypes()


    # ---


    def appendLine(self, text, type=WConsoleType.NORMAL, data=None):
        """Append a new line to console

        Given `style` is a combination of WConsoleTextStyle
            Example: WConsoleTextStyle.FONT_BOLD|WConsoleTextStyle.COLOR_RED

        Given `type` is a WConsoleType value
        """
        lines=self.__formatText(text)
        for line in lines:
            self.appendHtml(line)

            lastBlock=self.document().lastBlock()
            if lastBlock:
                lastBlock.setUserData(WConsoleUserData(type, data))
                lastBlock.setVisible(not self.__isTypeFiltered(type))


    def append(self, text):
        """Append to current line"""

        texts=self.__formatText(text)

        for text in texts:
            self.moveCursor(QTextCursor.End)
            self.textCursor().insertHtml(text)
            self.moveCursor(QTextCursor.End)


    # ---

    def search(self):
        """Return search object"""
        return self.__search



class WConsoleUserData(QTextBlockUserData):

    def __init__(self, type=None, data={}):
        QTextBlockUserData.__init__(self)
        self.__type=type
        self.__data=data

    def type(self):
        return self.__type

    def data(self, key=None):
        if key is None or not isinstance(self.__data, dict):
            return self.__data
        elif key in self.__data:
            return self.__data[key]
        else:
            return None


class WConsoleGutterArea(QWidget):
    """Gutter area for console

    # From example documentation
    We paint the line numbers on this widget, and place it over the WConsole's viewport() 's left margin area.

    We need to use protected functions in QPlainTextEdit while painting the area.
    So to keep things simple, we paint the area in the WConsole class.
    The area also asks the editor to calculate its size hint.

    Note that we could simply paint the gutter content directly on the code editor, and drop the WConsoleGutterArea class.
    However, the QWidget class helps us to scroll() its contents.
    Also, having a separate widget is the right choice if we wish to extend the console features.
    The widget would then help in the handling of mouse events.
    """

    def __init__(self, console):
        super(WConsoleGutterArea, self).__init__(console)
        self.__console = console

    def sizeHint(self):
        if self.__console:
            return QSize(self.__console.gutterAreaWidth(), 0)
        return QSize(0, 0)

    def paintEvent(self, event):
        """It Invokes the draw method(gutterAreaPaintEvent) in Console"""
        if self.__console:
            self.__console.gutterAreaPaintEvent(event)

    def disconnect(self):
        """Disconnect area from console"""
        self.__console = None
