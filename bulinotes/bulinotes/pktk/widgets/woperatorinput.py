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
# The woperatorinput module provides a set of widget to easily manage operator
# inputs like =, >=, <=, ...
#
# Main class from this module
#
# - WOperatorBaseInput:
#       Widget
#       The base widget used to defined an operator input
#
# - WOperatorInputInt:
#       Widget
#       Manage input integer widget
#
# - WOperatorInputFloat:
#       Widget
#       Manage input float widget
#
# - WOperatorInputDateTime:
#       Widget
#       Manage input date/time widget
#
# - WOperatorInputDate:
#       Widget
#       Manage input date widget
#
# - WOperatorInputTime:
#       Widget
#       Manage input time widget
#
# - WOperatorInputStr:
#       Widget
#       Manage input string widget
#
# - WOperatorInputList:
#       Widget
#       Manage input list widget
#
# -----------------------------------------------------------------------------

import re
from enum import Enum

from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )

from ..modules.utils import replaceLineEditClearButton
from ..modules.imgutils import buildIcon
from .wtaginput import WTagInput


STYLE_DROPDOWN_BUTTON_CALENDAR = """
::drop-down {
        margin: 0px;
        border: 0px solid rgb(255,0,255);
        background: rgba(0,0,0,0);
    }

::down-arrow {
        image: url(:/pktk/images/normal/calendar_month);
        background: rgba(0,0,0,0);
        border: 0px solid rgba(0,0,255,128);
        margin:0px;
        padding:0px;
        left:1px;
    }
::down-arrow:disabled {
        image: url(:/pktk/images/disabled/calendar_month);
    }
"""


class WOperatorType:
    OPERATOR_GT =          '>'
    OPERATOR_GE =          '>='
    OPERATOR_LT =          '<'
    OPERATOR_LE =          '<='
    OPERATOR_EQ =          '='
    OPERATOR_NE =          '!='
    OPERATOR_BETWEEN =     'between'
    OPERATOR_NOT_BETWEEN = 'not between'
    OPERATOR_MATCH =       'match'
    OPERATOR_NOT_MATCH =   'not match'
    OPERATOR_LIKE =        'like'
    OPERATOR_NOT_LIKE =    'not like'
    OPERATOR_IN =          'in'
    OPERATOR_NOT_IN =      'not in'


class WOperatorCondition:
    """A condition defition that can be used to define predefined conditions"""

    @staticmethod
    def fromFmtString(value, converter=None):
        """Return a WOperatorCondition from a formatted string

        If `value` given as string can't be parsed, return None

        string format:
        (label)//(operator)//(value)//(value2)

        values:
            's:XXXX' ==> string 'XXXX'
            'i:9999' ==> integer 9999
            'f:9.99' ==> float 9.99
            'l:s:X1;;s:X2' ==> list ['X1', 'X2']

        if `converter` is provided, must be a callable with 2 parameters:
            x(value, input)
                => value: the value to convert
                => input: the WOperatorBaseInput instance for which value will be set
        """
        def parsedValue(parameter):
            if len(parameter) > 2:
                if parameter[0] == 's':
                    return parameter[2:].replace('^/^/', '//')
                elif parameter[0] == 'i':
                    return int(parameter[2:])
                elif parameter[0] == 'f':
                    return float(parameter[2:])
                elif parameter[0] == 'l':
                    return [parsedValue(v) for v in parameter[2:].split(';;')]
            else:
                return None

        if not isinstance(value, str):
            raise EInvalidType("Given `value` must be <str>")

        parameters = value.split('//')
        if len(parameters) < 3:
            raise EInvalidValue("Given `value` can't be parsed")

        if len(parameters) == 3:
            parameters.append(parameters[2])

        return WOperatorCondition(parameters[0], parameters[1], parsedValue(parameters[2]), parsedValue(parameters[3]), converter)

    def __init__(self, label, operator, value, value2=None, converter=None):
        self.__label = label
        self.__operator = operator
        self.__value = value
        self.__value2 = value2
        self.__converter = None
        if callable(converter):
            self.__converter = converter

    def __toStr(self, value):
        if isinstance(value, str):
            return f"s:{value.replace('//', '^/^/').replace(';;', '^;^;')}"
        elif isinstance(value, float):
            return f"f:{value}"
        elif isinstance(value, int):
            return f"i:{value}"
        elif isinstance(value, list):
            return f"l:{';;'.join([self.__toStr(v) for v in value])}"

    def label(self):
        return self.__label

    def operator(self):
        return self.__operator

    def value(self):
        return self.__value

    def value2(self):
        return self.__value2

    def converter(self):
        return self.__converter

    def asFmtString(self):
        """Return as formatted string"""
        returned = [self.__label, self.__operator, self.__toStr(self.__value)]
        if self.__value2 is not None:
            returned.append(self.__toStr(self.__value2))

        return "//".join(returned)


