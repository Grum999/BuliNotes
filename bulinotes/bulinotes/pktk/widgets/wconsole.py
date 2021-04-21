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
from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )
from PyQt5.QtWidgets import (
        QWidget
    )


class WConsole(QPlainTextEdit):
    """A console output (no input...)"""

    COLORS={
            'warning': '#FF00FF',
            'error': '#FF0000',
            'info': '#FFFF00',
            'normal': '#FFFFFF',
            'ok': '#00FF00',
            'ignore': '#00FFFF'
        }

    def __init__(self, parent=None):
        super(WConsole, self).__init__(parent)

        self.setStyleSheet("WConsole { background: #000000; color: #ffffff;}")

    def appendLine(self, text):
        """Append a new line to console"""
        self.appendHtml(text)

    def append(self, text, style=None):
        """Append to current line"""
        if isinstance(text, str):
            self.moveCursor(QTextCursor.End)
            lstyle=style.lower()
            if lstyle in WConsole.COLORS:
                self.textCursor().insertHtml(f"<font color='{WConsole.COLORS[lstyle]}'>{text}</font>")
            else:
                self.textCursor().insertHtml(text)
            self.moveCursor(QTextCursor.End)
        elif isinstance(text, list):
            for item in text:
                if isinstance(item, str):
                    self.append(item, style)
                elif isinstance(item, tuple):
                    self.append(item[0], item[1])
