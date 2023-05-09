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
# The imgutils module provides miscellaneous date&time functions
#
# -----------------------------------------------------------------------------

from math import floor
import time
import re

from PyQt5.Qt import (QTimer, QEventLoop)


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

    fmt = re.match(r"^(\d{4}-\d{2}-\d{2})?\s*(\d{2}:\d{2}:\d{2})?$", value)
    if fmt is not None:
        if fmt.group(1) is None:
            value = time.strftime('%Y-%m-%d ') + value
        if fmt.group(2) is None:
            value += ' 00:00:00'

        return time.mktime(time.strptime(value, '%Y-%m-%d %H:%M:%S'))

    return 0


def frToStrTime(nbFrames, frameRate):
    """Convert a number of frame to duration"""
    returned_ss = int(nbFrames/frameRate)
    returned_ff = nbFrames - returned_ss * frameRate
    returned_mn = int(returned_ss/60)
    returned_ss = returned_ss - returned_mn * 60

    return f"{returned_mn:02d}:{returned_ss:02d}.{returned_ff:02d}"


def secToStrTime(nbSeconds):
    """Convert a number of seconds to duration (Days, H:M:S)"""
    returned = ''
    nbDays = floor(nbSeconds / 86400)
    if nbDays > 0:
        nbSeconds = nbSeconds - nbDays * 86400
        returned = f'{nbDays}D, '

    returned += time.strftime('%H:%M:%S', time.gmtime(nbSeconds))

    return returned


class Timer(object):

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
    def reset(reKey=None):
        """Reset all Stopwatches"""
        if reKey is None:
            Stopwatch.__current = {}
        else:
            for key in list(Stopwatch.__current.keys()):
                if re.search(reKey, key):
                    Stopwatch.__current.pop(key)

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

    @staticmethod
    def list(pattern=None):
        """Return all stopwatch durations with a list of tuple(key, duration in seconds)

        If stopwatch doesn't exist, return None
        If stopwatch is not stopped, return current duration from start time
        """
        if isinstance(pattern, str):
            return [(name, Stopwatch.duration(name)) for name in sorted(Stopwatch.__current.keys()) if re.match(pattern, name)]
        else:
            return [(name, Stopwatch.duration(name)) for name in sorted(Stopwatch.__current.keys())]