class WOperatorBaseInput(QWidget):
    """A widget to define search condition using operator

    Class <WOperatorBaseInput> is ancestor for:
    - WOperatorInputInt
    - WOperatorInputFloat
    - WOperatorInputStr
    - WOperatorInputList
    - WOperatorInputDate
    - WOperatorInputTime
    - WOperatorInputDateTime

             | int   |     |      |      | date |      |
    Operator | float | str | date | time | time | list |
    ---------+-------+-----+------+------+------+------+
    >        |   x   |     |  x   |  x   |  x   |      |
    >=       |   x   |     |  x   |  x   |  x   |      |
    <        |   x   |     |  x   |  x   |  x   |      |
    <=       |   x   |     |  x   |  x   |  x   |      |
    =        |   x   |  x  |  x   |  x   |  x   |      |
    !=       |   x   |  x  |  x   |  x   |  x   |      |
    between  |   x   |     |  x   |  x   |  x   |      |
    !between |   x   |     |  x   |  x   |  x   |      |
    match    |       |  x  |      |      |      |      |
    !match   |       |  x  |      |      |      |      |
    like     |       |  x  |      |      |      |      |
    !like    |       |  x  |      |      |      |      |
    in       |       |     |      |      |      |  x   |
    !in      |       |     |      |      |      |  x   |
             |       |     |      |      |      |      |

    According to searched type:

                                       (for between operator)
                QComboBox   Input*     Input*
                <-------->  <--------> <---------------->      *Input

                +--------+  +--------+         +--------+
    int         |       V|  |      <>|     and |      <>|      QSpinBox
                +--------+  +--------+         +--------+

                +--------+  +--------+         +--------+
    float       |       V|  |      <>|     and |      <>|      QDoubleSpinBox
                +--------+  +--------+         +--------+

                +--------+  +--------+
    str         |       V|  |        |                         QLineEdit
                +--------+  +--------+

                +--------+  +--------+         +--------+
    date        |       V|  |      <>|     and |      <>|      QDateEdit
                +--------+  +--------+         +--------+

                +--------+  +--------+         +--------+
    time        |       V|  |      <>|     and |      <>|      QTimeEdit
                +--------+  +--------+         +--------+

                +--------+  +--------+         +--------+
    date/time   |       V|  |      <>|     and |      <>|      QDateTimeEdit
                +--------+  +--------+         +--------+

                +--------+  +--------+
    list        |       V|  |       +|                         WTagInput
                +--------+  +--------+

    """
    operatorChanged = Signal(str)
    valueChanged = Signal(object)
    value2Changed = Signal(object)

    __LABELS = {
            WOperatorType.OPERATOR_GT:          '>',
            WOperatorType.OPERATOR_GE:          '≥',
            WOperatorType.OPERATOR_LT:          '<',
            WOperatorType.OPERATOR_LE:          '≤',
            WOperatorType.OPERATOR_EQ:          '=',
            WOperatorType.OPERATOR_NE:          '≠',
            WOperatorType.OPERATOR_BETWEEN:     i18n('between'),
            WOperatorType.OPERATOR_NOT_BETWEEN: i18n('not between'),
            WOperatorType.OPERATOR_MATCH:       i18n('match'),
            WOperatorType.OPERATOR_NOT_MATCH:   i18n('not match'),
            WOperatorType.OPERATOR_LIKE:        i18n('like'),
            WOperatorType.OPERATOR_NOT_LIKE:    i18n('not like'),
            WOperatorType.OPERATOR_IN:          i18n('in'),
            WOperatorType.OPERATOR_NOT_IN:      i18n('not in'),
        }

    @staticmethod
    def operatorLabel(operator):
        """Return label for operator"""
        if operator in WOperatorBaseInput.__LABELS:
            return WOperatorBaseInput.__LABELS[operator]
        return f"{operator}"

    def __init__(self, parent=None):
        super(WOperatorBaseInput, self).__init__(parent)
        self._inInit = True

        self.__predefinedConditionsSubMenu = None
        self.__predefinedConditions = []
        self.__predefinedConditionsLabel = i18n("Predefined conditions")

        self._defaultOperatorList = []
        self._checkRangeValue = True

        self.__layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setDirection(QBoxLayout.LeftToRight)

        self._cbOperatorList = QComboBox()
        self._cbOperatorList.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self._cbOperatorList.currentIndexChanged.connect(self.__operatorChanged)

        self._input1 = QWidget()
        self._input2 = QWidget()
        self._lblAnd = QLabel(i18n('and'))
        self._lblAnd.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        # initialise UI
        self._initializeUi()

        # keep a pointer to original contextMenuEvent method
        self._input1._contextMenuEvent = self._input1.contextMenuEvent
        self._input2._contextMenuEvent = self._input2.contextMenuEvent

        # define dedicated contextMenuEvent method to manage suffix
        self._input1.contextMenuEvent = self.__contextMenuEvent1
        self._input2.contextMenuEvent = self.__contextMenuEvent2

        self.__layout.addWidget(self._cbOperatorList)
        self.__layout.addWidget(self._input1)
        self.__layout.addWidget(self._lblAnd)
        self.__layout.addWidget(self._input2)

        self.__layout.setAlignment(self._cbOperatorList, Qt.AlignTop)
        self.__layout.setAlignment(self._input1, Qt.AlignTop)
        self.__layout.setAlignment(self._lblAnd, Qt.AlignVCenter)
        self.__layout.setAlignment(self._input2, Qt.AlignTop)

        self.setLayout(self.__layout)
        self._inInit = False

    def _initOperator(self, values):
        """Initialise operator combox box from given list"""
        self._inInit = True
        self._cbOperatorList.clear()
        for operator in values:
            self._cbOperatorList.addItem(WOperatorBaseInput.__LABELS[operator], operator)
        self._inInit = False

    def _input1Changed(self, value=None):
        """Value for input1 has changed"""
        pass

    def _input2Changed(self, value=None):
        """Value for input2 has changed"""
        pass

    def __operatorChanged(self, index):
        """Operator value has been changed"""
        self._operator = self._cbOperatorList.currentData()

        input2Visible = (self._operator in [WOperatorType.OPERATOR_BETWEEN, WOperatorType.OPERATOR_NOT_BETWEEN])

        self._lblAnd.setVisible(input2Visible)
        self._input2.setVisible(input2Visible)
        self._input2.setEnabled(input2Visible)

        if self._inInit:
            return

        self.operatorChanged.emit(self._operator)

    def _initializeUi(self):
        """Implemented by sub classes to initialise interface"""
        raise EInvalidStatus("Method '_initialize' must be overrided by sub-classes")

    def __contextMenuEvent1(self, event):
        """Manage context menu event for input 1"""
        self._contextMenuEvent(self._input1, event)

    def __contextMenuEvent2(self, event):
        """Manage context menu event for input 2"""
        self._contextMenuEvent(self._input2, event)

    def _contextMenuEvent(self, input, event, display=True):
        """Display context menu for given input

        If suffix list is not empty, add action to select a suffix
        """
        def applyCondition(condition):
            # apply condition...
            self.setOperator(condition.operator())
            if condition.converter() is None:
                self.setValue(condition.value())
                self.setValue2(condition.value2())
            else:
                converter = condition.converter()

                self.setValue(converter(condition.value(), self))
                self.setValue2(converter(condition.value2(), self))

        def executeAction(action):
            if action.data():
                data = action.data()
                # data=tuple (function, parameter)
                data[0](data[1])

        if isinstance(input, QLineEdit):
            menu = input.createStandardContextMenu()
        elif isinstance(input, (QSpinBox, QDoubleSpinBox, QDateEdit)):
            menu = input.lineEdit().createStandardContextMenu()
        elif isinstance(input, WTagInput):
            menu = input.lineEdit().createStandardContextMenu()
        else:
            menu = QMenu()

        if len(menu.actions()) > 0:
            fAction = menu.actions()[0]
        else:
            fAction = None

        if len(self.__predefinedConditions) == 0 and display:
            input._contextMenuEvent(event)
            return
        elif len(self.__predefinedConditions) > 0:
            self.__predefinedConditionsSubMenu = QMenu(self.__predefinedConditionsLabel)
            for predefinedCondition in self.__predefinedConditions:
                action = None
                if isinstance(predefinedCondition, WOperatorCondition):
                    action = self.__predefinedConditionsSubMenu.addAction(predefinedCondition.label())
                    action.setData((applyCondition, predefinedCondition))

            if fAction is not None:
                menu.insertMenu(fAction, self.__predefinedConditionsSubMenu)
                menu.insertSeparator(fAction)
            else:
                menu.addMenu(self.__predefinedConditionsSubMenu)

        menu.triggered.connect(executeAction)
        if display:
            menu.exec(event.globalPos())
            return None
        else:
            return menu

    def operator(self):
        """Return current operator"""
        return self._operator

    def setOperator(self, value):
        """Set current operator"""
        if value == self._cbOperatorList.currentData():
            return

        for index in range(self._cbOperatorList.count()):
            if self._cbOperatorList.itemData(index) == value:
                self._cbOperatorList.setCurrentIndex(index)

    def value(self):
        """Return current value"""
        pass

    def setValue(self, value):
        """set current value"""
        pass

    def value2(self):
        """Return current 2nd value (when 'between' operator)"""
        pass

    def setValue2(self, value):
        """Set current 2nd value (when 'between' operator)"""
        pass

    def orientation(self):
        """Return current layout orientation"""
        if self.__layout.direction() in (QBoxLayout.LeftToRight, QBoxLayout.RightToLeft):
            return Qt.Horizontal
        else:
            return Qt.Vertical

    def setOrientation(self, value):
        """Set current layout orientation"""
        if value == Qt.Horizontal:
            self.__layout.setDirection(QBoxLayout.LeftToRight)
        else:
            self.__layout.setDirection(QBoxLayout.TopToBottom)

    def operators(self):
        """Return list of available operators"""
        return [self._cbOperatorList.itemData(index) for index in range(self._cbOperatorList.count())]

    def setOperators(self, operators=None):
        """Define list of available operators

        If `operators` is None or empty list, reset to default operators for widget
        """
        validList = []
        if isinstance(operators, list):
            validList = [operator for operator in operators if operator in self._defaultOperatorList]

        if operators is None or len(validList) == 0:
            validList = self._defaultOperatorList

        self._initOperator(validList)
        self.setOperator(self._operator)

    def operatorEnabled(self):
        """Return if the operator is enabled or not"""
        return self._cbOperatorList.isEnabled()

    def setOperatorEnabled(self, value):
        """Set if the operator is enabled or not"""
        self._cbOperatorList.setEnabled(value)

    def checkRangeValues(self):
        """Return if range values are checked or not"""
        return self._checkRangeValue

    def setCheckRangeValues(self, value):
        """Set if range values are checked or not"""
        if isinstance(value, bool) and value != self._checkRangeValue:
            self._checkRangeValue = value
            if self._checkRangeValue:
                self._input1Changed()

    def predefinedConditions(self):
        """Return list of predefined values

        Each item is a tuple (label, condition)
        """
        return self.__predefinedConditions

    def setPredefinedConditions(self, values):
        """Set list of predefined values

        Each item is a WOperatorCondition
        """
        self.__predefinedConditions = []
        for value in values:
            if isinstance(value, WOperatorCondition):
                self.__predefinedConditions.append(value)

    def predefinedConditionsLabel(self):
        """Return predefined label displayed in menu"""
        return self.__predefinedConditionsLabel

    def setPredefinedConditionsLabel(self, value):
        """Set predefined label displayed in menu"""
        if isinstance(value, str):
            self.__predefinedConditionsLabel = value


