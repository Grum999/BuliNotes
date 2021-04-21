#-----------------------------------------------------------------------------
# Buli Commander
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
# A Krita plugin designed to manage documents
# -----------------------------------------------------------------------------


# Buli Script language definition

from PyQt5.Qt import *

import re

from pktk.modules.tokenizer import (
            Token,
            TokenStyle,
            Tokenizer,
            TokenizerRule
        )

from pktk.pktk import (
            EInvalidType,
            EInvalidValue
        )

class LanguageDef:

    def __init__(self, rules=[], styles=[]):
        """Initialise language & styles"""
        self.__tokenizer = Tokenizer(rules)
        self.__tokenStyle = TokenStyle()

    def tokenizer(self):
        """Return tokenizer for language"""
        return self.__tokenizer

    def setStyles(self, theme, styles):
        for style in styles:
            self.__tokenStyle.setStyle(theme, *style)

    def style(self, item):
        """Return style for given token and/or rule"""
        return self.__tokenStyle.style(item.type())

    def getTextProposal(self, text, full=False):
        """Return a list of possible values for given text

        return list of tuple (str, str, rule)
            str: autoCompletion value
            str: description
            rule: current rule
        """
        if not isinstance(text, str):
            raise EInvalidType('Given `text` must be str')

        rePattern=re.compile(re.escape(re.sub('\s+', '\x02', text)).replace('\x02', r'\s+')+'.*')
        returned=[]
        for rule in self.__tokenizer.rules():
            values=rule.matchText(rePattern, full)
            if len(values)>0:
                returned+=values
        # return list without any duplicate values
        return list(set(returned))
