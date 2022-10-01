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
# The uncompress module provides class used to manage 7Zip and RAR archives files
# using installed 7z and unrar tools installed on system, if available
#
# Notes:
#   - Unrar only manage RAR files
#   - 7Zip manage 7z and RAR files
#   - Implementation manage Windows & Linux OS (not MacOS)
#
# Main class from this module
#
# - Uncompress
#       Main class to uncomrpess files
#
# - UncompressFileInfo
#       File information about file from archive
#
# -----------------------------------------------------------------------------

import sys
import re
import os
import os.path
import subprocess

from .timeutils import (strToTs, tsToStr)
from .utils import Debug

# define command line according to OS
if sys.platform == 'win32':
    import winreg

    def getUnrar():
        """return unrar executable full path name as string, None if not found"""
        try:
            # When installed, WinRAR create this registry key where value "path" can be found
            registryKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\WinRAR.exe", 0, winreg.KEY_READ)
            value, regtype = winreg.QueryValueEx(registryKey, "Path")
        except Exception:
            value = None

        winreg.CloseKey(registryKey)

        if value is not None:
            value = os.path.join(value, "unrar.exe")
            if os.path.isfile(value):
                return value
        return None

    def get7z():
        """return 7z executable full path name as string, None if not found"""
        try:
            # When installed, WinRAR create this registry key where value "path" can be found
            registryKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\7zFM.exe", 0, winreg.KEY_READ)
            value, regtype = winreg.QueryValueEx(registryKey, "Path")
        except Exception:
            value = None

        winreg.CloseKey(registryKey)

        if value is not None:
            value = os.path.join(value, "7z.exe")
            if os.path.isfile(value):
                return value
        return None

elif sys.platform == 'linux':
    def getUnrar():
        """return unrar executable full path name as string, None if not found"""
        # When installed, unrar should be available in /usr/bin
        value = "/usr/bin/unrar"
        if os.path.isfile(value):
            return value

        return None

    def get7z():
        """return 7z executable full path name as string, None if not found"""
        # When installed, unrar should be available in /usr/bin
        value = "/usr/bin/7z"
        if os.path.isfile(value):
            return value

        return None

else:
    # do not manage other system...
    def getUnrar():
        return None

    def get7z():
        return None


class UncompressFileInfo:
    """File information from archive"""

    def __init__(self, fileName, fileDate, fileTime, fileUncompressedSize, fileCompressedSize, fileIsDir):
        self.__fileName = fileName
        self.__fileDateTime = strToTs(f"{fileDate} {fileTime}")
        self.__fileUncompressedSize = fileUncompressedSize
        self.__fileCompressedSize = fileCompressedSize
        self.__fileIsDir = fileIsDir

    def __repr__(self):
        return f"<UncompressFileInfo('{self.__fileName}', {self.__fileIsDir}, {self.__fileUncompressedSize}>>{self.__fileCompressedSize}, {tsToStr(self.__fileDateTime)})>"

    def name(self):
        return self.__fileName

    def timeStamp(self):
        return self.__fileDateTime

    def uncompressedSize(self):
        return self.__fileUncompressedSize

    def compressedSize(self):
        return self.__fileCompressedSize

    def isDirectory(self):
        return self.__fileIsDir


