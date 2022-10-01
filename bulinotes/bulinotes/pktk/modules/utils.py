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
# The imgutils module provides miscellaneous functions
#
# -----------------------------------------------------------------------------

import locale
import re
import sys
import os
import json
import base64

import xml.etree.ElementTree as ET

import PyQt5.uic

from PyQt5.Qt import *

from PyQt5.QtCore import (
        QRect
    )

from .imgutils import buildIcon
from ..widgets.wcolorbutton import QEColor
from ..pktk import *

# -----------------------------------------------------------------------------

try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    pass


def intDefault(value, default=0):
    """Return value as int

    If value is empty or None or not a valid integer, return default value
    """
    if value is None:
        return default

    try:
        return int(value)
    except Exception:
        return default


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
        lang = locale.getlocale()[0].replace('_', '-')

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
    returned = {
            'major': 0,
            'minor': 0,
            'revision': 0,
            'devFlag': '',
            'git': '',
            'rawString': Krita.instance().version()
        }
    nfo = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-([^\s]+)\s\(git\s([^\)]+)\))?", returned['rawString'])
    if nfo is not None:
        returned['major'] = int(nfo.groups()[0])
        returned['minor'] = int(nfo.groups()[1])
        returned['revision'] = int(nfo.groups()[2])
        returned['devFlag'] = nfo.groups()[3]
        returned['git'] = nfo.groups()[4]

    return returned


def checkKritaVersion(major, minor, revision):
    """Return True if current version is greater or equal to asked version"""
    nfo = kritaVersion()

    if major is None:
        return True
    elif nfo['major'] == major:
        if minor is None:
            return True
        elif nfo['minor'] == minor:
            if revision is None or nfo['revision'] >= revision:
                return True
        elif nfo['minor'] > minor:
            return True
    elif nfo['major'] > major:
        return True
    return False


def loadXmlUi(fileName, parent):
    """Load a ui file PyQt5.uic.loadUi()

    For each item in ui file that refers to an icon resource, update widget
    properties with icon reference
    """
    def findByName(parent, name):
        # return first widget for which name match to searched name
        if parent.objectName() == name:
            return parent

        if len(parent.children()) > 0:
            for widget in parent.children():
                searched = findByName(widget, name)
                if searched is not None:
                    return searched

        return None

    # load UI
    PyQt5.uic.loadUi(fileName, parent, PkTk.packageName())

    # Parse XML file and retrieve all object for which an icon is set
    tree = ET.parse(fileName)
    for nodeParent in tree.iter():
        for nodeChild in nodeParent:
            if 'name' in nodeChild.attrib and nodeChild.attrib['name'] == 'icon':
                nodeIconSet = nodeChild.find("iconset")
                if nodeIconSet:
                    widget = findByName(parent, nodeParent.attrib['name'])
                    if widget is not None:
                        for nodeIcon in list(nodeIconSet):
                            # store on object resource path for icons
                            widget.setProperty(f"__bcIcon_{nodeIcon.tag}", nodeIcon.text)


def cloneRect(rect):
    """Clone a QRect"""
    return QRect(rect.left(), rect.top(), rect.width(), rect.height())


def regExIsValid(regex):
    """Return True if given regular expression is valid, otherwise false"""
    try:
        r = re.compile(regex)
    except Exception:
        return False
    return True


