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

# some utility functions
# -> need to review it and maybe created different dedicated modules

from math import floor
import locale
import re
import time
import sys
import os

import xml.etree.ElementTree as ET

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtGui import (
        QBrush,
        QPainter,
        QPixmap
    )
from PyQt5.QtCore import (
        pyqtSignal as Signal,
        QRect
    )
from PyQt5.QtWidgets import (
        QAction
    )

from pktk import *

# -----------------------------------------------------------------------------
PkTk.setModuleInfo(
    'edialog',
    '1.0.0',
    'EDialog',
    'Some basics utility functions'
)

try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass



# ------------------------------------------------------------------------------
# don't really like to use global variable... create a class with static methods instead?
__bytesSizeToStrUnit = 'autobin'
def setBytesSizeToStrUnit(unit):
    global __bytesSizeToStrUnit
    if unit.lower() in ['auto', 'autobin']:
        __bytesSizeToStrUnit = unit

def getBytesSizeToStrUnit():
    global __bytesSizeToStrUnit
    return __bytesSizeToStrUnit

def strToBytesSize(value):
    """Convert a value to bytes

    Given `value` can be an integer (return value) or a string
    When provided as a string, can be in form:
        <size><unit>

        With:
            Size:
                An integer or decimal:
                    1
                    1.1
                    .1
            Unit
                'GB', 'GiB'
                'MB', 'MiB'
                'KB', 'KiB'
                'B', ''

    If unable to parse value, raise an exception
    """
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        return int(value)
    elif isinstance(value, str):
        fmt = re.match("^(\d*\.\d*|\d+)(gb|gib|mb|mib|kb|kib|b)?$", value.lower())

        if not fmt is None:
            returned = float(fmt.group(1))

            if fmt.group(2) == 'kb':
                returned *= 1000
            elif fmt.group(2) == 'kib':
                returned *= 1024
            elif fmt.group(2) == 'mb':
                returned *= 1000000
            elif fmt.group(2) == 'mib':
                returned *= 1048576
            elif fmt.group(2) == 'gb':
                returned *= 1000000000
            elif fmt.group(2) == 'gib':
                returned *= 1073741824

            return int(returned)

        else:
            raise Exception(f"Given value '{value}' can't be parsed!")
    else:
        raise Exception(f"Given value '{value}' can't be parsed!")

def strDefault(value, default=''):
    """Return value as str

    If value is empty or None, return default value
    """
    if value is None or value == '' or value == 0:
        return default
    return str(value)

def intDefault(value, default=0):
    """Return value as int

    If value is empty or None or not a valid integer, return default value
    """
    if value is None:
        return default

    try:
        return int(value)
    except:
        return default

def bytesSizeToStr(value, unit=None, decimals=2):
    """Convert a size (given in Bytes) to given unit

    Given unit can be:
    - 'auto'
    - 'autobin' (binary Bytes)
    - 'GiB', 'MiB', 'KiB' (binary Bytes)
    - 'GB', 'MB', 'KB', 'B'
    """
    global __bytesSizeToStrUnit
    if unit is None:
        unit = __bytesSizeToStrUnit

    if not isinstance(unit, str):
        raise Exception('Given `unit` must be a valid <str> value')

    unit = unit.lower()
    if not unit in ['auto', 'autobin', 'gib', 'mib', 'kib', 'gb', 'mb', 'kb', 'b']:
        raise Exception('Given `unit` must be a valid <str> value')

    if not isinstance(decimals, int) or decimals < 0 or decimals > 8:
        raise Exception('Given `decimals` must be a valid <int> between 0 and 8')

    if not (isinstance(value, int) or isinstance(value, float)):
        raise Exception('Given `value` must be a valid <int> or <float>')

    if unit == 'autobin':
        if value >= 1073741824:
            unit = 'gib'
        elif value >= 1048576:
            unit = 'mib'
        elif value >= 1024:
            unit = 'kib'
        else:
            unit = 'b'
    elif unit == 'auto':
        if value >= 1000000000:
            unit = 'gb'
        elif value >= 1000000:
            unit = 'mb'
        elif value >= 1000:
            unit = 'kb'
        else:
            unit = 'b'

    fmt = f'{{0:.{decimals}f}}{{1}}'

    if unit == 'gib':
        return fmt.format(value/1073741824, 'GiB')
    elif unit == 'mib':
        return fmt.format(value/1048576, 'MiB')
    elif unit == 'kib':
        return fmt.format(value/1024, 'KiB')
    elif unit == 'gb':
        return fmt.format(value/1000000000, 'GB')
    elif unit == 'mb':
        return fmt.format(value/1000000, 'MB')
    elif unit == 'kb':
        return fmt.format(value/1000, 'KB')
    else:
        return f'{value}B'

