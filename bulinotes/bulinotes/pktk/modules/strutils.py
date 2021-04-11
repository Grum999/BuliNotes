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
# String utility: miscellaneous
# -----------------------------------------------------------------------------

import os
import re

from PyQt5.QtGui import QTextDocumentFragment

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

def indent(text, firstIndent='', nextIndent='', strip=False):
    """Indent text

    Given `firstIndent` is used to define prefix applied on first line
    Given `nextIndent` is used to define prefix applied on other lines

    If `strip` if True, line are stripped before indent is applied

    Example:
        s1='This is an\n'
           'an example'

        s2='Given list\n'
           '- item 1\n'
           '- item 2'


        indent(s1, '* ', ' ')
           '* This is an\n'
           '  an example'

        indent(s2, '* ', '    ')
           '* Given list\n'
           '    - item 1\n'
           '    - item 2'
    """
    if isinstance(text, str):
        text=text.split(os.linesep)

    if not isinstance(text, list):
        return str(text)

    result=[]
    for index, line in enumerate(text):
        if strip:
            line=line.strip()

        if index==0 and firstIndent!='':
            line=firstIndent+line
        elif nextIndent!='':
            line=nextIndent+line

        result.append(line)

    return os.linesep.join(result)
