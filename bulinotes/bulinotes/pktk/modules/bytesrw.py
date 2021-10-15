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
import struct
import io

from PyQt5.QtCore import QByteArray

class BytesRW(io.BytesIO):
    """Provides an easy access to read/write binary data, provided functions
    doing the pack/unpack according to type

    """

    def __init__(self, blob=None):
        if isinstance(blob, QByteArray):
            super(BytesRW, self).__init__(bytes(blob))
        elif isinstance(blob, bytes):
            super(BytesRW, self).__init__(blob)
        else:
            super(BytesRW, self).__init__()

        self.__byteOrder='!' # network


    def byteOrder(self):
        """return current byte order used to pack/unpack data"""
        return self.__byteOrder


    def setByteOrder(self, value):
        """Set byte byte order used to pack/unpack data

        value can be:
            '<' or 'le' little-endian
            '>' or 'be' big-endian
            '!' or 'n'  network (big-endian)

            all other values are ignored
        """
        if value=='<' or value=='le':
            self.__byteOrder='<'
        elif value=='>' or value=='be':
            self.__byteOrder='>'
        elif value=='!' or value=='n':
            self.__byteOrder='!'


    def readBool(self):
        """Read a boolean value (1 byte)"""
        b=self.read(1)
        if len(b)==1:
            return (struct.unpack(f'{self.__byteOrder}B', b)[0]==1)
        return None


    def readShort(self):
        """Read a short signed value (1 byte)"""
        b=self.read(1)
        if len(b)==1:
            return struct.unpack(f'{self.__byteOrder}b', b)[0]
        return None


    def readUShort(self):
        """Read a short unsigned value (1 byte)"""
        b=self.read(1)
        if len(b)==1:
            return struct.unpack(f'{self.__byteOrder}B', b)[0]
        return None


    def readInt2(self):
        """Read an integer signed value (2 bytes)"""
        b=self.read(2)
        if len(b)==2:
            return struct.unpack(f'{self.__byteOrder}h', b)[0]
        return None


    def readUInt2(self):
        """Read a integer unsigned value (2 bytes)"""
        b=self.read(2)
        if len(b)==2:
            return struct.unpack(f'{self.__byteOrder}H', b)[0]
        return None


    def readInt4(self):
        """Read an integer signed value (4 bytes)"""
        b=self.read(4)
        if len(b)==4:
            return struct.unpack(f'{self.__byteOrder}i', b)[0]
        return None


    def readUInt4(self):
        """Read a integer unsigned value (4 bytes)"""
        b=self.read(4)
        if len(b)==4:
            return struct.unpack(f'{self.__byteOrder}I', b)[0]
        return None


    def readInt8(self):
        """Read an integer signed value (8 bytes)"""
        b=self.read(8)
        if len(b)==8:
            return struct.unpack(f'{self.__byteOrder}q', b)[0]
        return None


    def readUInt8(self):
        """Read a integer unsigned value (8 bytes)"""
        b=self.read(8)
        if len(b)==8:
            return struct.unpack(f'{self.__byteOrder}Q', b)[0]
        return None


    def readFloat4(self):
        """Read a float signed value (4 bytes)"""
        b=self.read(4)
        if len(b)==4:
            return struct.unpack(f'{self.__byteOrder}f', b)[0]
        return None


    def readFloat8(self):
        """Read a float signed value (8 bytes)"""
        b=self.read(8)
        if len(b)==8:
            return struct.unpack(f'{self.__byteOrder}d', b)[0]
        return None


    def readStr(self, size=None, encoding='utf-8'):
        """Read a UTF8 string

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)

        If `size` is not provided, read until EOF
        """
        if isinstance(size, int):
            b=self.read(size)
        else:
            b=self.read()
        return b.decode(encoding)


    def readPStr(self, encoding='utf-8'):
        """Read a UTF8 pascal string (1 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)
        """
        size=self.readUShort()
        if size>0:
            b=self.read(size)
            return b.decode(encoding)
        return ''


    def readPStr2(self, encoding='utf-8'):
        """Read a UTF8 pascal string (2 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)
        """
        size=self.readUInt2()
        if size>0:
            b=self.read(size)
            return b.decode(encoding)
        return ''


    def readPStr4(self, encoding='utf-8'):
        """Read a UTF8 pascal string (4 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)
        """
        size=self.readUInt4()
        if size>0:
            b=self.read(size)
            return b.decode(encoding)
        return ''


    def writeBool(self, value):
        """Write a boolean value (1 byte)"""
        if isinstance(value, bool):
            if value:
                return self.write(b'\x01')
            else:
                return self.write(b'\x00')
        return 0


    def writeShort(self, value):
        """Write a short signed value (1 byte)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}b', value)
            return self.write(b)
        return 0


    def writeUShort(self, value):
        """Write a short unsigned value (1 byte)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}B', value)
            return self.write(b)
        return 0


    def writeInt2(self, value):
        """Write an integer signed value (2 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}h', value)
            return self.write(b)
        return 0


    def writeUInt2(self, value):
        """Write a integer unsigned value (2 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}H', value)
            return self.write(b)
        return 0


    def writeInt4(self, value):
        """Write an integer signed value (4 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}i', value)
            return self.write(b)
        return 0


    def writeUInt4(self, value):
        """Write a integer unsigned value (4 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}I', value)
            return self.write(b)
        return 0


    def writeInt8(self, value):
        """Write an integer signed value (8 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}q', value)
            return self.write(b)
        return 0


    def writeUInt8(self, value):
        """Write a integer unsigned value (8 bytes)"""
        if isinstance(value, int):
            b=struct.pack(f'{self.__byteOrder}Q', value)
            return self.write(b)
        return 0


    def writeFloat4(self, value):
        """Write a float signed value (4 bytes)"""
        if isinstance(value, float):
            b=struct.pack(f'{self.__byteOrder}f', value)
            return self.write(b)
        return 0


    def writeFloat8(self, value):
        """Write a float signed value (8 bytes)"""
        if isinstance(value, float):
            b=struct.pack(f'{self.__byteOrder}d', value)
            return self.write(b)
        return 0


    def writeStr(self, value, encoding='utf-8'):
        """Write an UTF-8 string

        Given `encoding` value can be provided to write other type of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)
        """
        if isinstance(value, str):
            return self.write(value.encode(encoding))
        return 0


    def writePStr(self, value, encoding='utf-8'):
        """Write a UTF8 pascal string (4 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)

        If string length is too long, string is truncated!
        """
        b=value.encode(encoding)

        if len(b)>0xFF:
            b=b[0:256]

        w=self.writeUShort(len(b))
        if len(b)>0:
            return self.write(b)+w
        return w


    def writePStr2(self, value, encoding='utf-8'):
        """Write a UTF8 pascal string (2 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)

        If string length is too long, string is truncated!
        """
        b=value.encode(encoding)

        if len(b)>0xFFFF:
            b=b[0:0x10000]

        w=self.writeUInt2(len(b))
        if len(b)>0:
            return self.write(b)+w
        return w


    def writePStr4(self, value, encoding='utf-8'):
        """Write a UTF8 pascal string (4 byte size)

        Given `encoding` value can be provided to read other type
        of string
        (https://docs.python.org/3/library/codecs.html#standard-encodings)

        If string length is too long, string is truncated!
        """
        b=value.encode(encoding)

        if len(b)>0xFFFFFFFF:
            b=b[0:0x100000000]

        w=self.writeUInt4(len(b))
        if len(b)>0:
            return self.write(b)+w
        return w