class WOperatorBaseInputNumber(WOperatorBaseInput):
    """Search operator for Integer"""
    suffixChanged = Signal(str)

    def __init__(self, parent=None):
        super(WOperatorBaseInputNumber, self).__init__(parent)
        self._suffixList = []
        self._suffixLabel = ""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_GT,
                WOperatorType.OPERATOR_GE,
                WOperatorType.OPERATOR_LT,
                WOperatorType.OPERATOR_LE,
                WOperatorType.OPERATOR_EQ,
                WOperatorType.OPERATOR_NE,
                WOperatorType.OPERATOR_BETWEEN,
                WOperatorType.OPERATOR_NOT_BETWEEN
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_GT)

        self._input1.setAlignment(Qt.AlignRight)
        self._input2.setAlignment(Qt.AlignRight)

        self._input1.valueChanged.connect(self._input1Changed)
        self._input2.valueChanged.connect(self._input2Changed)

    def _input1Changed(self, value=None):
        """Value for input1 has changed"""
        if value:
            self.valueChanged.emit(value)
        if self._checkRangeValue and self._input1.value() > self._input2.value():
            self._input2.setValue(self._input1.value())

    def _input2Changed(self, value=None):
        """Value for input2 has changed"""
        if value:
            self.value2Changed.emit(value)
        if self._checkRangeValue and self._input1.value() > self._input2.value():
            self._input1.setValue(self._input2.value())

    def _contextMenuEvent(self, input, event):
        """Display context menu for given input

        If suffix list is not empty, add action to select a suffix
        """
        if len(self._suffixList) == 0 and len(self.predefinedConditions()) == 0:
            super(WOperatorBaseInputNumber, self)._contextMenuEvent(input, event)
            return

        menu = super(WOperatorBaseInputNumber, self)._contextMenuEvent(input, event, False)

        actionStepUp = QAction(i18n('Step up'))
        actionStepUp.triggered.connect(input.stepUp)
        actionStepDown = QAction(i18n('Step down'))
        actionStepDown.triggered.connect(input.stepDown)

        if len(self._suffixList) > 0:
            group = QActionGroup(self)
            group.setExclusive(True)
            subMenu = QMenu(self._suffixLabel)
            for suffix in self._suffixList:
                action = None
                if isinstance(suffix, str):
                    action = QAction(suffix)
                    action.setData((self.setSuffix, suffix))
                    action.setCheckable(True)
                elif isinstance(suffix, (tuple, list)) and len(suffix) == 2:
                    action = QAction(suffix[0])
                    action.setData((self.setSuffix, suffix[1]))
                    action.setCheckable(True)

                if action:
                    group.addAction(action)
                    subMenu.addAction(action)

                    if self._input1.suffix() == action.data()[1]:
                        action.setChecked(True)

            fAction = menu.actions()[0]
            menu.insertMenu(fAction, subMenu)

            if len(self.predefinedConditions()) == 0:
                menu.insertSeparator(fAction)

        menu.addSeparator()
        menu.addAction(actionStepUp)
        menu.addAction(actionStepDown)
        menu.exec(event.globalPos())

    def value(self):
        """Return current value"""
        return self._input1.value()

    def setValue(self, value):
        """set current value"""
        if value != self._input1.value():
            self._input1.setValue(value)

    def value2(self):
        """Return current 2nd value (when 'between' operator)"""
        return self._input2.value()

    def setValue2(self, value):
        """Set current 2nd value (when 'between' operator)"""
        if value != self._input2.value():
            self._input2.setValue(value)

    def minimum(self):
        """Return minimum value"""
        return self._input1.minimum()

    def setMinimum(self, value):
        """Set minimum value"""
        self._input1.setMinimum(value)
        self._input2.setMinimum(value)

    def maximum(self):
        """Return minimum value"""
        return self._input1.maximum()

    def setMaximum(self, value):
        """Set minimum value"""
        self._input1.setMaximum(value)
        self._input2.setMaximum(value)

    def suffix(self):
        """Return current suffix"""
        return self._input1.suffix()

    def setSuffix(self, value):
        """Return current suffix"""
        self._input1.setSuffix(value)
        self._input2.setSuffix(value)
        self.suffixChanged.emit(value)

    def suffixList(self):
        """Return suffix list"""
        return self._suffixList

    def setSuffixList(self, values):
        """Set suffix list"""
        self._suffixList = values

    def suffixLabel(self):
        """Return suffix label"""
        return self._suffixLabel

    def setSuffixLabel(self, value):
        """Set suffix label"""
        if isinstance(value, str):
            self._suffixLabel = value


