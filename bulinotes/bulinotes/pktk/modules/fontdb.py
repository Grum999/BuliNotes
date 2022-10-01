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
# The fontdb module provides access to system font and tries to complete
# missing methods from Qt.QFontDatabase, especially to be able to:
# - Locate file(s) from which font has been loaded
# - Determinate embeddable font status
#
# According to number of font installed on computer, initialization can be a
# little bit slow...
#
# Main class from this module
#
# - FontDatabase:
#       A class with high level methods for font management
#
# -----------------------------------------------------------------------------


from PyQt5.Qt import *
import sys
import re
import os.path

from .bytesrw import BytesRW
from .utils import Debug


class FontDatabase:
    """Qt.QFontDatabase is not complete for font management, especially to be able to:
    - Locate file(s) from which font has been loaded
    - Determinate embeddable font status

    The PkTk FontDatabase provides methods for that
    """

    __initialized = False

    # windows font path
    __WIN_PATHS = [r'c:\windows\fonts']

    # linux additional system paths
    __X11_PATHS = ['/usr/share/fonts',
                   '/usr/local/share/fonts']

    # OSX font paths
    __OSX_PATHS = ['/Library/Fonts',
                   '/Network/Library/Fonts',
                   '/System/Library/Fonts',
                   '/opt/local/share/fonts']

    @staticmethod
    def __initialize():
        """Initialise database"""
        if FontDatabase.__initialized:
            return

        # get an instance of Qt font database
        FontDatabase.__qFontDatabase = QFontDatabase()

        FontDatabase.__paths = QStandardPaths.standardLocations(QStandardPaths.FontsLocation)
        FontDatabase.__fontsByName = {}
        FontDatabase.__fontsByFile = {}

        if sys.platform == 'linux':
            FontDatabase.__addPaths(FontDatabase.__X11_PATHS)
        elif sys.platform == 'darwin':
            # OSX
            FontDatabase.__addPaths(FontDatabase.__OSX_PATHS)
        elif sys.platform == 'win32':
            # Windows
            FontDatabase.__paths = [os.path.normpath(path.lower()) for path in FontDatabase.__paths]
            FontDatabase.__addPaths(FontDatabase.__WIN_PATHS)

        FontDatabase.__loadFonts()
        FontDatabase.__initialized = True

    @staticmethod
    def __addPaths(paths):
        """Add given paths to current database paths"""
        for path in paths:
            if path not in FontDatabase.__paths:
                FontDatabase.__paths.append(path)

    @staticmethod
    def __fullPath(fileName):
        """Check if given file name exists

        Otherwise try to check for file name in known fonts directories

        Return full path/file name or None if unable to find file
        """
        if os.path.isfile(fileName):
            return os.path.normpath(fileName)

        for path in FontDatabase.__paths:
            fullPathFileName = os.path.normpath(os.path.join(path, fileName))
            if os.path.isfile(fullPathFileName):
                return fullPathFileName
        return None

    @staticmethod
    def __loadFonts():
        """Initialise database from fonts directories"""
        # scan all directories to look for fonts
        fileList = []
        for dirName in FontDatabase.__paths:
            for path, subdirs, files in os.walk(dirName):
                for name in files:
                    if re.search(r"\.(ttf|ttc|otf|otc|pfb)", name):
                        # load font file
                        font = Font(os.path.normpath(os.path.join(path, name)))

                        if font.type() not in (Font.TYPE_NOTREADABLE, Font.TYPE_UNKNOWN):
                            FontDatabase.__addFontFile(font)
                            FontDatabase.__addFontName(font)

    @staticmethod
    def __addFontFile(font):
        """Add font to database, referenced by file name"""
        FontDatabase.__fontsByFile[font.fileName()] = font

    @staticmethod
    def __addFontName(font):
        """Add font to database, referenced by file name"""
        if font.type() == Font.TYPE_OPENTYPE_TTC:
            # a collection, add all fonts
            for fontFromCollection in font.property(Font.PROPERTY_COLLECTION_FONTS):
                FontDatabase.__addFontName(fontFromCollection)
        else:
            fontName = font.property(Font.PROPERTY_FAMILY_NAME)
            fontTypoName = font.property(Font.PROPERTY_TYPO_FAMILY_NAME)

            if fontName is None:
                fontName = font.property(Font.PROPERTY_FULLNAME)

            fontNameList = []
            if fontName is not None:
                fontNameList.append(fontName)

            if fontTypoName is not None and fontTypoName not in fontNameList:
                fontNameList.append(fontTypoName)

            for fontName in fontNameList:
                if fontName not in FontDatabase.__fontsByName:
                    FontDatabase.__fontsByName[fontName] = []
                FontDatabase.__fontsByName[fontName].append(font)

    @staticmethod
    def font(name):
        """Return font objects for given `name`

        A list of Font() object matching given `name` is returned
        """
        if not isinstance(name, str):
            raise EInvalidType("Given `name` must be <str>")

        FontDatabase.__initialize()

        noFoundryName = None
        if r := re.search(r"(.*)\s\[[^\]]+\]$", name):
            # a foundry name is present in given font name?
            # get name without foundt name
            noFoundryName = r.groups()[0]

        if name in FontDatabase.__fontsByName:
            return FontDatabase.__fontsByName[name]
        elif noFoundryName and noFoundryName in FontDatabase.__fontsByName:
            return FontDatabase.__fontsByName[noFoundryName]
        else:
            return []

    @staticmethod
    def installed(name):
        """Return True if font is installed

        - available from QFontDatabase
        - available from font files
        """
        return (name in FontDatabase.__fontsByName) and (name in FontDatabase.__qFontDatabase.families())

    @staticmethod
    def fonts():
        """Return all fonts as dictionnary, with font name as key"""
        FontDatabase.__initialize()
        return FontDatabase.__fontsByName

    @staticmethod
    def files():
        """Return all fonts as dictionnary, with file name as key"""
        FontDatabase.__initialize()
        return FontDatabase.__fontsByFile

    @staticmethod
    def paths():
        """Return paths from where font has been loaded"""
        FontDatabase.__initialize()
        return FontDatabase.__paths

    @staticmethod
    def qFontDatabase():
        """Return instance on an QFontDatabase"""
        return FontDatabase.__qFontDatabase


