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

import os

class EInvalidType(Exception):
    """An invalid type has been provided"""
    pass

class EInvalidValue(Exception):
    """An invalid value has been provided"""
    pass

class EInvalidStatus(Exception):
    """An invalid status has been detected"""
    pass



class PkTk:
    __libraries = {}
    __packageName=''

    PATH = os.path.dirname(__file__)
    PATH_RESOURCES = os.path.join(os.path.dirname(__file__), 'resources')

    @staticmethod
    def getPath(name=None):
        """Return path for library"""

        if isinstance(name, str):
            return os.path.join(os.path.realpath(os.path.dirname(__file__)), name)
        elif isinstance(name, list):
            return os.path.join(os.path.realpath(os.path.dirname(__file__)), *name)
        else:
            return os.path.realpath(os.path.dirname(__file__))

    @staticmethod
    def setPackageName(package=None):
        """Define current package name for PkTk"""
        if not isinstance(package, str):
            PkTk.__packageName=''
        else:
            PkTk.__packageName=package

    @staticmethod
    def packageName():
        """Return current package name for PkTk"""
        return PkTk.__packageName