class WOperatorInputInt(WOperatorBaseInputNumber):
    """Search operator for Integer"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._input1 = QSpinBox()
        self._input2 = QSpinBox()
        super(WOperatorInputInt, self)._initializeUi()


class WOperatorInputFloat(WOperatorBaseInputNumber):
    """Search operator for Float"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._input1 = QDoubleSpinBox()
        self._input2 = QDoubleSpinBox()
        super(WOperatorInputFloat, self)._initializeUi()

    def decimals(self):
        """Return current number of decimals"""
        return self._input1.decimals()

    def setDecimals(self, value):
        """Return current number of decimals"""
        self._input1.setDecimals(value)
        self._input2.setDecimals(value)


class WOperatorInputDateTime(WOperatorBaseInput):
    """Search operator for DateTime"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_GT,
                WOperatorType.OPERATOR_GE,
                WOperatorType.OPERATOR_LT,
                WOperatorType.OPERATOR_LE,
                WOperatorType.OPERATOR_EQ,
                WOperatorType.OPERATOR_NE,
                WOperatorType.OPERATOR_BETWEEN,
                WOperatorType.OPERATOR_NOT_BETWEEN
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_GT)

        self._input1 = QDateTimeEdit()
        self._input2 = QDateTimeEdit()

        self._input1.setCalendarPopup(True)
        self._input2.setCalendarPopup(True)

        self._input1.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._input2.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self._input1.setStyleSheet(STYLE_DROPDOWN_BUTTON_CALENDAR)
        self._input2.setStyleSheet(STYLE_DROPDOWN_BUTTON_CALENDAR)

        self._input1.dateTimeChanged.connect(self._input1Changed)
        self._input2.dateTimeChanged.connect(self._input2Changed)

    def _input1Changed(self, value=None):
        """Value for input1 has changed"""
        if value:
            self.valueChanged.emit(value.toMSecsSinceEpoch())
        if self._checkRangeValue and self._input1.dateTime() > self._input2.dateTime():
            self._input2.setDateTime(self._input1.dateTime())

    def _input2Changed(self, value=None):
        """Value for input2 has changed"""
        if value:
            self.value2Changed.emit(value.toMSecsSinceEpoch())
        if self._checkRangeValue and self._input1.dateTime() > self._input2.dateTime():
            self._input1.setDateTime(self._input2.dateTime())

    def value(self):
        """Return current value (as timestamp)"""
        return self._input1.dateTime().toMSecsSinceEpoch()/1000

    def setValue(self, value):
        """set current value

        Can be a time stamp or QDateTime
        """
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000)

        if isinstance(value, QDateTime) and value != self._input1.dateTime():
            self._input1.setDateTime(value)

    def value2(self):
        """Return current 2nd value (as timestamp) - (when 'between' operator)"""
        return self._input2.dateTime().toMSecsSinceEpoch()/1000

    def setValue2(self, value):
        """Set current 2nd value (when 'between' operator)"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000)

        if isinstance(value, QDateTime) and value != self._input2.dateTime():
            self._input2.setDateTime(value)

    def minimum(self):
        """Return minimum value  (as timestamp)"""
        return self._input1.minimumDateTime().toMSecsSinceEpoch()/1000

    def setMinimum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000)

        if isinstance(value, QDateTime):
            self._input1.setMinimumDateTime(value)
            self._input2.setMinimumDateTime(value)

    def maximum(self):
        """Return minimum value  (as timestamp)"""
        return self._input1.maximumDateTime().toMSecsSinceEpoch()/1000

    def setMaximum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000)

        if isinstance(value, QDateTime):
            self._input1.setMaximumDateTime(value)
            self._input2.setMaximumDateTime(value)


