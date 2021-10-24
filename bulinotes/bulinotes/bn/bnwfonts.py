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
import re

from bulinotes.pktk import *

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from bulinotes.pktk.modules.fontdb import FontDatabase
from bulinotes.pktk.modules.strutils import (stripHtml, bytesSizeToStr)
from bulinotes.pktk.modules.imgutils import warningAreaBrush
from bulinotes.pktk.modules.fontdb import Font
from bulinotes.pktk.widgets.wtextedit import (WTextEdit, WTextEditDialog, WTextEditBtBarOption)
from bulinotes.pktk.widgets.wiodialog import WDialogBooleanInput

from .bnembeddedfont import BNEmbeddedFont
from .bnsettings import (BNSettings, BNSettingsKey)



class BNFont:
    """A font definition for tree view"""
    def __init__(self, name, used, fonts):
        self.__name=name
        self.__fonts=FontDatabase.font(self.__name)
        self.__used=used
        self.__embedded=(len(fonts)>0)
        self.__totalSize=0
        self.__totalSizeStr=''

        if len(self.__fonts)==0:
            self.__fonts=fonts
        self.__nbFonts=len(self.__fonts)

        for font in self.__fonts:
            self.__nbFonts
            if r:=font.property(Font.PROPERTY_FILE_SIZE):
                self.__totalSize+=r
            elif font.type()==Font.TYPE_OPENTYPE_TTC:
                self.__nbFonts+=font.property(Font.PROPERTY_COLLECTION_COUNT)-1
                for fnt in font.property(Font.PROPERTY_COLLECTION_FONTS):
                    if r:=fnt.property(Font.PROPERTY_FILE_SIZE):
                        self.__totalSize+=r

        self.__totalSizeStr=bytesSizeToStr(self.__totalSize)

    def __eq__(self, value):
        if isinstance(value, BNFont):
            return self.__name==value.__name
        else:
            return self.__name==value

    def name(self):
        """Return font name"""
        return self.__name

    def fonts(self):
        """Return font or None if font defition was not found"""
        return self.__fonts

    def nbFonts(self):
        return self.__nbFonts

    def used(self):
        """Return if font is used in document or not"""
        return self.__used

    def embedded(self):
        """Return if font is embedded in document or not"""
        return self.__embedded

    def setEmbedded(self, value):
        """set if font is embedded in document or not"""
        self.__embedded=value

    def embeddable(self, asBoolean=True):
        """Return if font can be embedded

        If `asBoolean` is True, return a True/False status
        Otherwise return an integer value:
           -2=Not available
           -1=Unknown
            0=Installable
            2=Restricted
            4=Preview & Print
            8=Editable
        """
        if not FontDatabase.installed(self.__name):
            if asBoolean:
                return False
            else:
                return -2
        embeddingState=0
        for fontNfo in self.__fonts:
            propEmbeddingState=fontNfo.embeddingState()[0]
            # for embedding state, as each font in list can have her own embeddable definition
            # need to return the most restrictive from list
            if propEmbeddingState==2:
                # at least one font is in restrictive state, no need to continue
                if asBoolean:
                    return False
                return propEmbeddingState
            elif propEmbeddingState==4 and embeddingState in (0, 8):
                embeddingState=4
            elif propEmbeddingState==8 and embeddingState in (0, 8):
                embeddingState=8
            elif propEmbeddingState!=0:
                # at least one font is an unknown state, no need to continue
                if asBoolean:
                    return False
                return -1
        if asBoolean:
            return embeddingState in (0, 8)
        return embeddingState

    def fileSize(self, asStr=False):
        """return total files size for fonts"""
        if asStr:
            return self.__totalSizeStr
        return self.__totalSize

    def available(self):
        """Return if font is available in QFontDatabase"""
        noFoundryName=None
        if r:=re.search(r"(.*)\s\[[^\]]+\]$", self.__name):
            # a foundry name is present in given font name?
            # get name without foundt name
            noFoundryName=r.groups()[0]

        families=FontDatabase.qFontDatabase().families()
        if self.__name in families or noFoundryName in families:
            return True
        return False



