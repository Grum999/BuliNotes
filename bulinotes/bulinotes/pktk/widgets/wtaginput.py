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
# The wtaginput module provides an input tag widget manager
# standard color layer selector
#
# Main class from this module
#
# - WTagInput:
#       Widget
#       The main input widget
#
# - WTag:
#       Widget
#       A tag widget
#
# -----------------------------------------------------------------------------

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from ..modules.imgutils import buildIcon

from .wflowlayout import WFlowLayout
from .wlineedit import WLineEdit
from ..pktk import *


class WTag(QFrame):
    """A widget tag, used by WTagInput

        ┌───────┬───┐
        │ Text  │ X │
        └───────┴───┘

    """
    removeClicked = Signal(QWidget)

    __TOOLBUTTON_CSS = """
QToolButton {
    border-bottom-right-radius: 4px;
    border-top-right-radius: 4px;
}

QToolButton:hover {
    border: none;
    background-color: rgba(255,255,255,50);
}
QToolButton:disabled {
    padding-left: 100px;
}
        """

    __TOOLBUTTON_CSS_RO = """
QToolButton {
    border-bottom-right-radius: 4px;
    border-top-right-radius: 4px;
}
        """

    __TAG_CSS = """
WTag {
    border-radius: 4px;
    background-color: palette(light);
}
WTag:disabled {
    background-color: palette(mid);
}
        """

    __LABEL_CSS = """
QLabel {
    color: palette(text);
}
QLabel:disabled {
    color: palette(light);
}
        """

    def __init__(self, value, text=None, readOnly=False, parent=None):
        super(WTag, self).__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(4, 0, 0, 0)

        if not isinstance(value, str):
            raise EInvalidType("Given `value` must be <str>")
        elif not (isinstance(text, str) or text is None):
            raise EInvalidType("Given `text` must be <str> or None")

        self.__value = value

        if not isinstance(text, str):
            text = value

        self.__label = QLabel(text)
        self.__label.setStyleSheet(WTag.__LABEL_CSS)

        self.__btRemove = QToolButton()
        self.__btRemove.setToolTip(i18n('Remove tag'))
        self.__btRemove.setIcon(buildIcon('pktk:close'))
        self.__btRemove.setFocusPolicy(Qt.NoFocus)
        self.__btRemove.setAutoRaise(True)
        self.__btRemove.setStyleSheet(WTag.__TOOLBUTTON_CSS)
        self.__btRemove.setCursor(Qt.PointingHandCursor)
        self.__btRemove.clicked.connect(self.__removeClicked)

        self.__label.setMinimumHeight(self.__btRemove.minimumSizeHint().height())

        self.setStyleSheet(WTag.__TAG_CSS)

        layout.addWidget(self.__label)
        layout.addWidget(self.__btRemove)

        if readOnly:
            self.setReadOnly(readOnly)

        self.setLayout(layout)

    def __repr__(self):
        return f"<WTag({self.__value})>"

    def __readOnlyModeChanged(self, value):
        """Parent read only mode has been modified"""
        self.__btRemove.setVisible(value)

    def __removeClicked(self):
        """Emit signal"""
        self.removeClicked.emit(self)

    def value(self):
        """Return current tag value"""
        return self.__value

    def label(self):
        """Return current tag label"""
        return self.__label.text()

    def setReadOnly(self, value):
        """Set/Unset tag in read only mode"""
        if value:
            # read only
            # let the button here, change icon and deactivate things...
            #
            # there's might be more elegant wait to implement that but I'm lazy :-)
            self.__btRemove.setIcon(buildIcon('pktk:tag'))
            self.__btRemove.clicked.disconnect(self.__removeClicked)
            self.__btRemove.setCursor(Qt.ArrowCursor)
            self.__btRemove.setStyleSheet(WTag.__TOOLBUTTON_CSS_RO)
        else:
            # not read only
            self.__btRemove.setIcon(buildIcon('pktk:close'))
            self.__btRemove.clicked.connect(self.__removeClicked)
            self.__btRemove.setCursor(Qt.PointingHandCursor)
            self.__btRemove.setStyleSheet(WTag.__TOOLBUTTON_CSS)


