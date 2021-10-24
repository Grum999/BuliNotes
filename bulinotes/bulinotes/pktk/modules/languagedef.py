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


# Buli Script language definition

from PyQt5.Qt import *
from enum import Enum

import re

from .tokenizer import (
            Token,
            TokenType,
            TokenStyle,
            Tokenizer,
            TokenizerRule
        )
from .uitheme import UITheme

from ..pktk import *

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


class LanguageDefXML(LanguageDef):
    """Extent language definition for XML markup language"""

    class ITokenType(TokenType, Enum):
        STRING = ('String', 'A STRING value')
        MARKUP = ('Markup', 'A XML Markup')
        ATTRIBUTE = ('Attribute', 'A node attribute')
        SETATTR = ('=', 'Set attribute')
        NUMBER = ('Number', 'A NUMBER value')
        CDATA = ('Data', 'A CDATA value')
        VALUE = ('Value', 'A VALUE value')

    def __init__(self):
        super(LanguageDefXML, self).__init__([
            TokenizerRule(LanguageDefXML.ITokenType.CDATA, r'<!\[CDATA\[.*\]\]>'),
            TokenizerRule(LanguageDefXML.ITokenType.STRING, r'"[^"\\]*(?:\\.[^"\\]*)*"'),
            TokenizerRule(LanguageDefXML.ITokenType.STRING, r"'[^'\\]*(?:\\.[^'\\]*)*'"),
            TokenizerRule(LanguageDefXML.ITokenType.MARKUP, r'<[a-zA-Z][a-zA-Z0-9_-]*|<\?xml|<!DOCTYPE'),
            TokenizerRule(LanguageDefXML.ITokenType.MARKUP, r'</[a-zA-Z][a-zA-Z0-9_-]*>'),
            TokenizerRule(LanguageDefXML.ITokenType.MARKUP, r'/?>|\?>'),
            TokenizerRule(LanguageDefXML.ITokenType.ATTRIBUTE, r'\s[a-zA-Z][a-zA-Z0-9_\:-]*'),
            TokenizerRule(LanguageDefXML.ITokenType.SETATTR, r'='),
            TokenizerRule(LanguageDefXML.ITokenType.NUMBER, r'-\d+|\d+'),
            TokenizerRule(LanguageDefXML.ITokenType.SPACE, r'\s+'),
            TokenizerRule(LanguageDefXML.ITokenType.VALUE, r'[^<>]+')
        ])

        self.setStyles(UITheme.DARK_THEME, [
            (LanguageDefXML.ITokenType.STRING, '#9ac07c', False, False),
            (LanguageDefXML.ITokenType.MARKUP, '#e5dd82', True, False),
            (LanguageDefXML.ITokenType.NUMBER, '#c9986a', False, False),
            (LanguageDefXML.ITokenType.ATTRIBUTE, '#e18890', False, False),
            (LanguageDefXML.ITokenType.SETATTR, '#c278da', False, False),
            (LanguageDefXML.ITokenType.CDATA, '#78dac2', False, False),
            (LanguageDefXML.ITokenType.VALUE, '#82dde5', False, False),
            (LanguageDefXML.ITokenType.SPACE, None, False, False)
        ])
        self.setStyles(UITheme.LIGHT_THEME, [
            (LanguageDefXML.ITokenType.STRING, '#9ac07c', False, False),
            (LanguageDefXML.ITokenType.MARKUP, '#e5dd82', True, False),
            (LanguageDefXML.ITokenType.NUMBER, '#c9986a', False, False),
            (LanguageDefXML.ITokenType.ATTRIBUTE, '#e18890', False, False),
            (LanguageDefXML.ITokenType.SETATTR, '#c278da', False, False),
            (LanguageDefXML.ITokenType.CDATA, '#78dac2', False, False),
            (LanguageDefXML.ITokenType.VALUE, '#82dde5', False, False),
            (LanguageDefXML.ITokenType.SPACE, None, False, False)
        ])