def tsToStr(value, pattern=None, valueNone=''):
    """Convert a timestamp to localtime string

    If no pattern is provided or if pattern = 'dt' or 'full', return full date/time (YYYY-MM-DD HH:MI:SS)
    If pattern = 'd', return date (YYYY-MM-DD)
    If pattern = 't', return time (HH:MI:SS)
    Otherwise try to use pattern literally (strftime)
    """
    if value is None:
        return valueNone
    if pattern is None or pattern.lower() in ['dt', 'full']:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
    elif pattern.lower() == 'd':
        return time.strftime('%Y-%m-%d', time.localtime(value))
    elif pattern.lower() == 't':
        return time.strftime('%H:%M:%S', time.localtime(value))
    else:
        return time.strftime(pattern, time.localtime(value))

def strToTs(value):
    """Convert a string to timestamp

    If value is a numeric value, return value

    Value must be in form:
    - YYYY-MM-DD HH:MI:SS
    - YYYY-MM-DD            (consider time is 00:00:00)
    - HH:MI:SS              (consider date is current date)

    otherwise return 0
    """
    if value is None or value == '':
        return None
    if isinstance(value, float) or isinstance(value, int):
        return value

    fmt = re.match("^(\d{4}-\d{2}-\d{2})?\s*(\d{2}:\d{2}:\d{2})?$", value)
    if not fmt is None:
        if fmt.group(1) is None:
            value = time.strftime('%Y-%m-%d ') + value
        if fmt.group(2) is None:
            value += ' 00:00:00'

        return time.mktime(time.strptime(value, '%Y-%m-%d %H:%M:%S'))

    return 0

def frToStrTime(nbFrames, frameRate):
    """Convert a number of frame to duration"""
    returned_ss=int(nbFrames/frameRate)
    returned_ff=nbFrames - returned_ss * frameRate
    returned_mn=int(returned_ss/60)
    returned_ss=returned_ss - returned_mn * 60

    return f"{returned_mn:02d}:{returned_ss:02d}.{returned_ff:02d}"

def secToStrTime(nbSeconds):
    """Convert a number of seconds to duration"""
    returned = ''
    nbDays = floor(nbSeconds / 86400)
    if nbDays > 0:
        nbSeconds = nbSeconds - nbDays * 86400
        returned = f'{nbDays}D, '

    returned+=time.strftime('%H:%M:%S', time.gmtime(nbSeconds))

    return returned

def getLangValue(dictionary, lang=None, default=''):
    """Return value from a dictionary for which key is lang code (like en-US)

    if `dictionary` is empty:
        return `default` value
    if `dictionary` contains one entry only:
        return it

    if `lang` is None:
        use current locale

    if `lang` exist in dictionary:
        return it
    else if language exist (with different country code):
        return it
    else if 'en-XX' exists:
        return it
    else:
        return first entry
    """
    if not isinstance(dictionary, dict):
        raise Exception('Given `dictionary` must be a valid <dict> value')

    if len(dictionary) == 0:
        return default
    elif len(dictionary) == 1:
        return dictionary[list(dictionary.keys())[0]]

    if lang is None:
        lang = locale.getlocale()[0].replace('_','-')

    if lang in dictionary:
        return dictionary[lang]
    else:
        language = lang.split('-')[0]
        for key in dictionary.keys():
            keyLang = key.split('-')[0]

            if keyLang == language:
                return dictionary[key]

        # not found, try "en"
        language = 'en'
        for key in dictionary.keys():
            keyLang = key.split('-')[0]

            if keyLang == language:
                return dictionary[key]

        # not found, return first entry
        return dictionary[list(dictionary.keys())[0]]