class WOperatorInputDate(WOperatorBaseInput):
    """Search operator for DateTime"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_GT,
                WOperatorType.OPERATOR_GE,
                WOperatorType.OPERATOR_LT,
                WOperatorType.OPERATOR_LE,
                WOperatorType.OPERATOR_EQ,
                WOperatorType.OPERATOR_NE,
                WOperatorType.OPERATOR_BETWEEN,
                WOperatorType.OPERATOR_NOT_BETWEEN
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_GT)

        self._input1 = QDateEdit()
        self._input2 = QDateEdit()

        self._input1.setCalendarPopup(True)
        self._input2.setCalendarPopup(True)

        self._input1.setDisplayFormat("yyyy-MM-dd")
        self._input2.setDisplayFormat("yyyy-MM-dd")

        self._input1.setStyleSheet(STYLE_DROPDOWN_BUTTON_CALENDAR)
        self._input2.setStyleSheet(STYLE_DROPDOWN_BUTTON_CALENDAR)

        self._input1.userDateChanged.connect(self._input1Changed)
        self._input2.userDateChanged.connect(self._input2Changed)

    def _input1Changed(self, value=None):
        """Value for input1 has changed"""
        if value:
            self.valueChanged.emit(QDateTime(value).toMSecsSinceEpoch())
        if self._input1.date() > self._input2.date():
            self._input2.setDate(self._input1.date())

    def _input2Changed(self, value=None):
        """Value for input2 has changed"""
        if value:
            self.value2Changed.emit(QDateTime(value).toMSecsSinceEpoch())
        if self._input1.date() > self._input2.date():
            self._input1.setDate(self._input2.date())

    def value(self):
        """Return current value (as timestamp)"""
        return QDateTime(self._input1.date()).toMSecsSinceEpoch()/1000

    def setValue(self, value):
        """set current value

        Can be a time stamp or QDateTime
        """
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000).date()

        if isinstance(value, QDate) and value != self._input1.date():
            self._input1.setDate(value)

    def value2(self):
        """Return current 2nd value (as timestamp) - (when 'between' operator)"""
        return QDateTime(self._input2.date()).toMSecsSinceEpoch()/1000

    def setValue2(self, value):
        """Set current 2nd value (when 'between' operator)"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000).date()

        if isinstance(value, QDate) and value != self._input2.date():
            self._input2.setDate(value)

    def minimum(self):
        """Return minimum value  (as timestamp)"""
        return QDateTime(self._input1.minimumDate()).toMSecsSinceEpoch()/1000

    def setMinimum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000).date()

        if isinstance(value, QDate):
            self._input1.setMinimumDate(value)
            self._input2.setMinimumDate(value)

    def maximum(self):
        """Return minimum value  (as timestamp)"""
        return QDateTime(self._input1.maximumDate()).toMSecsSinceEpoch()/1000

    def setMaximum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QDateTime.fromMSecsSinceEpoch(value*1000).date()

        if isinstance(value, QDate):
            self._input1.setMaximumDate(value)
            self._input2.setMaximumDate(value)