def colorSpaceNfo(colorSpace):
    """Return informations for a given color Space

    Example:
        "RGBA" will return dictionary:
            {
                'channelSize': 1,
                'channels': ('Red', 'Green', 'Blue', 'Alpha'),
                'text': 'RGB with Alpha, 8-bit integer/channel'
            }

    If color space is not known, return None
    """
    # Color model id comparison through the ages (from kis_kra_loader.cpp)
    #
    #   2.4        2.5          2.6         ideal
    #
    #   ALPHA      ALPHA        ALPHA       ALPHAU8
    #
    #   CMYK       CMYK         CMYK        CMYKAU8
    #              CMYKAF32     CMYKAF32
    #   CMYKA16    CMYKAU16     CMYKAU16
    #
    #   GRAYA      GRAYA        GRAYA       GRAYAU8
    #   GrayF32    GRAYAF32     GRAYAF32
    #   GRAYA16    GRAYAU16     GRAYAU16
    #
    #   LABA       LABA         LABA        LABAU16
    #              LABAF32      LABAF32
    #              LABAU8       LABAU8
    #
    #   RGBA       RGBA         RGBA        RGBAU8
    #   RGBA16     RGBA16       RGBA16      RGBAU16
    #   RgbAF32    RGBAF32      RGBAF32
    #   RgbAF16    RgbAF16      RGBAF16
    #
    #   XYZA16     XYZA16       XYZA16      XYZAU16
    #              XYZA8        XYZA8       XYZAU8
    #   XyzAF16    XyzAF16      XYZAF16
    #   XyzAF32    XYZAF32      XYZAF32
    #
    #   YCbCrA     YCBCRA8      YCBCRA8     YCBCRAU8
    #   YCbCrAU16  YCBCRAU16    YCBCRAU16
    #              YCBCRF32     YCBCRF32
    channelSize = None
    channels = None
    text = None

    # RGB
    if colorSpace in ['RGBA', 'RGBAU8']:
        cspace = ('RGBA', 'U8')
        channelSize = 1
        channels = ('Red', 'Green', 'Blue', 'Alpha')
        text = 'RGB with Alpha, 8-bit integer/channel'
    elif colorSpace in ['RGBA16', 'RGBAU16']:
        cspace = ('RGBA', 'U16')
        channelSize = 2
        channels = ('Red', 'Green', 'Blue', 'Alpha')
        text = 'RGB with Alpha, 16-bit integer/channel'
    elif colorSpace in ['RgbAF16', 'RGBAF16']:
        cspace = ('RGBA', 'F16')
        channelSize = 2
        channels = ('Red', 'Green', 'Blue', 'Alpha')
        text = 'RGB with Alpha, 16-bit float/channel'
    elif colorSpace in ['RgbAF32', 'RGBAF32']:
        cspace = ('RGBA', 'F32')
        channelSize = 4
        channels = ('Red', 'Green', 'Blue', 'Alpha')
        text = 'RGB with Alpha, 32-bit float/channel'
    # CYMK
    elif colorSpace in ['CMYK', 'CMYKAU8']:
        cspace = ('CMYKA', 'U8')
        channelSize = 1
        channels = ('Cyan', 'Magenta', 'Yellow', 'Black', 'Alpha')
        text = 'CMYK with Alpha, 8-bit integer/channel'
    elif colorSpace in ['CMYKA16', 'CMYKAU16']:
        cspace = ('CMYKA', 'U16')
        channelSize = 2
        channels = ('Cyan', 'Magenta', 'Yellow', 'Black', 'Alpha')
        text = 'CMYK with Alpha, 16-bit integer/channel'
    elif colorSpace in ['CMYKAF32', 'CMYKAF32']:
        cspace = ('CMYKA', 'F32')
        channelSize = 4
        channels = ('Cyan', 'Magenta', 'Yellow', 'Black', 'Alpha')
        text = 'CMYK with Alpha, 32-bit float/channel'
    # GRAYSCALE
    elif colorSpace in ['A', 'G']:
        cspace = ('A', 'U8')
        channelSize = 1
        channels = ('Level',)
        text = 'Grayscale, 8-bit integer/channel'
    elif colorSpace in ['GRAYA', 'GRAYAU8']:
        cspace = ('GRAYA', 'U8')
        channelSize = 1
        channels = ('Gray', 'Alpha')
        text = 'Grayscale with Alpha, 8-bit integer/channel'
    elif colorSpace in ['GRAYA16', 'GRAYAU16']:
        cspace = ('GRAYA', 'U16')
        channelSize = 2
        channels = ('Gray', 'Alpha')
        text = 'Grayscale with Alpha, 16-bit integer/channel'
    elif colorSpace == 'GRAYAF16':
        cspace = ('GRAYA', 'F16')
        channelSize = 2
        channels = ('Gray', 'Alpha')
        text = 'Grayscale with Alpha, 16-bit float/channel'
    elif colorSpace in ['GrayF32', 'GRAYAF32']:
        cspace = ('GRAYA', 'F32')
        channelSize = 4
        channels = ('Gray', 'Alpha')
        text = 'Grayscale with Alpha, 32-bit float/channel'
    # L*A*B*
    elif colorSpace == 'LABAU8':
        cspace = ('LABA', 'U8')
        channelSize = 1
        channels = ('L*', 'a*', 'b*', 'Alpha')
        text = 'L*a*b* with Alpha, 8-bit integer/channel'
    elif colorSpace in ['LABA', 'LABAU16']:
        cspace = ('LABA', 'U16')
        channelSize = 2
        channels = ('L*', 'a*', 'b*', 'Alpha')
        text = 'L*a*b* with Alpha, 16-bit integer/channel'
    elif colorSpace == 'LABAF32':
        cspace = ('LABA', 'F32')
        channelSize = 4
        channels = ('L*', 'a*', 'b*', 'Alpha')
        text = 'L*a*b* with Alpha, 32-bit float/channel'
    # XYZ
    elif colorSpace in ['XYZAU8', 'XYZA8']:
        cspace = ('XYZA', 'U8')
        channelSize = 1
        channels = ('X', 'Y', 'Z', 'Alpha')
        text = 'XYZ with Alpha, 8-bit integer/channel'
    elif colorSpace in ['XYZA16', 'XYZAU16']:
        cspace = ('XYZA', 'U16')
        channelSize = 2
        channels = ('X', 'Y', 'Z', 'Alpha')
        text = 'XYZ with Alpha, 16-bit integer/channel'
    elif colorSpace in ['XyzAF16', 'XYZAF16']:
        cspace = ('XYZA', 'F16')
        channelSize = 2
        channels = ('X', 'Y', 'Z', 'Alpha')
        text = 'XYZ with Alpha, 16-bit float/channel'
    elif colorSpace in ['XyzAF32', 'XYZAF32']:
        cspace = ('XYZA', 'F32')
        channelSize = 4
        channels = ('X', 'Y', 'Z', 'Alpha')
        text = 'XYZ with Alpha, 32-bit float/channel'
    # YCbCr
    elif colorSpace in ['YCbCrA', 'YCBCRA8', 'YCBCRAU8']:
        cspace = ('YCbCrA', 'U8')
        channelSize = 1
        channels = ('Y', 'Cb', 'Cr', 'Alpha')
        text = 'YCbCr with Alpha, 8-bit integer/channel'
    elif colorSpace in ['YCbCrAU16', 'YCBCRAU16']:
        cspace = ('YCbCrA', 'U16')
        channelSize = 2
        channels = ('Y', 'Cb', 'Cr', 'Alpha')
        text = 'YCbCr with Alpha, 16-bit integer/channel'
    elif colorSpace == 'YCBCRF32':
        cspace = ('YCbCrA', 'F32')
        channelSize = 4
        channels = ('Y', 'Cb', 'Cr', 'Alpha')
        text = 'YCbCr with Alpha, 32-bit float/channel'

    if channelSize is None:
        return None

    return {
            'cspace': cspace,
            'channelSize': channelSize,
            'channels': channels,
            'text': text
        }