class WTagPopupList(QFrame):
    """User interface for tags list selection"""
    tagChecked = Signal(str)
    tagUnchecked = Signal(str)

    def __init__(self, parent=None):
        super(WTagPopupList, self).__init__(None)
        self.__parent = parent

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setLineWidth(1)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        self.__modelTags = QStandardItemModel()
        self.__modelTags.itemChanged.connect(self.__itemChanged)
        self.__proxyModelTags = QSortFilterProxyModel()
        self.__proxyModelTags.setSourceModel(self.__modelTags)
        self.__proxyModelTags.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModelTags.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.__proxyModelTags.setDynamicSortFilter(True)
        self.__proxyModelTags.sort(0, Qt.AscendingOrder)
        self.__proxyModelTags.rowsInserted.connect(self.__updateListViewMinMaxHeight)
        self.__proxyModelTags.rowsRemoved.connect(self.__updateListViewMinMaxHeight)

        self.__lvTags = QListView()
        self.__lvTags.setModel(self.__proxyModelTags)
        self.__lvTags.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__lvTags.setUniformItemSizes(True)
        self.__lvTags.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        # min/max number of rows to display
        self.__optionMinNumberOfRows = -1
        self.__optionMaxNumberOfRows = -1

        self.setMinNumberOfRows(4)
        self.setMaxNumberOfRows(15)

        # widget content
        # set layout as "proteced": allows potential inherited class to update
        # layout content if needed
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(1,1,1,1)
        self._layout.addWidget(self.__lvTags)

        self.setFocusProxy(self.__parent)

        self.__parent.lineEdit().focusOut.connect(self.__lineEditFocusOut)

        self.setLayout(self._layout)

    def __itemChanged(self, item):
        """Item has been changed... emit signal for check/unchecked"""
        if item.checkState() == Qt.Checked:
            self.tagChecked.emit(item.data())
        else:
            self.tagUnchecked.emit(item.data())

    def __initialiseCurrentIndex(self, selectFirstItem=True):
        """Initialise current index to first position"""
        if selectFirstItem:
            index = self.__proxyModelTags.index(0, 0)
            if index.isValid():
                index = self.__proxyModelTags.mapToSource(index)
                self.__lvTags.setCurrentIndex(index)
        else:
            index = self.__proxyModelTags.index(-1, 0)
            self.__lvTags.setCurrentIndex(index)

    def __lineEditFocusOut(self):
        """LineEdit loose focus, need to check which widget got it

        If widget is not from popup or parent, then hide popup, otherwise keep popup visible (is visible)
        """
        if not(QApplication.focusWidget() == self or QApplication.focusWidget() == self.__parent or QApplication.focusWidget() == self.__parent.lineEdit() or QApplication.focusWidget() == self.__lvTags):
            self.hide()

    def __updateListViewMinMaxHeight(self):
        """Calculate and update min/max height for list view"""
        rowHeight = self.__lvTags.sizeHintForRow(0)

        if rowHeight <= 0:
            rowHeight = self.__lvTags.fontMetrics().height()

        # nbrows+1 => not sure, not digged problem, but if just use exact number of rows, last one is truncated...
        #             add one one is easier way to ensure last rows in not truncated when min < nb rows < max
        nbRows = max(min(self.__optionMaxNumberOfRows, self.__lvTags.model().rowCount()+1), self.__optionMinNumberOfRows)
        self.setMinimumHeight(nbRows*rowHeight)
        self.setMaximumHeight(nbRows*rowHeight)

        if self.__lvTags.model().rowCount() == 0:
            # no items in list, do not popup...
            self.hide()

    def eventFilter(self, object, event):
        """Filter keypress event from line edit"""
        processed = False
        if event.type() == QEvent.KeyPress:
            # event type is a key pressed, check which key has been pressed
            if event.key() == Qt.Key_Down:
                # key down: select next item in list
                index = self.__lvTags.currentIndex()
                if index.isValid():
                    row = min(index.row()+1, self.__proxyModelTags.rowCount()-1)
                else:
                    row = 0

                index = self.__proxyModelTags.index(row, 0)
                if index.isValid():
                    self.__lvTags.setCurrentIndex(index)
                processed = True
            elif event.key() == Qt.Key_Up:
                # key down: select previous item in list
                index = self.__lvTags.currentIndex()
                if index.isValid():
                    row = max(index.row()-1, 0)
                else:
                    row = 0

                index = self.__proxyModelTags.index(row, 0)
                if index.isValid():
                    self.__lvTags.setCurrentIndex(index)
                processed = True
            elif event.key() == Qt.Key_Escape:
                # close popup list
                self.hide()
                processed = True
            elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
                # enter/return key
                # if an item is selected in list, toggle checked state without
                # closing popup
                # otherwise let the line edit manage the pressed key
                index = self.__lvTags.currentIndex()
                if index.isValid():
                    index = self.__proxyModelTags.mapToSource(index)
                    item = self.__modelTags.item(index.row(),0)
                    if item:
                        self.selectTag(item.data(), not(item.checkState() == Qt.Checked))
                        processed = True
        return processed

    def showEvent(self, event):
        """Popup is visible, need to manage focus"""
        def init():
            # really dirty implementation
            # but didn't found any other method
            #
            # it seems as a widget is displayed as "window" (popup, ...)
            # management of focus is not really possible?
            # tried que QCompleter but in this case, not possible to Keep popup
            # opened once a choice is made in list (key pressed, mouse click...)
            #
            # so here the result...

            # try to define top widget from parent (WTagInput) as active
            self.__parent.activateWindow()
            self.__parent.setWindowState(Qt.WindowActive)

            # try to define parent (WTagInput) as focused
            self.__parent.raise_()
            self.__parent.setFocus(Qt.PopupFocusReason)

            # try to define line edit of parent (WTagInput) as focused
            self.__parent.lineEdit().setFocus(Qt.PopupFocusReason)
            # force line edit of parent (WTagInput) to grab keyboard
            self.__parent.lineEdit().grabKeyboard()
            # add event filter to let current widget being able to manage some case (key up, key down, ...)
            self.__parent.lineEdit().installEventFilter(self)
            # selection is important; don't know why but without it, there's no text cursor :-/
            # and even here, cursor is not blinking :-(
            self.__parent.lineEdit().setSelection(len(self.__parent.lineEdit().text()),1)

            self.__updateListViewMinMaxHeight()

        super(WTagPopupList, self).showEvent(event)
        # here dirty trick: seems to need to apply change in next event loop, then use a QTimer with dedaly to 0
        # dirty yes :-/
        QTimer.singleShot(0, init)

    def hideEvent(self, event):
        """Popup has been closed, need to release focus management"""
        super(WTagPopupList, self).hideEvent(event)
        self.__parent.lineEdit().releaseKeyboard()
        self.__parent.lineEdit().removeEventFilter(self)

    def minNumberOfRows(self):
        """Return minimum number of rows to display"""
        return self.__optionMinNumberOfRows

    def setMinNumberOfRows(self, value):
        """Set minimum number of rows to display"""
        if isinstance(value, int) and value != self.__optionMinNumberOfRows and value >= 0:
            self.__optionMinNumberOfRows = value

            if self.__optionMinNumberOfRows > self.__optionMaxNumberOfRows:
                self.__optionMaxNumberOfRows = self.__optionMinNumberOfRows

            self.__updateListViewMinMaxHeight()

    def maxNumberOfRows(self):
        """Return maximum number of rows to display"""
        return self.__optionMaxNumberOfRows

    def setMaxNumberOfRows(self, value):
        """Set maximum number of rows to display"""
        if isinstance(value, int) and value != self.__optionMaxNumberOfRows and value >= 0:
            self.__optionMaxNumberOfRows = value

            if self.__optionMaxNumberOfRows < self.__optionMinNumberOfRows:
                self.__optionMinNumberOfRows = self.__optionMaxNumberOfRows

            self.__updateListViewMinMaxHeight()

    def filter(self, value=None):
        """Filter tags matching given `value`"""
        if isinstance(value, str) and value.strip() != '':
            value = QRegularExpression.escape(value)
            self.__proxyModelTags.setFilterRegExp(value)
        else:
            # no filter
            self.__proxyModelTags.setFilterRegExp("")

    def updatePopupPosition(self):
        """Update current popup position"""
        self.setMinimumWidth(self.__parent.width())

        # display under parent
        screenPosition = self.__parent.mapToGlobal(QPoint(0,self.__parent.height()))
        checkPosition = QPoint(screenPosition)

        # need to ensure popup is not "outside" visible screen
        for screen in QGuiApplication.screens():
            screenRect = screen.availableGeometry()
            if screenRect.contains(checkPosition):
                # we're on the right screen
                # need to check if window if displayed properly in screen
                relativePosition = screenPosition - screenRect.topLeft()

                if screenPosition.x() < screenRect.left():
                    screenPosition.setX(screenRect.left())
                elif screenPosition.x() + self.width() > screenRect.right():
                    screenPosition.setX(screenRect.right() - self.width())

                if screenPosition.y() < screenRect.top():
                    screenPosition.setY(screenRect.top())
                elif screenPosition.y() + self.height() > screenRect.bottom():
                    screenPosition.setY(screenRect.bottom() - self.height())

        if screenPosition.y() < checkPosition.y():
            screenPosition.setY(self.__parent.mapToGlobal(QPoint(0,-self.height())).y())

        self.move(screenPosition)

    def popup(self, selectFirstItem=True):
        """Show popup using given `widget` as reference for position"""
        self.__updateListViewMinMaxHeight()
        self.updatePopupPosition()
        self.show()
        self.__initialiseCurrentIndex(selectFirstItem)

    def clear(self):
        """Clear all items"""
        self.__modelTags.clear()

    def addTag(self, tagValue, tagLabel=None, selected=False):
        """add a tag to list"""
        if tagLabel is None:
            tagLabel = tagValue

        if not isinstance(tagLabel, str):
            raise EInvalidType("Given `tagLabel` must be <str>")

        item = QStandardItem(tagLabel)
        item.setData(tagValue)
        item.setCheckable(True)
        if selected:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

        self.__modelTags.appendRow(item)

    def removeTag(self, tagValue):
        """Remove tag designed by `tagValue` from list"""
        for index in range(self.__modelTags.rowCount()):
            item = self.__modelTags.item(index)
            if item.data() == tagValue:
                self.__modelTags.removeRow(index)
                return True

        return False

    def selectTag(self, tagValue, selected=True):
        """Select tag designed `tagValue`

        If `selected` is True, tag is checked, otherwise is unchecked
        """
        for index in range(self.__modelTags.rowCount()):
            item = self.__modelTags.item(index)
            if item.data() == tagValue:
                if selected:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                return True
        return False

    def isSelectTag(self, tagValue):
        """Return if tag designed by `tagValue` is selected

        If `selected` is True, tag is checked, otherwise is unchecked
        """
        for index in range(self.__modelTags.rowCount()):
            item = self.__modelTags.item(index)
            if item.data() == tagValue:
                return item.checkState() == Qt.Checked
        return False

    def selectedTags(self):
        """Return list of selected tags"""
        returned = []
        for index in range(self.__modelTags.rowCount()):
            item = self.__modelTags.item(index)
            if item.checkState() == Qt.Checked:
                returned.append(item.data())
        return returned