class WOperatorInputTime(WOperatorBaseInput):
    """Search operator for DateTime"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_GT,
                WOperatorType.OPERATOR_GE,
                WOperatorType.OPERATOR_LT,
                WOperatorType.OPERATOR_LE,
                WOperatorType.OPERATOR_EQ,
                WOperatorType.OPERATOR_NE,
                WOperatorType.OPERATOR_BETWEEN,
                WOperatorType.OPERATOR_NOT_BETWEEN
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_GT)

        self._input1 = QTimeEdit()
        self._input2 = QTimeEdit()

        self._input1.setDisplayFormat("HH:mm:ss")
        self._input2.setDisplayFormat("HH:mm:ss")

        self._input1.userTimeChanged.connect(self._input1Changed)
        self._input2.userTimeChanged.connect(self._input2Changed)

    def _input1Changed(self, value=None):
        """Value for input1 has changed"""
        if value:
            self.valueChanged.emit(value.msecsSinceStartOfDay())
        if self._checkRangeValue and self._input1.time() > self._input2.time():
            self._input2.setTime(self._input1.time())

    def _input2Changed(self, value=None):
        """Value for input2 has changed"""
        if value:
            self.value2Changed.emit(value.msecsSinceStartOfDay())
        if self._checkRangeValue and self._input1.time() > self._input2.time():
            self._input1.setTime(self._input2.time())

    def value(self):
        """Return current value (as number of seconds since start of day)"""
        return self._input1.time().msecsSinceStartOfDay()/1000

    def setValue(self, value):
        """set current value

        Can be a time stamp or QDateTime
        """
        if isinstance(value, (int, float)):
            value = QTime.fromMSecsSinceStartOfDay(1000*value)

        if isinstance(value, QTime) and value != self._input1.time():
            self._input1.setTime(value)

    def value2(self):
        """Return current 2nd value (as timestamp) - (when 'between' operator)"""
        return self._input2.time().msecsSinceStartOfDay()/1000

    def setValue2(self, value):
        """Set current 2nd value (when 'between' operator)"""
        if isinstance(value, (int, float)):
            value = QTime.fromMSecsSinceStartOfDay(1000*value)

        if isinstance(value, QTime) and value != self._input2.time():
            self._input2.setTime(value)

    def minimum(self):
        """Return minimum value  (as timestamp)"""
        return self._input1.minimumTime().msecsSinceStartOfDay()/1000

    def setMinimum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QTime.fromMSecsSinceStartOfDay(1000*value)

        if isinstance(value, QTime):
            self._input1.setMinimumTime(value)
            self._input2.setMinimumTime(value)

    def maximum(self):
        """Return minimum value  (as timestamp)"""
        return self._input1.maximumTime().msecsSinceStartOfDay()/1000

    def setMaximum(self, value):
        """Set minimum value"""
        if isinstance(value, (int, float)):
            value = QTime.fromMSecsSinceStartOfDay(1000*value)

        if isinstance(value, QTime):
            self._input1.setMaximumTime(value)
            self._input2.setMaximumTime(value)


class WOperatorInputStr(WOperatorBaseInput):
    """Search operator for DateTime"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_EQ,
                WOperatorType.OPERATOR_NE,
                WOperatorType.OPERATOR_MATCH,
                WOperatorType.OPERATOR_NOT_MATCH,
                WOperatorType.OPERATOR_LIKE,
                WOperatorType.OPERATOR_NOT_LIKE
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_EQ)

        self._input1 = QLineEdit()
        self._input1.setClearButtonEnabled(True)
        replaceLineEditClearButton(self._input1)

        self._input1.textChanged.connect(lambda v: self.valueChanged.emit(v))

    def value(self):
        """Return current value"""
        return self._input1.text()

    def setValue(self, value):
        """set current value"""
        if value != self._input1.text():
            self._input1.setText(value)


class WOperatorInputList(WOperatorBaseInput):
    """Search operator for List"""

    def _initializeUi(self):
        """Initialise widget

        - Operator list
        - Input widgets
        """
        self._defaultOperatorList = [
                WOperatorType.OPERATOR_IN,
                WOperatorType.OPERATOR_NOT_IN
            ]
        self._initOperator(self._defaultOperatorList)
        self.setOperator(WOperatorType.OPERATOR_IN)

        self._input1 = WTagInput()
        self._input1.setAcceptNewTags(WTagInput.ACCEPT_NEWTAG_NO)
        self._input1.setAutoSort(True)
        self._input1.lineEdit().setContextMenuPolicy(Qt.NoContextMenu)

        self._input1.tagSelection.connect(lambda: self.valueChanged.emit(self._input1.selectedTags()))

    def value(self):
        """Return current value (list of selected tags)"""
        return self._input1.selectedTags()

    def setValue(self, values):
        """set current values (list of selected tags)"""
        self._input1.setSelectedTags(values)

    def tagInput(self):
        """Expose WTagInput instance, allowing to define properties directly"""
        return self._input1