def replaceLineEditClearButton(lineEdit):
    """Replace default 'clear' button with a better one"""
    toolButton = lineEdit.findChild(QToolButton)
    if toolButton:
        toolButton.setIcon(buildIcon("pktk:edit_text_clear"))


# ------------------------------------------------------------------------------

class JsonQObjectEncoder(json.JSONEncoder):
    """Json encoder class to take in account additional object

    data={
        v1: QSize(1,2),
        v2: QEColor('#ffff00')
    }
    json.dumps(data, cls=JsonQObjectEncoder)

    will return string:
        '''
        {"v1": {
                "objType": 'QSize',
                "width": 1,
                "height": 2,
            },
         "v2": {
                "objType": 'QEColor',
                "color": '#ffff00',
                "isNone": false,
            }
        }
        '''
    """
    def default(self, objectToEncode):
        if isinstance(objectToEncode, QSize):
            return {
                    'objType': "QSize",
                    'width': objectToEncode.width(),
                    'height': objectToEncode.height()
                }
        elif isinstance(objectToEncode, QEColor):
            return {
                    'objType': "QEColor",
                    'color': objectToEncode.name(),
                    'isNone': objectToEncode.isNone()
                }
        elif isinstance(objectToEncode, QImage):
            ptr = objectToEncode.bits()
            ptr.setsize(objectToEncode.byteCount())
            return {
                    'objType': "QImage",
                    'b64': base64.b64encode(ptr.asstring()).decode()
                }
        elif isinstance(objectToEncode, bytes):
            return {
                    'objType': "bytes",
                    'b64': base64.b64encode(objectToEncode).decode()
                }
        # Let the base class default method raise the TypeError
        return super(JsonQObjectEncoder, self).default(objectToEncode)


class JsonQObjectDecoder(json.JSONDecoder):
    """Json decoder class to take in account additional object

    json string:
        '''
        {"v1": {
                "objType": 'QSize',
                "width": 1,
                "height": 2,
            },
         "v2": {
                "objType": 'QEColor',
                "color": '#ffff00',
                "isNone": false,
            }
        }
        '''

    json.loads(data, cls=JsonQObjectDecoder)

    will return dict:
        {
            v1: QSize(1,2),
            v2: QEColor('#ffff00')
        }
    """
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict2obj)

    def dict2obj(self, objectToDecode):
        if ('objType' in objectToDecode and objectToDecode['objType'] == "QSize" and
           'width' in objectToDecode and 'height' in objectToDecode):
            return QSize(objectToDecode['width'], objectToDecode['height'])
        elif ('objType' in objectToDecode and objectToDecode['objType'] == "QEColor" and
              'color' in objectToDecode and 'isNone' in objectToDecode):
            returned = QEColor(objectToDecode['color'])
            returned.setNone(objectToDecode['isNone'])
            return returned
        elif ('objType' in objectToDecode and objectToDecode['objType'] == "QImage" and
              'b64' in objectToDecode):
            return QImage.fromData(base64.b64decode(objectToDecode['b64']))
        elif ('objType' in objectToDecode and objectToDecode['objType'] == "bytes" and
              'b64' in objectToDecode):
            return base64.b64decode(objectToDecode['b64'])

        # Let the base class default method raise the TypeError
        return objectToDecode


# ------------------------------------------------------------------------------

class Debug(object):
    """Display debug info to console if debug is enabled"""
    __enabled = False

    @staticmethod
    def print(value, *argv):
        """Print value to console, using argv for formatting"""
        if Debug.__enabled and isinstance(value, str):
            sys.stdout = sys.__stdout__
            print('DEBUG:', value.format(*argv))

    @staticmethod
    def enabled():
        """return if Debug is enabled or not"""
        return Debug.__enabled

    @staticmethod
    def setEnabled(value):
        """set Debug enabled or not"""
        Debug.__enabled = value