class WTagInput(QWidget):
    """A widget to manage tags inputs"""
    tagAdded = Signal(WTag)               # A tag has been added to list
    tagRemoved = Signal(WTag)             # A tag has been removed from list
    tagCreated = Signal(WTag)             # A new tag has been created (added to tag list)
    tagSelection = Signal()

    ACCEPT_NEWTAG_NO=   0b00000001  # do not accept tags that are not in available tags list
    ACCEPT_NEWTAG_YES=  0b00000010  # accept tags that are not in available tags list
    ACCEPT_NEWTAG_ADD=  0b00000110  # accept tags that are not in available tags list and add them to available list automatically

    __TOOLBUTTON_CSS = """
QToolButton {
    padding: 0;
    margin: 0;
    background-color: transparent;
}

QToolButton:hover {
    border: none;
    border-radius: 4px;
    background-color: palette(light);
}
        """

    def __init__(self, parent=None):
        super(WTagInput, self).__init__(parent)

        # widget layouts
        self.__layout = WFlowLayout()
        self.__layout.setContentsMargins(3,4,3,4)       # also change setReadOnly if margins are changed

        # input layout
        self.__layoutInput = QHBoxLayout()
        self.__layoutInput.setContentsMargins(0,0,0,0)
        self.__layoutInput.setSpacing(0)

        self.__layout.addLayout(self.__layoutInput)

        self.__lineEdit = WLineEdit()
        self.__lineEdit.setStyleSheet("border: none;")
        self.__lineEdit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.__lineEdit.focusIn.connect(self.update)
        self.__lineEdit.focusOut.connect(self.update)
        self.__lineEdit.textEdited.connect(self.__popupFilter)
        self.__lineEdit.keyPressed.connect(self.__keyPressed)

        self.__buttonTags = QToolButton()
        self.__buttonTags.setToolTip(i18n('Tags list'))
        self.__buttonTags.setIcon(buildIcon('pktk:tags'))
        self.__buttonTags.setFocusPolicy(Qt.NoFocus)
        self.__buttonTags.setAutoRaise(True)
        self.__buttonTags.setStyleSheet(WTagInput.__TOOLBUTTON_CSS)
        self.__buttonTags.setCursor(Qt.PointingHandCursor)
        self.__buttonTags.clicked.connect(lambda: self.__popupFilter())

        self.__layoutInput.addWidget(self.__lineEdit)
        self.__layoutInput.addWidget(self.__buttonTags)

        self.__isDefaultPopup = True
        self.__tagPopupList = WTagPopupList(self)
        self.__tagPopupList.tagChecked.connect(self.addSelectedTag)
        self.__tagPopupList.tagUnchecked.connect(self.removeSelectedTag)

        # dictionnary of possible tags values
        self.__availableTagList = {}

        # list of current selected tags (list of WTag)
        self.__selectedTags = []

        # If true, accept provided values even if not available in tag list
        self.__optionAcceptNewTags = WTagInput.ACCEPT_NEWTAG_NO

        # If true, automatically sort tags (note: tags list from popup is always sorted)
        self.__optionAutoSort = True

        # If true, user input (text value) is case sensitive
        # Example:
        #   value = 'test1'
        #   text = 'Test value 1'
        #
        # if __optionCaseSensitive is True:
        #   - User input "Test value 1" => return value "test1"
        #   - User input "test value 1" => return value "test value 1"
        #
        # if __optionCaseSensitive is False:
        #   - User input "Test Value 1" => return value "test1"
        #   - User input "test value 1" => return value "test1"
        self.__optionCaseSensitive = False

        # determiante if widget is in read-only mode
        # note that read only is not the same than "disabled"
        # in read only mode, widget look is not the same, looks like more to an
        # information panel than a input widget
        self.__isReadOnly = False

        # mass updates actions
        self.__inMassUpdate = 0
        self.__inSortUpdate = False
        self.__needToSort = False

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.__lineEdit)
        self.setLayout(self.__layout)

    def __cleanupTags(self):
        """Update selected tags: remove all tags that are not in available tags list"""
        self.__startMassUpdate()
        self.__stopMassUpdate()

    def __startMassUpdate(self):
        """Start a mass update"""
        self.__inMassUpdate += 1

    def __stopMassUpdate(self):
        """Stop a mass update"""
        self.__inMassUpdate -= 1
        if self.__inMassUpdate <= 0:
            self.__inMassUpdate = 0
            if self.__needToSort:
                self.sortSelectedTags()

    def __isInMassUpdate(self):
        """Return true is currently in a mass update"""
        return self.__inMassUpdate > 0

    def __addFromLineEdit(self):
        """Add current value from LineEdit"""
        value = self.__lineEdit.text()
        if value.strip() == '':
            self.__tagPopupList.popup()
            return

        # assume that, from line edit, user provide Text instead of value
        # need to check for value associated to text
        found = False
        for tagValue in self.__availableTagList:
            if self.__optionCaseSensitive:
                if self.__availableTagList[tagValue] == value:
                    # found value from text
                    value = tagValue
                    found = True
                    break
            elif self.__availableTagList[tagValue].lower() == value.lower():
                    # found value from text
                    value = tagValue
                    found = True
                    break

        if not found and self.__optionAcceptNewTags&WTagInput.ACCEPT_NEWTAG_YES == WTagInput.ACCEPT_NEWTAG_YES:
            # didn't found value from text
            # but accept text for which value is not defined
            found = True

        if found and self.addSelectedTag(value):
            self.__tagPopupList.selectTag(value)
            self.__lineEdit.clear()
            self.__tagPopupList.filter()

    def __removeWTag(self, wtag, indexList=None):
        """Remove widget tag"""
        if indexList is None:
            for index, widgetTag in enumerate(self.__selectedTags):
                if widgetTag.value() == wtag.value():
                    indexList = index
                    break

        self.__selectedTags.pop(indexList)
        self.__tagPopupList.selectTag(wtag.value(), False)

        indexLayout = self.__layout.indexOf(wtag)
        item = self.__layout.takeAt(indexLayout)

        widget = item.widget()
        widget.setVisible(False)
        widget.setParent(None)
        del widget
        del item

        if not self.__isInMassUpdate():
            self.__layout.update()

        return True

    def __addFromCompleter(self, tagValue):
        """Tag is added from completer"""
        # clear line edit in this case
        self.__lineEdit.clear()

    def __popupFilter(self, filterText=None, selectFirstItem=False):
        """Display tags popup list and filter values"""
        if filterText is None or filterText == '':
            filterText = self.__lineEdit.text()

        self.__tagPopupList.filter(filterText.strip())
        self.__tagPopupList.popup(selectFirstItem)

    def __keyPressed(self, event, textAfter, textBefore):
        """Key has been pressed in line edit"""
        focused = False
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if textAfter == '':
                self.__popupFilter("", True)
            else:
                self.__addFromLineEdit()
        elif event.key() == Qt.Key_Down:
            self.__popupFilter(self.__lineEdit.text(), self.__lineEdit.text() == '')
        elif event.key() == Qt.Key_Backspace and textBefore == '' and len(self.__selectedTags):
            self.removeSelectedTag(self.__selectedTags[-1].value())

    def eventFilter(self, object, event):
        """ *** """
        if event.type() in (QEvent.MouseButtonRelease, QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
            self.__lineEdit.setFocus()
        return False

    def sizeHint(self):
        return self.__lineEdit.sizeHint()

    def lineEdit(self):
        """Return line edit used by WInputTag"""
        return self.__lineEdit

    def resizeEvent(self, event):
        """Widget has been resized"""
        self.__tagPopupList.updatePopupPosition()

    def paintEvent(self, event):
        """Paint widget

        Mainly, paint borders..
        """
        if not self.__isReadOnly:
            painter = QPainter(self)

            option = QStyleOptionFrame()
            option.initFrom(self.__lineEdit)
            option.rect = self.contentsRect()
            option.lineWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth, option, self.__lineEdit)
            option.midLineWidth = 0
            option.state |= QStyle.State_Sunken

            self.style().drawPrimitive(QStyle.PE_PanelLineEdit, option, painter, self.__lineEdit)
        else:
            super(WTagInput, self).paintEvent(event)

    def minNumberOfRows(self):
        """Return minimum number of rows to display"""
        return self.__tagPopupList.minNumberOfRows()

    def setMinNumberOfRows(self, value):
        """Set minimum number of rows to display"""
        self.__tagPopupList.setMinNumberOfRows(value)

    def maxNumberOfRows(self):
        """Return maximum number of rows to display"""
        return self.__tagPopupList.maxNumberOfRows()

    def setMaxNumberOfRows(self, value):
        """Set maximum number of rows to display"""
        self.__tagPopupList.setMaxNumberOfRows(value)

    def popup(self):
        """Return instance of popup widget"""
        return self.__tagPopupList

    def setPopup(self, value):
        """Set instance of popup widget to use

        Must be a WTagPopupList
        Provide None to reapply default popup

        Note
        """
        if isinstance(value, WTagPopupList) and value != self.__tagPopupList:
            self.__isDefaultPopup = False
            # disconnect current signals
            self.__tagPopupList.tagChecked.disconnect(self.addSelectedTag)
            self.__tagPopupList.tagUnchecked.disconnect(self.removeSelectedTag)

            # affect new popup widget
            self.__tagPopupList = value

            # reconnect signals
            self.__tagPopupList.tagChecked.connect(self.addSelectedTag)
            self.__tagPopupList.tagUnchecked.connect(self.removeSelectedTag)

            # repopulate available tags
            selectedTags = self.selectedTags()
            for tagId in self.__availableTagList:
                self.__tagPopupList.addTag(tagId, self.__availableTagList[tagId], tagId in selectedTags)
        elif value is None and not self.__isDefaultPopup:
            self.__isDefaultPopup = True
            # disconnect current signals
            self.__tagPopupList.tagChecked.disconnect(self.addSelectedTag)
            self.__tagPopupList.tagUnchecked.disconnect(self.removeSelectedTag)

            # affect new popup widget
            self.__tagPopupList = WTagPopupList(self)

            # reconnect signals
            self.__tagPopupList.tagChecked.connect(self.addSelectedTag)
            self.__tagPopupList.tagUnchecked.connect(self.removeSelectedTag)

            selectedTags = self.selectedTags()
            # repopulate available tags
            for tagId in self.__availableTagList:
                self.__tagPopupList.addTag(tagId, self.__availableTagList[tagId], tagId in selectedTags)

    def readOnly(self):
        """Return if read only mode is active or not"""
        return self.__isReadOnly

    def setReadOnly(self, value):
        """Set if read only mode is active or not"""
        if isinstance(value, bool) and value != self.__isReadOnly:
            self.__isReadOnly = value

            self.__layoutInput.setEnabled(not self.__isReadOnly)
            self.__lineEdit.setVisible(not self.__isReadOnly)
            self.__buttonTags.setVisible(not self.__isReadOnly)

            if self.__isReadOnly:
                self.__layout.setContentsMargins(0,0,0,0)
            else:
                self.__layout.setContentsMargins(3,4,3,4)

            for tag in self.__selectedTags:
                tag.setReadOnly(self.__isReadOnly)

            self.update()

    def autoSort(self):
        """Return if automatic sort is active or not"""
        return self.__optionAutoSort

    def setAutoSort(self, value):
        """Set if automatic sort is active or not"""
        if isinstance(value, bool) and value != self.__optionAutoSort:
            self.__optionAutoSort = value
            if self.__optionAutoSort:
                self.sortSelectedTags()

    def caseSensitive(self):
        """Return if user input is case sensitive"""
        return self.__optionCaseSensitive

    def setCaseSensitive(self, value):
        """Set if user input is case sensitive"""
        if isinstance(value, bool) and value != self.__optionCaseSensitive:
            self.__optionCaseSensitive = value

    def acceptNewTags(self):
        """Return if tags not available in default tag list can be added or not"""
        return self.__optionAcceptNewTags

    def setAcceptNewTags(self, value):
        """Set if tags not available in default tag list can be added or not"""
        if value in (WTagInput.ACCEPT_NEWTAG_NO, WTagInput.ACCEPT_NEWTAG_YES, WTagInput.ACCEPT_NEWTAG_ADD) and value != self.__optionAcceptNewTags:
            self.__optionAcceptNewTags = value
            if self.__optionAcceptNewTags == WTagInput.ACCEPT_NEWTAG_NO:
                self.__cleanupTags()

    def sortSelectedTags(self):
        """Sort tags values by their text"""
        if self.__inSortUpdate:
            return
        elif self.__isInMassUpdate():
            self.__needToSort = True
            return

        self.__inSortUpdate = True
        selectedTagsSorted = sorted([tag.value() for tag in self.__selectedTags], key=lambda v: self.__availableTagList[v].lower() if v in self.__availableTagList else v.lower())

        self.setSelectedTags(selectedTagsSorted)
        self.__layout.update()
        self.__needToSort = False
        self.__inSortUpdate = False

    def clearSelectedTags(self):
        """Clear all selected tags"""
        self.__startMassUpdate()

        while len(self.__selectedTags):
            self.__removeWTag(self.__selectedTags[0], 0)

        self.__stopMassUpdate()

    def availableTags(self):
        """Return list of available tags

        List items are tuples (value, text)
        """
        return list(self.__availableTagList.keys())

    def setAvailableTags(self, values):
        """Set list of available tags

        Given `values` is list of:
        - tuples (value, text)
        - str (value)   ==> in this case, value is used as text
        """
        if not isinstance(values, list):
            raise EInvalidType("Given `values` must be a <list>")

        self.__startMassUpdate()
        self.clearSelectedTags()
        self.__availableTagList = {}
        for value in values:
            self.addAvailableTag(value)

        self.__stopMassUpdate()

    def addAvailableTag(self, value):
        """Add a tag in available list tags

        Given `value` is:
        - a tuple (value, text)
        - a str (value)   ==> in this case, value is used as text

        If a tags already exist for given value, it won't be added
        """
        if isinstance(value, str):
            # need a tuple
            value = (value, value)

        if not(isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], str)):
            # not a valid tuple, do nothing
            return False

        if value[0] in self.__availableTagList:
            # value already exists
            return False

        self.__availableTagList[value[0]] = value[1]
        self.__tagPopupList.addTag(value[0], value[1])

        return True

    def removeAvailableTag(self, value):
        """remove a tag in available list tags, if exist

        Given `value` is a <str>

        If tag doesn't exist for given value, does nothing
        """
        if isinstance(value, str) and value in self.__availableTagList:
            self.__availableTagList.pop(value)
            self.__tagPopupList.removeTag(value)

            if not self.__isInMassUpdate():
                pass
            return True
        return False

    def selectedTags(self):
        """Return list of selected tags

        List items are str (values)
        """
        return [tag.value() for tag in self.__selectedTags]

    def setSelectedTags(self, values):
        """Set list of selected tags

        List items are str (values)
        """
        self.__startMassUpdate()
        self.clearSelectedTags()

        for value in values:
            self.addSelectedTag(value)

        self.__stopMassUpdate()

    def addSelectedTag(self, value):
        """Add a tag in selected list tags

        Given `value` is a str (value or text)
        """
        if not isinstance(value, str):
            # not a valid value
            raise EInvalidType("Given `value` must be <str>")
        elif not(value in self.__availableTagList or self.__optionAcceptNewTags&WTagInput.ACCEPT_NEWTAG_YES == WTagInput.ACCEPT_NEWTAG_YES):
            # value must exist in available list or option __optionAcceptNewTags must be True
            return False

        for widgetTag in self.__selectedTags:
            if value == widgetTag.value():
                # value is already selected, can't select it again
                return False

        if value in self.__availableTagList:
            tag = WTag(value, self.__availableTagList[value], self.__isReadOnly)
        else:
            tag = WTag(value, value, self.__isReadOnly)

        tag.removeClicked.connect(self.__removeWTag)
        self.__layout.insertWidget(self.__layout.count()-1, tag)
        self.__selectedTags.append(tag)
        self.__tagPopupList.selectTag(value, True)

        if not value in self.__availableTagList and self.__optionAcceptNewTags&WTagInput.ACCEPT_NEWTAG_ADD == WTagInput.ACCEPT_NEWTAG_ADD:
            self.addAvailableTag(value)

        if self.__optionAutoSort:
            self.sortSelectedTags()

        self.tagSelection.emit()

        return True

    def removeSelectedTag(self, value):
        """remove a tag from selected list tags, if selected

        Given `value` is a <str>

        If tag doesn't exist for given value, does nothing
        """
        wtag = None
        index = -1

        if isinstance(value, str):
            for index, widgetTag in enumerate(self.__selectedTags):
                if widgetTag.value() == value:
                    wtag = widgetTag
                    break

        if wtag and index > -1:
            return self.__removeWTag(wtag, index)

        self.tagSelection.emit()

        return True
