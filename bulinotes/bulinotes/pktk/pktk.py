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
    __packageName = ''

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
            PkTk.__packageName = ''
        else:
            PkTk.__packageName = package

    @staticmethod
    def packageName():
        """Return current package name for PkTk"""
        return PkTk.__packageName