class BNFontsModel(QAbstractTableModel):
    """A model provided to display fonts information"""

    COLNUM_NFO = 0
    ROLE_FONT = Qt.UserRole + 1

    def __init__(self, fonts, parent=None):
        """Initialise list"""
        super(BNFontsModel, self).__init__(parent)
        self.__items=fonts

    def __repr__(self):
        return f'<BNFontsModel()>'

    def __idRow(self, id):
        """Return row number for a given id; return -1 if not found"""
        try:
            return self.__items.index(id)
        except Exception as e:
            return -1

    def dataUpdated(self, fontName):
        index=self.createIndex(self.__idRow(fontName), BNFontsModel.COLNUM_NFO)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def columnCount(self, parent=QModelIndex()):
        """Return total number of column"""
        return 1

    def rowCount(self, parent=QModelIndex()):
        """Return total number of rows"""
        return len(self.__items)

    def data(self, index, role=Qt.DisplayRole):
        """Return data for index+role"""
        column = index.column()
        row=index.row()

        fontNfo=self.__items[row]
        if role == Qt.ToolTipRole:
            pass
        elif role == Qt.DisplayRole:
            return fontNfo.name()
        elif role == BNFontsModel.ROLE_FONT:
            return fontNfo
        return None

    def headerData(self, section, orientation, role):
        return None

    def fonts(self):
        """Expose fonts object"""
        return self.__items

    def embeddable(self):
        """Return number of embeddable fonts"""
        returnedNb=0
        returnedSize=0
        for item in self.__items:
            if item.embeddable():
                returnedNb+=1
                returnedSize+=item.fileSize()
        return (returnedNb, returnedSize)

    def embedded(self):
        """Return number of embedded fonts"""
        returnedNb=0
        returnedSize=0
        for item in self.__items:
            if item.embedded():
                returnedNb+=1
                returnedSize+=item.fileSize()
        return (returnedNb, returnedSize)


class BNWFonts(QTreeView):
    """Tree view fonts (editing mode)"""
    embbedFontStateChanged = Signal(BNFont, bool)

    def __init__(self, parent=None):
        super(BNWFonts, self).__init__(parent)
        self.setAutoScroll(False)
        #self.setAlternatingRowColors(True)

        self.__parent=parent
        self.__model = None
        self.__proxyModel = None
        self.__fontSize=self.font().pointSizeF()
        if self.__fontSize==-1:
            self.__fontSize=-self.font().pixelSize()

        self.__delegate=BNFontsModelDelegate(self)
        self.setItemDelegate(self.__delegate)
        self.setUniformRowHeights(True)
        self.setRootIsDecorated(False)

    def mouseDoubleClickEvent(self, event):
        """Double click on item, switch embedded status"""
        self.setEmbedded(userWarning=True)

    def setFonts(self, fonts):
        """Initialise treeview header & model"""
        self.__model = BNFontsModel(fonts)

        self.setModel(self.__model)
        self.resizeColumnToContents(BNFontsModel.COLNUM_NFO)

    def selectedItems(self):
        """Return a list of selected fonts items"""
        returned=[]
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(BNFontsModel.COLNUM_NFO):
                # normaly one item can be selected..
                font=item.data(BNFontsModel.ROLE_FONT)
                if not font is None:
                    returned.append(font)
        return returned

    def nbSelectedItems(self):
        """Return number of selected items"""
        return len(self.selectedItems())

    def setEmbedded(self, value=None, userWarning=False):
        """Set embedded status for current selected items

        If `value` is None, switch current embedded status
        Otherwise apply value

        If given `userWarning` flag is True, a confirmation to user to unembed font will be asked
        if font is not available on system
        """
        if self.selectionModel():
            for item in self.selectionModel().selectedRows(BNFontsModel.COLNUM_NFO):
                font=item.data(BNFontsModel.ROLE_FONT)

                if not font is None:

                    if not font.embeddable():
                        if font.embedded():
                            # we are in the case where font is not installed on
                            # system (not embeddable but embbeded)
                            # in this case, allows to unembed font
                            if userWarning:
                                if WDialogBooleanInput.display(i18n("Unembed font"), i18n("<h1>Warning</h1><p>You're about to unembed a font that is not available on your system.</p><p>Once font is unembedded, it won't be possible anymore to embed it again.</p><p><b><i>Do you confirm action?<i></b></p>")):
                                    newStatus=False
                                else:
                                    continue
                        else:
                            # we are in the case where font can't be embedded
                            # (not installed and/or embeddability rule doesn't
                            # allow to embed font)
                            continue
                    else:
                        # font is embeddable
                        if value is None:
                            newStatus=not font.embedded()
                        else:
                            newStatus=(value==True)

                    if newStatus!=font.embedded():
                        font.setEmbedded(newStatus)
                        self.model().dataUpdated(font.name())
                        self.embbedFontStateChanged.emit(font, newStatus)