def checkerBoardBrush(size=32):
    """Return a checker board brush"""
    tmpPixmap = QPixmap(size,size)
    tmpPixmap.fill(QColor(255,255,255))
    brush = QBrush(QColor(220,220,220))

    canvas = QPainter()
    canvas.begin(tmpPixmap)
    canvas.setPen(Qt.NoPen)

    s1 = size>>1
    s2 = size - s1

    canvas.setRenderHint(QPainter.Antialiasing, False)
    canvas.fillRect(QRect(0, 0, s1, s1), brush)
    canvas.fillRect(QRect(s1, s1, s2, s2), brush)
    canvas.end()

    return QBrush(tmpPixmap)

def checkerBoardImage(size, checkerSize=32):
    """Return a checker board image"""
    if isinstance(size, int):
        size = QSize(size, size)

    if not isinstance(size, QSize):
        return None

    pixmap = QPixmap(size)
    painter = QPainter(pixmap)
    painter.begin()
    painter.fillRect(pixmap.rect(), checkerBoardBrush(checkerSize))
    painter.end()

    return pixmap

def buildIcon(icons):
    """Return a QIcon from given icons"""
    if isinstance(icons, QIcon):
        return icons
    elif isinstance(icons, list) and len(icons)>0:
        returned = QIcon()
        for icon in icons:
            returned.addPixmap(*icon)
        return returned
    else:
        raise EInvalidType("Given `icons` must be a list of tuples")