class Uncompress:
    """A generic class to wrap unrar/7z tools

    Manage uncompression only
    """

    FORMAT_RAR = 'rar'
    FORMAT_7Z = '7z'

    __INITIALISED = False
    __PATH_RAR = None
    __PATH_7Z = None

    @staticmethod
    def initialize():
        """Initialize class"""
        if Uncompress.__INITIALISED:
            return
        Uncompress.__PATH_RAR = getUnrar()
        Uncompress.__PATH_7Z = get7z()
        Uncompress.__INITIALISED = True

    @staticmethod
    def availableFormat():
        """Return list of available uncompress format"""
        returned = []
        if Uncompress.__PATH_RAR is not None:
            returned.append(Uncompress.FORMAT_RAR)
        if Uncompress.__PATH_7Z is not None:
            returned.append(Uncompress.FORMAT_7Z)
            if Uncompress.FORMAT_RAR not in returned:
                # 7z can read RAR files
                returned.append(Uncompress.FORMAT_RAR)
        return returned

    @staticmethod
    def preferredForFileFormat(archiveFile):
        """Return which tool to use according to current file format

        return None if not possible to manage file format
        """
        returned = None

        if os.path.isfile(archiveFile):
            with open(archiveFile, 'rb') as fHandler:
                magicBytes = fHandler.read(6)

                if magicBytes == b'\x37\x7A\xBC\xAF\x27\x1C':
                    returned = Uncompress.FORMAT_7Z
                elif magicBytes == b'\x52\x61\x72\x21\x1A\x07':
                    returned = Uncompress.FORMAT_RAR

            # now file format is known
            # need to check available uncompression tools available to return the best one
            if returned == Uncompress.FORMAT_7Z:
                if Uncompress.__PATH_7Z is not None:
                    # 7Zip available, use it
                    return Uncompress.FORMAT_7Z
                elif Uncompress.__PATH_RAR is not None:
                    # 7Zip not available, but RAR is available, use it
                    return Uncompress.FORMAT_RAR
            elif returned == Uncompress.FORMAT_RAR:
                if Uncompress.__PATH_RAR is not None:
                    # Unrar available, use it
                    return Uncompress.FORMAT_RAR
                elif Uncompress.__PATH_7Z is not None:
                    #  Unrar not available, but 7Zip is available, use it
                    return Uncompress.FORMAT_7Z

        # no tools available
        return None

    @staticmethod
    def getList(archiveFile):
        """Return list of files in archive as list of <UncompressFileInfo>

        Return None if not possible to read file content
        """
        returned = []
        format = Uncompress.preferredForFileFormat(archiveFile)
        try:
            if format == Uncompress.FORMAT_7Z:
                result = subprocess.run([Uncompress.__PATH_7Z, "l", "-bd", "-spf", archiveFile], capture_output=True)
                if result.returncode == 0:
                    lines = result.stdout.decode(errors='replace').split(os.linesep)
                    # Returned example result:
                    #
                    # 2021-03-13 18:17:08 ....A        22296        22187  dir1/file1.jpg
                    # 2021-03-13 18:17:08 D....            0            0  dir1
                    for line in lines:
                        if r := re.search(r"^(\d{4}-\d{2}-\d{2})\s(\d{2}:\d{2}:\d{2})\s([A-Z\.]{5})\s+(\d+)\s+(\d*)\s+(.*)$", line):
                            # (
                            #   '2021-03-13',               // date
                            #   '18:17:08',                 // time
                            #   '....A',                    // atrributes
                            #   '22296',                    // uncompressed size
                            #   '22187',                    // compressed size      => can be empty if SOLID archive
                            #   'dir1/file1.jpg'            // relative path/name
                            # )
                            properties = list(r.groups())
                            if properties[4] == '':
                                properties[4] = None
                            else:
                                properties[4] = int(properties[4])
                            returned.append(UncompressFileInfo(properties[5],
                                                               properties[0],
                                                               properties[1],
                                                               int(properties[3]),
                                                               properties[4],
                                                               properties[3][0] == 'D'))

                    return returned
                else:
                    # error has occurred?
                    Debug.print('[Uncompress.getList] Unable to execute LIST command: {0}', result.stderr.decode())
            elif format == Uncompress.FORMAT_RAR:
                result = subprocess.run([Uncompress.__PATH_RAR, "v", archiveFile], capture_output=True)
                if result.returncode == 0:
                    lines = result.stdout.decode(errors='replace').split(os.linesep)
                    # Returned example result:
                    #
                    #   ..A....     22296     22187  99%  2021-03-13 17:17  C1D33145  dir1/file1.jpg
                    #   ...D...         0         0   0%  2021-03-13 17:17  00000000  dir1
                    for line in lines:
                        if r := re.search(r"^\s+([A-Z\.]{7})\s+(\d+)\s+(\d+)\s+\d+%\s+(\d{4}-\d{2}-\d{2})\s(\d{2}:\d{2})\s+[A-F0-9]{8}\s+(.*)$", line):
                            # (
                            #   '..A....',
                            #   '22296',
                            #   '22187',
                            #   '2021-03-13',
                            #   '17:17',
                            #   'dir1/file1.jpg'
                            # )
                            properties = r.groups()
                            returned.append(UncompressFileInfo(properties[5],
                                                               properties[3],
                                                               f"{properties[4]}:00",
                                                               int(properties[1]),
                                                               int(properties[2]),
                                                               properties[0][3] == 'D'))

                    return returned
                else:
                    # error has occurred?
                    Debug.print('[Uncompress.getList] Unable to execute LIST command: {0}', result.stderr.decode())
        except Exception as e:
            Debug.print('[Uncompress.getList] Unable to execute LIST command: {0}', f"{e}")

        return None

    @staticmethod
    def extractAll(archiveFile, path):
        """Extract files from `archiveFile` to given `path`

        Return None if not possible to read file content, otherwise return path within file
        """
        returned = None
        format = Uncompress.preferredForFileFormat(archiveFile)
        try:
            if format == Uncompress.FORMAT_7Z:
                result = subprocess.run([Uncompress.__PATH_7Z, "x", archiveFile, "-bd", "-y", f"-o{path}"], capture_output=True)
            elif format == Uncompress.FORMAT_RAR:
                if path[-1] != os.sep:
                    path += os.sep
                result = subprocess.run([Uncompress.__PATH_RAR, "x", "-y", archiveFile, path], capture_output=True)
            else:
                return None

            if result.returncode == 0:
                return path
            else:
                # error has occurred?
                Debug.print('[Uncompress.extractAll] Unable to execute EXTRACT command: {0}', result.stderr.decode())

        except Exception as e:
            Debug.print('[Uncompress.extractAll] Unable to execute EXTRACT command: {0}', f"{e}")

        return None

    @staticmethod
    def extract(archiveFile, fileName, path):
        """Extract `fileName` from `archiveFile` to given `path`

        Given `fileName` can be a <str> or a list of <str>

        Return None if not possible to extract file content

        If given `fileName` is <str> return full path/filename of extracted file
        If given `fileName` is a list, return a list of full path/filename extracted files
        """
        returned = None
        format = Uncompress.preferredForFileFormat(archiveFile)
        try:
            asStr = False
            if isinstance(fileName, str):
                asStr = True
                fileName = [fileName]

            if not isinstance(fileName, (list, tuple)):
                raise EInvalidType("Given `fileName` must be a <str> or a list of <str>")
            elif not isinstance(path, str):
                raise EInvalidType("Given `path` must be a <str>")

            if not os.path.isdir(path):
                raise EInvalidType("Given `path` doesn't exist")

            if format == Uncompress.FORMAT_7Z:
                result = subprocess.run([Uncompress.__PATH_7Z, "x", archiveFile, "-bd", "-y", f"-o{path}", *fileName], capture_output=True)
            elif format == Uncompress.FORMAT_RAR:
                if path[-1] != os.sep:
                    path += os.sep
                result = subprocess.run([Uncompress.__PATH_RAR, "x", "-y", archiveFile, *fileName, path], capture_output=True)
            else:
                return None

            if result.returncode == 0:
                if asStr:
                    extractedFile = os.path.join(path, fileName[0])
                    if os.path.isfile(extractedFile):
                        return extractedFile
                else:
                    extractedFiles = []
                    for file in fileName:
                        extractedFile = os.path.join(path, fileName)
                        if os.path.isfile(extractedFile):
                            extractedFiles.append(extractedFile)
                    return extractedFiles
            else:
                # error has occurred?
                Debug.print('[Uncompress.extract] Unable to execute EXTRACT command: {0}', result.stderr.decode())

        except Exception as e:
            Debug.print('[Uncompress.extract] Unable to execute EXTRACT command: {0}', f"{e}")

        return None


# intialize class
Uncompress.initialize()