class BNFontsModelDelegate(QStyledItemDelegate):
    """Extend QStyledItemDelegate class to build improved rendering items"""
    def __init__(self, parent=None):
        """Constructor, nothingspecial"""
        super(BNFontsModelDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """Paint list item"""
        if index.column() == BNFontsModel.COLNUM_NFO:
            # render brush information
            self.initStyleOption(option, index)

            font=index.data(BNFontsModel.ROLE_FONT)
            height=round((option.rect.height()-4)/5)

            painter.save()

            if not font.available() and not font.embedded():
                # not available or not embeddable
                painter.fillRect(option.rect, warningAreaBrush())


            if (option.state & QStyle.State_Selected) == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
                painter.setPen(QPen(option.palette.color(QPalette.HighlightedText)))
            else:
                painter.setPen(QPen(option.palette.color(QPalette.Text)))

            defaultFnt=painter.font()


            top = option.rect.top() + 2
            left = option.rect.left() + 2

            # draw formatted font name
            textRect=QRect(left, top, option.rect.width(), 2*height)
            fnt=QFont(font.name())
            fnt.setPixelSize(height*2)

            fntLoaded=True
            if not fnt.exactMatch():
                # font not available for Krita (not installed or not loaded)
                painter.setOpacity(0.55)
                fntLoaded=False
            painter.setFont(fnt)
            painter.drawText(textRect, Qt.AlignLeft|Qt.AlignVCenter, font.name())

            if not FontDatabase.installed(font.name()):
                # font not available for Krita (not installed)
                topTmp=top+2*height
                textRect=QRect(left, topTmp, option.rect.width() - 6, option.rect.bottom() - topTmp)
                fnt=QFont(defaultFnt)
                if ps:=fnt.pixelSize()!=-1:
                    fnt.setPixelSize(round(ps*0.84))
                else:
                    fnt.setPointSizeF(fnt.pointSizeF()*0.9)
                fnt.setItalic(True)
                painter.setFont(fnt)
                if fntLoaded:
                    # font has been loaded
                    painter.drawText(textRect, Qt.AlignRight|Qt.AlignTop, "Loaded")
                elif font.embedded():
                    painter.drawText(textRect, Qt.AlignRight|Qt.AlignTop, "Not yet loaded")

            painter.setOpacity(1.0)


            # draw font name (normal font, bold)
            top+=2*height
            textRect=QRect(left, top, option.rect.width(), option.rect.bottom() - top)
            fnt=QFont(defaultFnt)
            fnt.setBold(True)
            painter.setFont(fnt)
            painter.drawText(textRect, Qt.AlignLeft|Qt.AlignTop, font.name())

            # draw embedded status
            drawSize=True
            if font.embedded():
                text=i18n('Embedded')
            elif font.available():
                if font.embeddable():
                    text=i18n('Embeddable')
                else:
                    text=i18n('Not embeddable')
                    drawSize=False
            else:
                text=i18n('Not available')
                drawSize=False
            top+=height
            textRect=QRect(left + height, top, option.rect.width(), option.rect.bottom() - top)

            fnt=QFont(defaultFnt)
            fnt.setItalic(True)
            painter.setFont(fnt)
            painter.drawText(textRect, Qt.AlignLeft|Qt.AlignTop, text)

            if drawSize:
                textRect=QRect(left, top, option.rect.width() - 6, option.rect.bottom() - top)
                painter.drawText(textRect, Qt.AlignRight|Qt.AlignTop, font.fileSize(True))


            # draw used status
            if font.embedded() and not font.used():
                text=i18n('Not used (anymore) in document')
                top+=height
                textRect=QRect(left + height, top, option.rect.width(), option.rect.bottom() - top)
                fnt=QFont(defaultFnt)
                fnt.setItalic(True)
                painter.setFont(fnt)
                painter.drawText(textRect, Qt.AlignLeft|Qt.AlignTop, text)

            painter.restore()
            return

        QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        """Calculate size for items"""
        size = QStyledItemDelegate.sizeHint(self, option, index)

        # assume
        # > height for font name
        #   + 2*height for formatted font name
        #   + height for embeddable status
        #   + height for used status
        size.setHeight(size.height() * 5 + 4)
        size.setWidth(round(size.width() * 1.5 + 4))

        return size
