#-----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2020 - Grum999
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
# A Krita plugin designed to add Notes in documents
# -----------------------------------------------------------------------------

import re
import time
import sys
import os

import PyQt5.uic
from PyQt5.Qt import *
from PyQt5.QtGui import (
        QBrush,
        QPainter,
        QPixmap
    )

# ------------------------------------------------------------------------------
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

    def enabled():
        """return if Debug is enabled or not"""
        return Debug.__enabled

    def setEnabled(value):
        """set Debug enabled or not"""
        Debug.__enabled=value