class Font:
    """A font definition"""
    # Font specifications
    #   https://docs.microsoft.com/en-us/typography/opentype/spec/otff
    #   https://docs.microsoft.com/en-us/typography/opentype/spec/otff#collections

    TYPE_NOTREADABLE = 'Not readable'
    TYPE_UNKNOWN = 'Unknown'
    TYPE_OPENTYPE_TTF = 'OpenType (TrueType)'
    TYPE_OPENTYPE_CFF = 'OpenType (Compact Font Format)'
    TYPE_OPENTYPE_TTC = 'OpenType (Collection)'
    TYPE_TYPE1 = 'Type1'

    PROPERTY_COPYRIGHT =             0x00000000
    PROPERTY_FAMILY_NAME =           0x00000001
    PROPERTY_SUBFAMILY_NAME =        0x00000002
    PROPERTY_UNIQUEID =              0x00000003
    PROPERTY_FULLNAME =              0x00000004
    PROPERTY_VERSION =               0x00000005
    PROPERTY_PSNAME =                0x00000006
    PROPERTY_TRADEMARK =             0x00000007
    PROPERTY_MANUFACTURER_NAME =     0x00000008
    PROPERTY_DESIGNER =              0x00000009
    PROPERTY_DESCRIPTION =           0x0000000A
    PROPERTY_URLVENDOR =             0x0000000B
    PROPERTY_URLDESIGNER =           0x0000000C
    PROPERTY_LICENSE_DESCRIPTION =   0x0000000D
    PROPERTY_LICENSE_NFOURL =        0x0000000E
    PROPERTY_TYPO_FAMILY_NAME =      0x00000010
    PROPERTY_TYPO_SUBFAMILY_NAME =   0x00000011

    PROPERTY_COLLECTION_COUNT =      0x01000000
    PROPERTY_COLLECTION_FONTS =      0x01000001

    PROPERTY_FILE_SIZE =             0x02000000
    PROPERTY_FILE_DATE =             0x02000001

    PROPERTY_NAMES = {
            # Usual values only (list is not complete)
            #   https://docs.microsoft.com/en-us/typography/opentype/spec/name
            0x00000000: i18n("Copyright notice"),
            0x00000001: i18n("Font Family name"),
            0x00000002: i18n("Font Subfamily name"),
            0x00000003: i18n("Unique font identifier"),
            0x00000004: i18n("Full font name"),
            0x00000005: i18n("Version"),
            0x00000006: i18n("PostScript name"),
            0x00000007: i18n("Trademark"),
            0x00000008: i18n("Manufacturer Name"),
            0x00000009: i18n("Designer"),
            0x0000000A: i18n("Description"),
            0x0000000B: i18n("Vendor URL"),
            0x0000000C: i18n("Designer URL"),
            0x0000000D: i18n("License Description"),
            0x0000000E: i18n("License Info URL"),
            0x00000010: i18n("Typographic Family name"),
            0x00000011: i18n("Typographic Subfamily name"),

            0x01000000: i18n("Collection (count)"),
            0x01000001: i18n("Collection (fonts)"),

            0x02000000: i18n("File (size)"),
            0x02000001: i18n("File (date/time)")
        }

    __RECORD_OFFSET = 0
    __RECORD_LENGTH = 1

    __NAMERECORD_PLATFORM_ID = 0
    __NAMERECORD_ENCODING_ID = 1
    __NAMERECORD_LANGUAGE_ID = 2
    __NAMERECORD_NAME_ID = 3

    # interesting tags for
    __TAG_OS2 = b'OS/2'
    __TAG_NAME = b'name'

    def __init__(self, fileName, data=None):
        self.__propFileName = fileName
        self.__propFontType = Font.TYPE_NOTREADABLE
        self.__propEmbeddingState = None
        self.__propStrings = {}
        self.__collection = []
        self.__fileContent = b''

        if isinstance(data, dict):
            # initialise Font from data
            self.__propFontType = data['__propFontType']
            self.__propEmbeddingState = data['__propEmbeddingState']
            self.__propStrings = data['__propStrings']
        elif isinstance(data, bytes):
            # load font from bytes string
            # qDebug(f'Font from data {fileName} ({len(data)})')
            self.__fileContent = data
            self.__reader = None
            self.__tableRecord = {}
            self.__loadFont()
        else:
            # initialise Font from file name (load font file and do analysis)
            self.__reader = None
            self.__tableRecord = {}

            if not os.path.isfile(self.__propFileName):
                return

            self.__loadFont()

    def __repr__(self):
        if self.__propFontType not in (Font.TYPE_OPENTYPE_TTC, Font.TYPE_OPENTYPE_TTF, Font.TYPE_OPENTYPE_CFF, Font.TYPE_TYPE1):
            return f"<Font('{self.__propFileName}', {self.__propFontType})>"
        else:
            es = self.embeddingState()
            returned = [f"<Font('{self.__propFileName}', {self.__propFontType}",
                        f"      {es[1]}: {es[2]}"]

            for property in self.__propStrings:
                returned.append(f"      {Font.PROPERTY_NAMES[property]}: '{self.__propStrings[property]}'")

            returned.append(")>")

            return "\n".join(returned)

    def __eq__(self, value):
        """Check equality for font"""
        if isinstance(value, str):
            return self.__
        else:
            return super(Font, self).__eq__(value)

    def __loadFont(self):
        """Load font definition"""
        fileContent = self.getFileContent()

        if fileContent == b'':
            return

        self.__propStrings[Font.PROPERTY_FILE_SIZE] = len(fileContent)
        try:
            self.__propStrings[Font.PROPERTY_FILE_DATE] = os.path.getmtime(self.__propFileName)
        except Exception:
            pass

        if len(fileContent) == 0:
            return

        self.__propFontType = Font.TYPE_UNKNOWN

        # initialise reader
        self.__reader = BytesRW(fileContent)

        # load font properties
        # --------------------
        if not self.__loadOpenType():
            if not self.__loadOpenTypeCollection():
                self.__loadAdobeType()

        self.__reader.close()

    def __loadAdobeType(self):
        """Try to load font as adobe type 1 font

        Return True if loaded, otherwise False
        """
        # https://github.com/holzschu/lib-tex/blob/master/texk/ps2pk/pfb2pfa.c
        # try:
        # ensure to start reading from first byte
        self.__reader.seek(0, os.SEEK_SET)

        fntId_magicHeader = self.__reader.readUShort()
        if fntId_magicHeader != 0x80:
            # 0x80 => pfb file
            return False

        fntId_type = self.__reader.readShort()
        if fntId_type == 1:
            # Adobe Type 1

            fntId_length = self.__reader.readUInt4()

            fntId_comment = self.__reader.read(2)
            if fntId_comment != b'%!':
                return False

            self.__reader.seek(-2, os.SEEK_CUR)

            self.__propEmbeddingState = 16

            self.__loadAdobeType_Comments()
            self.__loadAdobeType_Dictionnary()
        else:
            # type not managed!
            return False

        self.__propFontType = Font.TYPE_TYPE1
        return True

    def __loadAdobeType_readLine(self):
        """Read a line

        Stop on \n or \r or \r\n
        """
        returned = b''
        while True:
            chr = self.__reader.read(1)
            if chr == b'\n' or chr == b'':
                return returned
            elif chr == b'\r':
                chr = self.__reader.read(1)
                if chr != 0x0A:
                    self.__reader.seek(-1, os.SEEK_CUR)
                return returned
            returned += chr

    def __loadAdobeType_Comments(self):
        """Load adobe type1 comments"""
        # just skip comments...
        while True:
            line = self.__loadAdobeType_readLine()
            if line != b'' and line[0] != 0x25:
                return

    def __loadAdobeType_Dictionnary(self):
        """Load adobe type1 dictionary"""
        # just skip comments...
        while True:
            line = self.__loadAdobeType_readLine()
            line = line.decode('utf-8', 'ignore')

            if r := re.search(r"^/FontName\s+/(.*)\sdef$", line):
                self.__propStrings[Font.PROPERTY_PSNAME] = r.groups()[0]
            elif r := re.search(r"^/UniqueID\s+/(.*)\sdef$", line):
                self.__propStrings[Font.PROPERTY_UNIQUEID] = r.groups()[0].strip('() ')
            elif r := re.search(r"^\s*/version\s+(.+).*readonly\sdef$", line):
                self.__propStrings[Font.PROPERTY_VERSION] = r.groups()[0].strip('() ')
            elif r := re.search(r"^\s*/Notice\s+(.+).*readonly\sdef$", line):
                self.__propStrings[Font.PROPERTY_COPYRIGHT] = r.groups()[0].strip('() ')
            elif r := re.search(r"^\s*/FullName\s+(.+).*readonly\sdef$", line):
                self.__propStrings[Font.PROPERTY_FULLNAME] = r.groups()[0].strip('() ')
            elif r := re.search(r"^\s*/FamilyName\s+(.+).*readonly\sdef$", line):
                self.__propStrings[Font.PROPERTY_FAMILY_NAME] = r.groups()[0].strip('() ')
            elif r := re.search(r"^\s*/FSType\s+(\d+)", line):
                # same as for OpenType?
                self.__propEmbeddingState = int(r.groups()[0])
            elif re.search(r"eexec$", line):
                return

    def __loadOpenType(self, offset=0):
        """Try to load font as opentype font

        Return True if loaded, otherwise False
        """
        try:
            # ensure to start reading from first byte
            self.__reader.seek(offset, os.SEEK_SET)

            # read sfntVersion
            fntId_sfntVersion = self.__reader.readUInt4()
            if not(fntId_sfntVersion == 0x00010000 or     # open type (TrueType)
                   fntId_sfntVersion == 0x4F54544F):      # open type (CFF data - version 1 or 2)
                return False

            # read numTables
            fntId_numTables = self.__reader.readUInt2()

            # go directly to tableRecord
            self.__reader.seek(6, os.SEEK_CUR)

            # load table records
            self.__loadOpenType_FontTableRecord(fntId_numTables)

            # load 'OS/2' record (determinate if font can be embedded or not)
            self.__loadOpenType_loadTag_OS2()

            # load 'name' record (determinate font name & license)
            self.__loadOpenType_loadTag_name()

            if fntId_sfntVersion == 0x00010000:
                self.__propFontType = Font.TYPE_OPENTYPE_TTF
            else:
                self.__propFontType = Font.TYPE_OPENTYPE_CFF
            return True
        except Exception as e:
            Debug.print('Font.__loadOpenType()', e)
            return False

    def __loadOpenTypeCollection(self):
        """Try to load font as opentype collection font

        Return True if loaded, otherwise False
        """
        try:
            # ensure to start reading from first byte
            self.__reader.seek(0, os.SEEK_SET)

            # read sfntVersion
            fntId_sfntVersion = self.__reader.readUInt4()
            if fntId_sfntVersion != 0x74746366:
                return False

            # get file format version
            fntId_version = self.__reader.readUInt4()

            # number of font in collection
            fntId_numFont = self.__reader.readUInt4()

            fntId_fontOffset = []
            for fontNumber in range(fntId_numFont):
                fntId_fontOffset.append(self.__reader.readUInt4())

            if fntId_numFont == 0x00020000:
                # file format version 2
                # skip digital signature
                self.__read.seek(12, os.SEEK_CUR)

            propEmbeddingState = 0
            for fontOffset in fntId_fontOffset:
                if self.__loadOpenType(fontOffset):
                    self.__collection.append(Font(self.__propFileName, {
                        '__propFontType': self.__propFontType,
                        '__propEmbeddingState': self.__propEmbeddingState,
                        '__propStrings': self.__propStrings
                    }))

                # for embedding state, as each font in collection can have their own embeddable definition
                # need to return the most restrictive from collection
                if self.__propEmbeddingState == 2:
                    propEmbeddingState = 2
                elif self.__propEmbeddingState == 4 and propEmbeddingState in (0, 8):
                    propEmbeddingState = 4
                elif self.__propEmbeddingState == 8 and propEmbeddingState == 0:
                    propEmbeddingState = 8

                self.__propStrings = {}

            self.__propEmbeddingState = propEmbeddingState
            self.__propStrings = {
                    Font.PROPERTY_COLLECTION_COUNT: len(self.__collection),
                    Font.PROPERTY_COLLECTION_FONTS: self.__collection
                }
            self.__propFontType = Font.TYPE_OPENTYPE_TTC
            return True
        except Exception as e:
            Debug.print('Font.__loadOpenTypeCollection()', e)
            return False

    def __loadOpenType_FontTableRecord(self, numTables):
        """Load font table record"""
        self.__tableRecord = {}

        for tableNumber in range(numTables):
            # table tag identifier
            fntId_Tag = self.__reader.read(4)

            # skip checksum
            self.__reader.seek(4, os.SEEK_CUR)

            # offset of record in font file, from beggining of font file
            fntId_offset = self.__reader.readUInt4()
            # length of record
            fntId_length = self.__reader.readUInt4()

            self.__tableRecord[fntId_Tag] = {
                    Font.__RECORD_OFFSET: fntId_offset,
                    Font.__RECORD_LENGTH: fntId_length,
                }

    def __loadOpenType_seekRecord(self, record):
        """Seek directly to a given record"""
        self.__reader.seek(record[Font.__RECORD_OFFSET], os.SEEK_SET)

    def __loadOpenType_loadTag_OS2(self):
        """Load tag 'OS/2'

        Only embedding flag is retrieved; other properties are ignored
        """
        if Font.__TAG_OS2 not in self.__tableRecord:
            return

        self.__loadOpenType_seekRecord(self.__tableRecord[Font.__TAG_OS2])

        # go to fsType
        self.__reader.seek(8, os.SEEK_CUR)

        # read fsType
        fntId_fsType = self.__reader.readUInt2()
        self.__propEmbeddingState = fntId_fsType & 0x000F

    def __loadOpenType_loadTag_name(self):
        """Load tag 'name'

        Contains strings properties
        """
        if Font.__TAG_NAME not in self.__tableRecord:
            return

        self.__loadOpenType_seekRecord(self.__tableRecord[Font.__TAG_NAME])

        currentPosition = self.__reader.tell()

        # read naming table version
        fntId_version = self.__reader.readUInt2()
        # read number of table records
        fntId_count = self.__reader.readUInt2()
        # read offset for storage of records (from start of table).
        fntId_offset = self.__reader.readUInt2()

        if fntId_version == 1:
            # skip language tag records
            fntId_langTagCount = self.__reader.readUInt2()
            self.__reader.seek(fntId_langTagCount*4, os.SEEK_CUR)

        fntId_nameRecords = {}
        for nameRecordIndex in range(fntId_count):
            uid = (
                    self.__reader.readUInt2(),  # platform Id
                    self.__reader.readUInt2(),  # platform encoding Id
                    self.__reader.readUInt2(),  # language Id
                    self.__reader.readUInt2()   # name Id
                )

            fntId_nameRecords[uid] = {
                    Font.__RECORD_LENGTH: self.__reader.readUInt2(),
                    Font.__RECORD_OFFSET: self.__reader.readUInt2(),    # from start of storage
                }

        # memorize start of storage position
        startOfStorage = self.__reader.tell()

        for recordUid in fntId_nameRecords:
            self.__reader.seek(startOfStorage+fntId_nameRecords[recordUid][Font.__RECORD_OFFSET], os.SEEK_SET)

            if recordUid[3] not in Font.PROPERTY_NAMES:
                # ignore record names we don't manage
                continue

            if recordUid[0] == 0:
                # Platform Id = 0 => Unicode
                if recordUid[1] == 0 and recordUid[2] == 0:
                    # encoding unicode 1.0 / english
                    self.__propStrings[recordUid[3]] = self.__reader.readStr(fntId_nameRecords[recordUid][Font.__RECORD_LENGTH], 'utf-8', 'ignore').strip()
            elif recordUid[0] == 1:
                # Platform Id = 1 => Macintosh / english
                if recordUid[1] == 0 and recordUid[2] == 0:
                    # encoding Roman; ignore other encoding
                    self.__propStrings[recordUid[3]] = self.__reader.readStr(fntId_nameRecords[recordUid][Font.__RECORD_LENGTH], 'utf-8', 'ignore').strip()
            elif recordUid[0] == 3 and recordUid[2]in (0x0809, 0x0409):
                # Platform Id = 3 => Windows / English
                if recordUid[1] == 1:
                    # encoding Unicode BMP
                    self.__propStrings[recordUid[3]] = self.__reader.readStr(fntId_nameRecords[recordUid][Font.__RECORD_LENGTH], 'utf-16be', 'ignore').strip()
                else:
                    self.__propStrings[recordUid[3]] = self.__reader.readStr(fntId_nameRecords[recordUid][Font.__RECORD_LENGTH], 'utf-8', 'ignore').strip()

    def fileName(self):
        """Return font file name"""
        return self.__propFileName

    def embeddingState(self):
        """Return readable description of embedding state value

        Return value is a tuple:
         0: Integer value for status (read from font file, or None if not found)
                0, 2, 4, 8: True Type codes
         1: Embedding state
         2: Embedding state description

        """
        if self.__propEmbeddingState == 0:
            return (self.__propEmbeddingState,
                    i18n("Installable"),
                    i18n("The font may be embedded, and may be permanently installed for use on a remote systems, or for use by other users.\nThe user of the remote system "
                         "acquires the identical rights, obligations and licenses for that font as the original purchaser of the font, and is subject to the same end-user "
                         "license agreement, copyright, design patent, and/or trademark as was the original purchaser."))
        elif self.__propEmbeddingState == 2:
            return (self.__propEmbeddingState,
                    i18n("Restricted"),
                    i18n("The font must not be modified, embedded or exchanged in any manner without first obtaining explicit permission of the legal owner."))
        elif self.__propEmbeddingState == 4:
            return (self.__propEmbeddingState,
                    i18n("Preview & Print"),
                    i18n("The font may be embedded, and may be temporarily loaded on other systems for purposes of viewing or printing the document.\n"
                         "Documents containing Preview & Print fonts must be opened “read-only”; no edits can be applied to the document."))
        elif self.__propEmbeddingState == 8:
            return (self.__propEmbeddingState,
                    i18n("Editable"),
                    i18n("The font may be embedded, and may be temporarily loaded on other systems.\n"
                         "As with Preview & Print embedding, documents containing Editable fonts may be opened for reading.\n"
                         "In addition, editing is permitted, including ability to format new text using the embedded font, and changes may be saved."))
        else:
            return (self.__propEmbeddingState,
                    i18n("Unknown"),
                    i18n("No information are available from font to determinate if it can be embedded or not, or not able to retrieve font informations."))

    def type(self):
        """Return font type"""
        return self.__propFontType

    def property(self, id=None):
        """Return property value

        If given `id` is None, return all properties
        If given `id` is not valid, return None
        """
        if id is None:
            return self.__propStrings
        elif id in self.__propStrings:
            return self.__propStrings[id]
        else:
            return None

    def getFileContent(self):
        """Return font file content as bytes"""
        if self.__fileContent != b'':
            # qDebug(f'getFileContent: return internal data ({len(self.__fileContent)}) -- {self.__propFileName}')
            return self.__fileContent

        # qDebug(f'getFileContent: return file data')
        returned = b''
        try:
            with open(self.__propFileName, mode='rb') as file:
                returned = file.read()
        except Exception as e:
            Debug.print('Font.getFileContent()', e)

        return returned