def buildQAction(icons, title, parent, action=None, parameters=[]):
    """Build a QAction and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    def execute(dummy=None):
        if callable(action):
            action(*parameters)

    pixmapList=[]
    propertyList=[]
    for icon in icons:
        if isinstance(icon[0], QPixmap):
            pixmapListItem=[icon[0]]
            propertyListPath=''
        elif isinstance(icon[0], str):
            pixmapListItem=[QPixmap(icon[0])]
            propertyListPath=icon[0]

        for index in range(1,3):
            if index == 1:
                if len(icon) >= 2:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Normal)
            elif index == 2:
                if len(icon) >= 3:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Off)

        pixmapList.append(tuple(pixmapListItem))

        key = '__bcIcon_'
        if pixmapListItem[1]==QIcon.Normal:
            key+='normal'
        elif pixmapListItem[1]==QIcon.Active:
            key+='active'
        elif pixmapListItem[1]==QIcon.Disabled:
            key+='disabled'
        elif pixmapListItem[1]==QIcon.Selected:
            key+='selected'
        if pixmapListItem[2]==QIcon.Off:
            key+='off'
        else:
            key+='on'

        propertyList.append( (key, propertyListPath) )

    returnedAction=QAction(buildIcon(pixmapList), title, parent)

    for property in propertyList:
        returnedAction.setProperty(*property)

    if callable(action):
        returnedAction.triggered.connect(execute)

    return returnedAction

def buildQMenu(icons, title, parent):
    """Build a QMenu and store icons resource path as properties

    Tricky method to be able to reload icons on the fly when theme is modified
    """
    pixmapList=[]
    propertyList=[]
    for icon in icons:
        if isinstance(icon[0], QPixmap):
            pixmapListItem=[icon[0]]
            propertyListPath=''
        elif isinstance(icon[0], str):
            pixmapListItem=[QPixmap(icon[0])]
            propertyListPath=icon[0]

        for index in range(1,3):
            if index == 1:
                if len(icon) >= 2:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Normal)
            elif index == 2:
                if len(icon) >= 3:
                    pixmapListItem.append(icon[index])
                else:
                    pixmapListItem.append(QIcon.Off)

        pixmapList.append(tuple(pixmapListItem))

        key = '__bcIcon_'
        if pixmapListItem[1]==QIcon.Normal:
            key+='normal'
        elif pixmapListItem[1]==QIcon.Active:
            key+='active'
        elif pixmapListItem[1]==QIcon.Disabled:
            key+='disabled'
        elif pixmapListItem[1]==QIcon.Selected:
            key+='selected'
        if pixmapListItem[2]==QIcon.Off:
            key+='off'
        else:
            key+='on'

        propertyList.append( (key, propertyListPath) )

    returnedMenu=QMenu(title, parent)
    returnedMenu.setIcon(buildIcon(pixmapList))

    for property in propertyList:
        returnedMenu.setProperty(*property)

    return returnedMenu

def kritaVersion():
    """Return a dictionary with following values:

    {
        'major': 0,
        'minor': 0,
        'revision': 0,
        'devRev': '',
        'git': '',
        'rawString': ''
    }

    Example:
        "5.0.0-prealpha (git 8f2fe10)"
        will return

        {
            'major': 5,
            'minor': 0,
            'revision', 0,
            'devFlag': 'prealpha',
            'git': '8f2fe10',
            'rawString': '5.0.0-prealpha (git 8f2fe10)'
        }
    """
    returned={
            'major': 0,
            'minor': 0,
            'revision': 0,
            'devFlag': '',
            'git': '',
            'rawString': Krita.instance().version()
        }
    nfo=re.match("(\d+)\.(\d+)\.(\d+)(?:-([^\s]+)\s\(git\s([^\)]+)\))?", returned['rawString'])
    if not nfo is None:
        returned['major']=int(nfo.groups()[0])
        returned['minor']=int(nfo.groups()[1])
        returned['revision']=int(nfo.groups()[2])
        returned['devFlag']=nfo.groups()[3]
        returned['git']=nfo.groups()[4]

    return returned

def checkKritaVersion(major, minor, revision):
    """Return True if current version is greater or equal to asked version"""
    nfo = kritaVersion()

    if major is None:
        return True
    elif nfo['major']==major:
        if minor is None:
            return True
        elif nfo['minor']==minor:
            if revision is None or nfo['revision']>=revision:
                return True
        elif nfo['minor']>minor:
            return True
    elif nfo['major']>major:
        return True
    return False

def strToMaxLength(value, maxLength, completeSpace=True, leftAlignment=True):
    """Format given string `value` to fit in given `maxLength`

    If len is greater than `maxLength`, string is splitted with carriage return

    If value contains carriage return, each line is processed separately

    If `completeSpace` is True, value is completed with space characters to get
    the expected length.
    """
    returned = []
    if os.linesep in value:
        rows = value.split(os.linesep)

        for row in rows:
            returned.append(strToMaxLength(row, maxLength, completeSpace))
    else:
        textLen = len(value)

        if textLen < maxLength:
            if completeSpace:
                # need to complete with spaces
                if leftAlignment:
                    returned.append( value + (' ' * (maxLength - textLen)))
                else:
                    returned.append( (' ' * (maxLength - textLen)) + value )
            else:
                returned.append(value)
        elif textLen > maxLength:
            # keep spaces separators
            tmpWords=re.split('(\s)', value)
            words=[]

            # build words list
            for word in tmpWords:
                while len(word) > maxLength:
                    words.append(word[0:maxLength])
                    word=word[maxLength:]
                if word != '':
                    words.append(word)

            builtRow=''
            for word in words:
                if (len(builtRow) + len(word))<maxLength:
                    builtRow+=word
                else:
                    returned.append(strToMaxLength(builtRow, maxLength, completeSpace))
                    builtRow=word

            if builtRow!='':
                returned.append(strToMaxLength(builtRow, maxLength, completeSpace))
        else:
            returned.append(value)

    return os.linesep.join(returned)

def stripTags(value):
    """Strip HTML tags and remove amperseed added by Qt"""
    return re.sub('<[^<]+?>', '', re.sub('<br/?>', os.linesep, value))  \
                .replace('&nbsp;', ' ')     \
                .replace('&gt;', '>')       \
                .replace('&lt;', '<')       \
                .replace('&amp;', '&&')     \
                .replace('&&', chr(1))      \
                .replace('&', '')           \
                .replace(chr(1), '&')

def stripHtml(value):
    """Return HTML plain text"""
    return QTextDocumentFragment.fromHtml(value).toPlainText();


def loadXmlUi(fileName, parent):
    """Load a ui file PyQt5.uic.loadUi()

    For each item in ui file that refers to an icon resource, update widget
    properties with icon reference
    """
    def findByName(parent, name):
        # return first widget for which name match to searched name
        if parent.objectName() == name:
            return parent

        if len(parent.children())>0:
            for widget in parent.children():
                searched = findByName(widget, name)
                if not searched is None:
                    return searched

        return None

    # load UI
    PyQt5.uic.loadUi(fileName, parent)

    # Parse XML file and retrieve all object for which an icon is set
    tree = ET.parse(fileName)
    for nodeParent in tree.getiterator():
        for nodeChild in nodeParent:
            if 'name' in nodeChild.attrib and nodeChild.attrib['name'] == 'icon':
                nodeIconSet=nodeChild.find("iconset")
                if nodeIconSet:
                    widget = findByName(parent, nodeParent.attrib['name'])
                    if not widget is None:
                        for nodeIcon in list(nodeIconSet):
                            # store on object resource path for icons
                            widget.setProperty(f"__bcIcon_{nodeIcon.tag}", nodeIcon.text)

def cloneRect(rect):
    """Clone a QRect"""
    return QRect(rect.left(), rect.top(), rect.width(), rect.height())

def regExIsValid(regex):
    """Return True if given regular expression is valid, otherwise false"""
    try:
        r=re.compile(regex)
    except:
        return False
    return True

def qImageToPngQByteArray(image):
    """Convert a QImage as PNG and return a QByteArray"""
    if isinstance(image, QImage):
        ba=QByteArray()
        buffer=QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        return ba

# ------------------------------------------------------------------------------
class BCTimer(object):

    @staticmethod
    def sleep(value):
        """Do a sleep of `value` milliseconds

        use of python timer.sleep() method seems to be not recommanded in a Qt application.. ??
        """
        loop = QEventLoop()
        QTimer.singleShot(value, loop.quit)
        loop.exec()


class Stopwatch(object):
    """Manage stopwatch, mainly used for performances test & debug"""
    __current = {}

    @staticmethod
    def reset():
        """Reset all Stopwatches"""
        Stopwatch.__current = {}

    @staticmethod
    def start(name):
        """Start a stopwatch

        If stopwatch already exist, restart from now
        """
        Stopwatch.__current[name] = {'start': time.time(),
                                     'stop': None
                                }

    @staticmethod
    def stop(name):
        """Stop a stopwatch

        If stopwatch doesn't exist or is already stopped, do nothing
        """
        if name in Stopwatch.__current and Stopwatch.__current[name]['stop'] is None:
            Stopwatch.__current[name]['stop'] = time.time()

    @staticmethod
    def duration(name):
        """Return stopwatch duration, in seconds

        If stopwatch doesn't exist, return None
        If stopwatch is not stopped, return current duration from start time
        """
        if name in Stopwatch.__current:
            if Stopwatch.__current[name]['stop'] is None:
                return time.time() - Stopwatch.__current[name]['start']
            else:
                return Stopwatch.__current[name]['stop'] - Stopwatch.__current[name]['start']


class Debug(object):
    """Display debug info to console if debug is enabled"""
    __enabled = False

    @staticmethod
    def print(value, *argv):
        """Print value to console, using argv for formatting"""
        if Debug.__enabled and isinstance(value, str):
            sys.stdout = sys.__stdout__
            print('DEBUG:', value.format(*argv))

    def enabled():
        """return if Debug is enabled or not"""
        return Debug.__enabled

    def setEnabled(value):
        """set Debug enabled or not"""
        Debug.__enabled=value
