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
# The tokenizer module provides a generic tokenizer and tools needed to
# define grammar
# (Works with languagedef + tokenizer modules)
# (that can be tokenized and parsed --> tokenizer + parser modules)
# Main class from this module
#
# - Tokenizer:
#       The tokenizer (need rules to tokenize)
#       Usually, language definition instanciate tokenizer and provides rules
#
# - Token:
#       A token built from given text and language definition
#
# - TokenizerRule:
#       A class that define a basic rule to produce a Token from text
#       Language definition are built with TokenizerRule items
#
# -----------------------------------------------------------------------------

from enum import Enum

import hashlib
import re
import time

from PyQt5.Qt import *
from .elist import EList
from .uitheme import UITheme
from ..pktk import *


class TokenType(Enum):
    # some default token type
    UNKNOWN = ('Unknown', 'This value is not know in grammar and might not be interpreted')
    NEWLINE = ('New line', 'A line feed')
    SPACE = ('Space', 'Space(s) character(s)')
    INDENT = ('Indent', 'An indented block start')
    DEDENT = ('Dedent', 'An indented block finished')
    WRONG_INDENT = ('WrongIndent', 'An indent is found but doesn\'t match expected indentation value')
    WRONG_DEDENT = ('WrongDedent', 'An dedent is found but doesn\'t match expected indentation value')
    COMMENT = ('Comment', 'A comment text')

    def id(self, **param):
        """Return token Id value"""
        if isinstance(param, dict):
            return self.value[0].format(**param)
        else:
            return self.value[0]

    def description(self, **param):
        """Return token description"""
        if isinstance(param, dict):
            return self.value[1].format(**param)
        else:
            return self.value[1]


class TokenStyle:
    """Define styles applied for tokens types"""

    def __init__(self, styles=[]):
        """Initialise token family"""
        self.__currentThemeId = UITheme.DARK_THEME

        # define default styles for tokens
        self.__tokenStyles = {}

        styles = {
                UITheme.DARK_THEME: [
                        (TokenType.UNKNOWN, '#d85151', True, True, '#7b1b1b'),
                        (TokenType.NEWLINE, None, False, False)
                    ],
                UITheme.LIGHT_THEME: [
                        (TokenType.UNKNOWN, '#d85151', True, True, '#7b1b1b'),
                        (TokenType.NEWLINE, None, False, False)
                    ]
            }

        for style in styles:
            for definition in styles[style]:
                self.setStyle(style, *definition)

    def style(self, type):
        """Return style to apply for a token type"""
        if isinstance(type, TokenType):
            if type in self.__tokenStyles[self.__currentThemeId]:
                return self.__tokenStyles[self.__currentThemeId][type]
        # in all other case, token style is not known...
        return self.__tokenStyles[self.__currentThemeId][TokenType.UNKNOWN]

    def setStyle(self, themeId, tokenType, fgColor, bold, italic, bgColor=None):
        """Define style for a token family"""
        textFmt = QTextCharFormat()
        textFmt.setFontItalic(italic)
        if bold:
            textFmt.setFontWeight(QFont.Bold)

        if fgColor is not None:
            textFmt.setForeground(QColor(fgColor))
        if bgColor is not None:
            textFmt.setBackground(QColor(bgColor))

        if themeId not in self.__tokenStyles:
            self.__tokenStyles[themeId] = {}

        self.__tokenStyles[themeId][tokenType] = textFmt

    def theme(self):
        """Return current defined theme"""
        return self.__currentThemeId

    def setTheme(self, themeId):
        """Set current theme

        If theme doesn't exist, current theme is not changed"""
        if themeId in self.__currentThemeId:
            self.__currentThemeId = themeId


class Token(object):
    """A token

    Once created, can't be changed

    A token have the following properties:
    - a type
    - a value
    - position (column and row) from original text
    """
    __LINE_NUMBER = 0
    __LINE_POSSTART = 0

    @staticmethod
    def resetTokenizer():
        Token.__LINE_NUMBER = 1
        Token.__LINE_POSSTART = 0

    def __init__(self, text, rule, positionStart, positionEnd, length, simplifySpaces=False):
        self.__text = text.lstrip()
        self.__rule = rule
        self.__positionStart = positionStart
        self.__positionEnd = positionEnd
        self.__length = length
        self.__lineNumber = Token.__LINE_NUMBER
        self.__linePositionStart = (positionStart - Token.__LINE_POSSTART)+1
        self.__linePositionEnd = self.__linePositionStart + length
        self.__next = None
        self.__previous = None
        self.__simplifySpaces = simplifySpaces

        if self.type() == TokenType.NEWLINE:
            self.__indent = 0
            Token.__LINE_NUMBER += text.count('\n')
            Token.__LINE_POSSTART = positionEnd
        else:
            self.__indent = len(text) - len(self.__text)

        if simplifySpaces and self.type() != TokenType.COMMENT:
            # do not simplify COMMENT token
            self.__text = re.sub(r"\s+", " ", self.__text)

        self.__caseInsensitive = self.__rule.caseInsensitive()
        self.__iText = self.__text.lower()

        self.__value = self.__rule.initValue(self.__text)

    def __repr__(self):
        if self.type() == TokenType.NEWLINE:
            txt = ''
        else:
            txt = self.__text
        return (f"<Token({self.__indent}, '{txt}', Type[{self.type()}]"
                f"Length: {self.__length}, "
                f"Global[Start: {self.__positionStart}, End: {self.__positionEnd}], "
                f"Line[Start: {self.__linePositionStart}, End: {self.__linePositionEnd}, Number: {self.__lineNumber}])>")

    def __str__(self):
        return f'| {self.__linePositionStart:>5} | {self.__lineNumber:>5} | {self.__indent:>2} | {self.type():<50} | {self.__length:>2} | `{self.__text}`'

    def type(self):
        """return token type"""
        return self.__rule.type()

    def positionStart(self):
        """Return position (start) in text"""
        return self.__positionStart

    def positionEnd(self):
        """Return position (end) in text"""
        return self.__positionEnd

    def length(self):
        """Return text length"""
        return self.__length

    def indent(self):
        """Return token indentation"""
        return self.__indent

    def text(self):
        """Return token text"""
        return self.__text

    def value(self):
        """Return token value

        Value can differ from text:
        - text is raw text, provided as string value
        - value is a pre-processed text
        """
        return self.__value

    def rule(self):
        """Return token rule"""
        return self.__rule

    def setNext(self, token=None):
        """Set next token"""
        self.__next = token

    def setPrevious(self, token=None):
        """Set previous token"""
        self.__previous = token

    def next(self):
        """Return next token, or None if current token is the last one"""
        return self.__next

    def previous(self):
        """Return previous token, or None if current token is the last one"""
        return self.__previous

    def column(self):
        """Return column number for token"""
        return self.__linePositionStart

    def row(self):
        """Return row number for token"""
        return self.__lineNumber

    def isUnknown(self):
        """return if it's an unknown token"""
        return (self.__rule.type() == TokenType.UNKNOWN)

    def simplifySpaces(self):
        """Return if spaces are simplified or not"""
        return self.__simplifySpaces

    def equal(self, value, doLower=False, caseInsensitive=None):
        """Check if given text `value` equals or not text value from token

        If given `value` is a list, check if token text is in given list

        If `doLower` is True, equal() will lowercase value before comparison (if case insensitive)
        If False, consider that when equal function is called, value are already provided as lowercase
        (avoid to lowercase on each call can improve performance)

        This method take in account if the rule is case sensitive or not
        If `caseInsensitive` is provided (True or False) it will overrides the rule defined by tokenizerule
        Otherwise (None value) comparison will use the rule defined by tokenizerule
        """
        if caseInsensitive is None:
            checkCaseInsensitive = self.__caseInsensitive
        else:
            checkCaseInsensitive = (caseInsensitive is True)

        if isinstance(value, str):
            if checkCaseInsensitive:
                if doLower:
                    value = value.lower()

                return (self.__iText == value)
            else:
                return (self.__text == value)
        elif isinstance(value, list) or isinstance(value, tuple):
            if checkCaseInsensitive:
                if doLower:
                    lValue = [v.lower() for v in value]
                    return (self.__iText in lValue)
                return (self.__iText in value)
            else:
                return (self.__text in value)


class Tokens(EList):
    """A tokenized text with facilities to access and parse tokens"""

    def __init__(self, text, tokens):
        super(Tokens, self).__init__(tokens)

        self.__text = None

        if isinstance(text, str):
            self.__text = text
        else:
            raise Exception('Given `text` must be a <str>')

    def __repr__(self):
        nl = '\n'
        return f"<Tokens({self.length()}, [{nl}{f'{nl}'.join([f'{token}' for token in self.list()])}{nl}])>"

    def text(self):
        """Return original tokenized text"""
        return self.__text

    def inText(self, displayPosition=False, reference=None):
        """Return current token in text

        if `reference` is provided, return text for the given reference
        can be:
        - a tuple(column, row)
        - a token
        - None (in this case, return information for current token)

        """
        col = 0
        row = 0
        length = 1
        outsideArrowRight = ">"

        if reference is None:
            if self.value() is None:
                if self.last(False) is None:
                    # nothing to return
                    return ""
                else:
                    # need to set position after last token in this case
                    token = self.last(False)
                    col = token.column() + token.length()
                    row = token.row() - 1       # as token start to row 1, and here we start to row 0
                    length = 1
                    outsideArrowRight = "^"
            else:
                col = self.value().column() - 1  # as token start to col 1, and here we start to col 0
                row = self.value().row() - 1     # as token start to row 1, and here we start to row 0
                length = self.value().length()
        elif isinstance(reference, Token):
            col = reference.column() - 1        # as token start to col 1, and here we start to col 0
            row = reference.row() - 1           # as token start to row 1, and here we start to row 0
            length = reference.length()
        elif isinstance(reference, tuple):
            if len(reference) >= 2 and isinstance(reference[0], int):
                col = reference[0]
            else:
                raise Exception("Given `reference` must be a <tuple(<int>,<int>)>")

            if len(reference) >= 2 and isinstance(reference[1], int):
                row = reference[1]
            else:
                raise Exception("Given `reference` must be a <tuple(<int>,<int>)>")

            if len(reference) >= 3 and isinstance(reference[3], int):
                length = max(1, reference[1])
        else:
            raise Exception("When given, `reference` must be a <Token> or <tuple(<int>,<int>)>")

        rows = self.__text.split('\n')

        returned = []
        if row >= 0 and row < len(rows):
            if displayPosition:
                returned.append(f'At position ({col}, {row}):')

            returned.append(rows[row])

            if col >= 0 and col < len(rows[row]):
                returned.append(('.' * col) + ('^' * length))
            elif col < 0:
                returned.append('<--')
            else:
                returned.append(('-' * len(rows[row])) + outsideArrowRight)

            return '\n'.join(returned)
        else:
            return f"Given position ({col}, {row}) is outside text"

    def tokenAt(self, col, row):
        """Return token for given row/col (start from 1/1)

        Return None if nothing to return
        """
        token = self.first(False)

        while token and token.row() < row:
            # continue to next tokens
            token = token.next()

        # tokens from row
        while token and token.row() == row and token.column() <= col:
            if token.column() <= col and col < token.column() + token.length():
                return token
            token = token.next()

        return None


class TokenizerRule(object):
    """Define a rule used by tokenizer to build a token

    A tokenizer rule is defined by:
    - A regular expression
    - A token type
    - An optional description
    - An optional autocompletion properties
    - An option autoCompletion character (for popup, used as an 'icon')
    - An optional flag to set rule case insensitive (by default=True) or case sensitive
    """

    @staticmethod
    def formatDescription(title=None, description='', example=''):
        """Return a formatted text, ready for tooltip

        Allows use of some 'Markdown' code:
        **XXX** => bold
        *XXX* => italic
        --- => separator
        `` => monospace
        (xx)[yy] => hyperlink <a href='yy'>xx</a>
        """
        def parsedText(text):
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
            text = re.sub(r'`([^`]+)`', r'<span style="font-family:monospace">\1</span>', text)
            text = re.sub(r'\n*---\n*', '<hr>', text)
            text = re.sub(r'\((.+)\)\[(.+)\]', r'<a href="\2">\1</a>', text)
            text = text.replace('\n', '<br>')
            return text

        returned = []

        if isinstance(title, str) and title.strip() != '':
            returned.append(f'<b><!-- title -->{parsedText(title)}<!-- title --></b><hr>')

        if isinstance(description, str) and description.strip() != '':
            returned.append(f'<!-- description -->{parsedText(description)}<!-- description -->')

        if isinstance(example, str) and example.strip() != '':
            returned.append('<hr><i>Example</i><br><br>')
            returned.append(f'<!-- example -->{parsedText(example)}<!-- example -->')

        return ''.join(returned)

    @staticmethod
    def descriptionExtractSection(description, section="title"):
        """Extract section from a TokenizerRule description

        Possible `section` value are:
        - "title"       (default)
        - "description"
        - "example"
        """
        regEx = fr'<!--\s+{section}\s+-->(.*)<!--\s+{section}\s+-->'

        if result := re.search(fr'<!--\s+{section}\s+-->(.*)<!--\s+{section}\s+-->', description):
            return result.groups()[0]
        else:
            return ""

    def __init__(self, type, regex, description=None, autoCompletion=None, autoCompletionChar=None, caseInsensitive=True, ignoreIndent=False, onInitValue=None):
        """Initialise a tokenizer rule

        Given `type` determinate which type of token will be generated by rule
        Given `regex` is a regular expression that will define token
        Given `description` is an optional str, and provide a textual description of token
        Given `autoCompletion` is an optional str / list(str) / tuple / list(tuple), and is provide a list of possible autocompletion value
            When given as an str, consider there's only one possible autocompletion
            When given as a list(str), consider there's multiple possible autocompletion
            When given as a tuple, consider there's only one possible autocompletion; tuple is in form (value, description)
            When given as a list(tuple), consider there's multiple possible autocompletion; tuple is in form (value, description)
        Given `autoCompletionChar` define one character that will be displayed in completer left gutter
        Given `caseInsensitive` allows to define if token is case sensitive or case insensitive (default)
        Given `ignoreIndent` allows to define if token ignore or not indent (default False)
            For example, no INDENT/DEDENT token is produced before a token with `ignoreIndent` set to True
        Given `onInitValue` allows to define a function called when a Token is defined from rule
            Called function will get TokenType and token value and return new value
            Mainly, this can be used to pre-process tokens like:
            - pre-convert a "number" as real number   (ie: value "45.7" <str> will be converted as 45.7 <float>)
        """
        self.__type = None
        self.__regEx = None
        self.__regExSingle = None           # put in cache a QRegularExpression with '^....$' to match single values (improve speed!)
        self.__error = []
        self.__description = description
        self.__autoCompletion = []
        self.__autoCompletionChar = None
        self.__caseInsensitive = caseInsensitive
        self.__ignoreIndent = ignoreIndent

        if callable(onInitValue):
            self.__onInitValue = onInitValue
        else:
            self.__onInitValue = None

        if isinstance(autoCompletionChar, str):
            self.__autoCompletionChar = autoCompletionChar

        self.__setRegEx(regex)
        self.__setType(type)

        if len(self.__error) > 0:
            NL = "\n"
            raise EInvalidValue(f'Token rule is not valid!{NL}{NL.join(self.__error)}')

        if isinstance(autoCompletion, str):
            self.__autoCompletion = [(autoCompletion, autoCompletion, '')]
        elif isinstance(autoCompletion, tuple) and len(autoCompletion) == 2 and isinstance(autoCompletion[0], str) and isinstance(autoCompletion[1], str):
            self.__autoCompletion = [autoCompletion]
        elif isinstance(autoCompletion, list):
            for item in autoCompletion:
                if isinstance(item, str):
                    self.__autoCompletion.append((item, item, ''))
                elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], str):
                    self.__autoCompletion.append(item)

    def __str__(self):
        if self.isValid():
            return f'{self.__type}: {self.__regEx.pattern()}'
        elif self.__regEx is None:
            return f'{self.__type} / None / {self.__error}'
        else:
            return f"{self.__type} / '{self.__regEx.pattern()}' / {self.__error}"

    def __repr__(self):
        if self.__regEx is None:
            return f"<TokenizerRule({self.__type}, None)>"
        return f"<TokenizerRule({self.__type}, '{self.__regEx.pattern()}')>"

    def __setRegEx(self, regEx):
        """Set current regular expression for rule

        Given `regEx` can be:
        - A QRegularExpression
        - A string

        If invalid, doesn't raise error: just define rule as 'in error' with a message
        """
        if isinstance(regEx, str):
            if self.__caseInsensitive:
                regEx = QRegularExpression(regEx, QRegularExpression.CaseInsensitiveOption)
            else:
                regEx = QRegularExpression(regEx)
        elif not isinstance(regEx, QRegularExpression):
            self.__error.append("Given regular expression must be a <str> or <QRegularExpression> type")
            return

        if not regEx.isValid():
            self.__error.append("Given regular expression is not a valid")

        self.__regEx = regEx

        pattern = regEx.pattern()
        if pattern != '' and pattern[0] == '^':
            pattern += '$'
        else:
            pattern = f'^{regEx.pattern()}$'

        if self.__caseInsensitive:
            self.__regExSingle = QRegularExpression(pattern, QRegularExpression.CaseInsensitiveOption)
        else:
            self.__regExSingle = QRegularExpression(pattern)

    def __setType(self, value):
        """Set current type for rule"""
        if isinstance(value, TokenType):
            self.__type = value
        else:
            self.__error.append("Given type must be a valid <TokenType>")

    def regEx(self, single=False):
        """Return regular expression for rule (as QRegularExpression)"""
        if single:
            return self.__regExSingle
        return self.__regEx

    def type(self):
        """Return current type for rule"""
        return self.__type

    def isValid(self):
        """Return True is token rule is valid"""
        return (len(self.__error) == 0 and self.__regEx is not None)

    def errors(self):
        """Return errors list"""
        return self.__error

    def description(self):
        """Return rule description (return str)"""
        return self.__description

    def caseInsensitive(self):
        """Return true if rule is case case insensitive"""
        return self.__caseInsensitive

    def autoCompletion(self):
        """Return rule autoCompletion (return list of tuple(value, description))"""
        return self.__autoCompletion

    def autoCompletionChar(self):
        """Return autoCompletion character"""
        return self.__autoCompletionChar

    def onInitValue(self):
        """Return callable function used for initValue() or None if no function has been defined"""
        return self.__onInitValue

    def initValue(self, value):
        """Process given `value`

        Return processed value from onInitValue() callable
        Or just return value is no callable has been defined
        """
        if self.__onInitValue is None:
            return value
        else:
            return self.__onInitValue(self.__type, value)

    def ignoreIndent(self):
        """Return if token ignore or not indent/dedent"""
        return self.__ignoreIndent

    def matchText(self, matchText, full=False):
        """Return rule as a autoCompletion (return list of tuple (str, str, rule), or empty list if there's no text representation) and
        that match the given `matchText`

        given `matchText` can be a str or a regular expression

        return list of tuple (str, str, rule)
            str: autoCompletion value
            str: description
            rule: current rule
        """
        returned = []
        if isinstance(matchText, str):
            if self.__caseInsensitive:
                matchText = re.compile(re.escape(re.sub(r'\s+', '\x02', matchText)).replace('\x02', r'\s+')+'.*', re.IGNORECASE)
            else:
                matchText = re.compile(re.escape(re.sub(r'\s+', '\x02', matchText)).replace('\x02', r'\s+')+'.*')

        if isinstance(matchText, re.Pattern):
            for item in self.__autoCompletion:
                if result := re.match(r'([^\x01]+)', item[0]):
                    checkMatch = result.groups()[0]
                else:
                    checkMatch = item[0]

                if matchText.match(checkMatch):
                    if full:
                        returned.append((checkMatch, item[0], item[1], self))
                    else:
                        returned.append(checkMatch)

        return returned


class Tokenizer(object):
    """A tokenizer will 'split' a text into tokens, according to given rules


    note: the tokenizer doesn't verify the validity of tokenized text (this is
          made in a second time by a parser)
    """
    ADD_RULE_LAST = 0
    ADD_RULE_TYPE_BEFORE_FIRST = 1
    ADD_RULE_TYPE_AFTER_FIRST = 2
    ADD_RULE_TYPE_BEFORE_LAST = 3
    ADD_RULE_TYPE_AFTER_LAST = 4

    POP_RULE_LAST = 0
    POP_RULE_FIRST = 1
    POP_RULE_ALL = 2

    __TOKEN_INDENT_RULE = TokenizerRule(TokenType.INDENT, '')
    __TOKEN_DEDENT_RULE = TokenizerRule(TokenType.DEDENT, '')
    __TOKEN_WRONGINDENT_RULE = TokenizerRule(TokenType.WRONG_INDENT, '')
    __TOKEN_WRONGDEDENT_RULE = TokenizerRule(TokenType.WRONG_DEDENT, '')

    def __init__(self, rules=None):
        # internal storage for rules (list of TokenizerRule)
        self.__rules = []

        self.__invalidRules = []

        # a global regEx with all rules
        self.__regEx = None

        # a flag to determinate if regular expression&cache need to be updated
        self.__needUpdate = True

        # a cache to store tokenized code
        self.__cache = {}
        self.__cacheOrdered = []

        # when True, for token including spaces, reduce consecutive spaces to 1
        # example: 'set    value'
        #       => 'set value'
        self.__simplifyTokenSpaces = False

        # indent value
        #   When
        #       -1: indent value is defined automatically on first found indent,
        #           and then is used
        #       0:  ignore indent
        #       N:  indent value is defined by given positive number
        self.__indent = 0

        if rules is not None:
            self.setRules(rules)

    def __repr__(self):
        NL = '\n'
        return f"<Tokenizer(Cache={len(self.__cache)}, Rules={len(self.__rules)}{NL}{NL.join([f'{rule}' for rule in self.__rules])}{NL}RegEx={self.regEx()})>"

    def __searchAddIndex(self, mode, type):
        """Search index for given `type` according to defined search `mode`"""
        foundLastPStart = -1
        foundLastPEnd = -1
        reset = True
        for index in range(len(self.__rules)):
            if self.__rules[index].type() == type:
                if reset:
                    if mode == Tokenizer.ADD_RULE_TYPE_BEFORE_FIRST:
                        return index
                    foundLastPStart = index
                    reset = False

                foundLastPEnd = index

            elif foundLastPEnd != -1 and mode == Tokenizer.ADD_RULE_TYPE_AFTER_FIRST:
                return index
            else:
                reset = True

        if mode == Tokenizer.ADD_RULE_TYPE_BEFORE_LAST:
            return foundLastPStart
        elif mode == Tokenizer.ADD_RULE_TYPE_AFTER_LAST:
            return foundLastPEnd

        return len(self.__rules)

    def __searchRemoveIndex(self, mode, type):
        """Search index for given `type` according to defined search `mode`"""
        if mode == Tokenizer.POP_RULE_LAST:
            rng = range(len(self.__rules), -1, -1)
        else:
            rng = range(len(self.__rules))

        for index in rng:
            if self.__rules[index].type() == type:
                return index

        return None

    def __setCache(self, hashValue, tokens=None):
        """Update cache content

        If no tokens is provided, consider to update existing hashValue
        """
        if tokens is True:
            # update cache timestamp
            # ==> assume that hashvalue exists in cache!!
            index = self.__cacheOrdered.index(hashValue)
            self.__cacheOrdered.pop(self.__cacheOrdered.index(hashValue))
            self.__cache[hashValue][0] = time.time()
            self.__cacheOrdered.append(hashValue)
            self.__cache[hashValue][1].resetIndex()
        elif tokens is False:
            # remove from cache
            # ==> assume that hashvalue exists in cache!!
            index = self.__cacheOrdered.index(hashValue)
            self.__cacheOrdered.pop(self.__cacheOrdered.index(hashValue))
            self.__cache.pop(hashValue)
        else:
            # add to cache
            self.__cache[hashValue] = [time.time(), tokens, len(self.__cacheOrdered)]
            self.__cacheOrdered.append(hashValue)
            self.__cache[hashValue][1].resetIndex()

    def indent(self):
        """Return current indent value used to generate INDENT/DEDENT tokens"""
        return self.__indent

    def setIndent(self, value):
        """Set indent value used to generate INDENT/DEDENT tokens"""
        if not isinstance(value, int):
            raise EInvalidType("Given `value` must be <int>")

        if value < 0 and self.__indent != -1:
            self.__indent = -1
            self.__needUpdate = True
        elif self.__indent != value:
            self.__indent = value
            self.__needUpdate = True

    def addRule(self, rules, mode=None):
        """Add tokenizer rule(s)

        Given `rule` must be a <TokenizerRule> or a list of <TokenizerRule>
        """
        if mode is None:
            mode = Tokenizer.ADD_RULE_LAST

        if isinstance(rules, list):
            for rule in rules:
                self.addRule(rule, mode)
        elif isinstance(rules, TokenizerRule):
            if rules.type() is not None:
                if mode == Tokenizer.ADD_RULE_LAST:
                    self.__rules.append(rules)
                else:
                    self.__rules.insert(self.__searchAddIndex(mode, rules.type()), rules)

                self.__needUpdate = True
            else:
                self.__invalidRules.append((rules, "The rule type is set to NONE: the NONE type is reserved"))
        else:
            raise Exception("Given `rule` must be a <TokenizerRule>")

    def removeRule(self, rules, mode=None):
        """Remove tokenizer rule(s)

        Given `rule` must be a <TokenizerRule> or a list of <TokenizerRule>
        """
        if mode is None:
            mode = Tokenizer.POP_RULE_LAST

        if isinstance(rules, list):
            for rule in rules:
                self.removeRule(rule)
        elif isinstance(rules, TokenizerRule):
            if rules.type() is not None:
                if mode == Tokenizer.POP_RULE_ALL:
                    while index := self.__searchRemoveIndex(Tokenizer.POP_RULE_LAST, rules.type()):
                        self.__rules.pop(index)
                elif index := self.__searchRemoveIndex(mode, rules.type()):
                    self.__rules.pop(index)

                self.__needUpdate = True
            else:
                self.__invalidRules.append((rules, "The rule type is set to NONE: the NONE type is reserved"))
        else:
            raise Exception("Given `rule` must be a <TokenizerRule>")

    def rules(self):
        """return list of given (and valid) rules"""
        return self.__rules

    def setRules(self, rules):
        """Define tokenizer rules"""
        if isinstance(rules, list):
            self.__rules = []
            self.__invalidRules = []

            self.addRule(rules)
        else:
            raise Exception("Given `rules` must be a list of <TokenizerRule>")

    def invalidRules(self):
        """Return list of invalid given rules"""
        return self.__invalidRules

    def regEx(self):
        """Return current built regular expression used for lexer"""
        def ruleInsensitive(rule):
            if rule.caseInsensitive():
                return f"(?:(?i){rule.regEx().pattern()})"
            else:
                return rule.regEx().pattern()

        if self.__needUpdate:
            self.clearCache(True)
            self.__needUpdate = False
            self.__regEx = QRegularExpression('|'.join([ruleInsensitive(rule) for rule in self.__rules]), QRegularExpression.MultilineOption)

        return self.__regEx

    def clearCache(self, full=True):
        """Clear cache content

        If `full`, clear everything

        Otherwise clear oldest values
        - At least 5 items are kept in cache
        - At most, 250 items are kept in cache
        """
        if full:
            self.__cache = {}
            self.__cacheOrdered = []
        else:
            currentTime = time.time()
            # keep at least, five items
            for key in self.__cacheOrdered[:-5]:
                if (currentTime - self.__cache[key][0]) > 120:
                    # older than than 2minutes, clear it
                    self.__setCache(key, False)

            if len(self.__cacheOrdered) > 250:
                keys = self.__cacheOrdered[:-250]
                for key in keys:
                    self.__setCache(key, False)

    def simplifyTokenSpaces(self):
        """Return if option 'simplify token spaces' is active or not"""
        return self.__simplifyTokenSpaces

    def setSimplifyTokenSpaces(self, value):
        """Set if option 'simplify token spaces' is active or not"""
        if not isinstance(value, bool):
            raise EInvalidType("Given ` value` must be a <bool>")

        if value != self.__simplifyTokenSpaces:
            self.__simplifyTokenSpaces = value
            self.__needUpdate = True

    def tokenize(self, text):
        """Tokenize given text

        If ` stripSpaces` is True, token spaces are simplified

        Example:
            token 'set   value'
            is returned as 'set value'


        Return a Tokens object
        """
        if not isinstance(text, str):
            raise EInvalidType("Given `text` must be a <str>")

        returned = []

        if self.__needUpdate:
            # rules has been modified, cleanup cache
            self.clearCache(True)

        if text == "" or len(self.__rules) == 0:
            # nothing to process (empty string and/or no rules?)
            return Tokens(text, returned)

        textHash = hashlib.sha1()
        textHash.update(text.encode())
        hashValue = textHash.hexdigest()

        if hashValue in self.__cache:
            # udpate
            self.__setCache(hashValue, True)
            # need to clear unused items in cache
            self.clearCache(False)
            return self.__cache[hashValue][1]

        matchIterator = self.regEx().globalMatch(text)

        Token.resetTokenizer()

        indent = self.__indent
        previousIndent = 0
        previousToken = None
        # iterate all found tokens
        while matchIterator.hasNext():
            match = matchIterator.next()

            for textIndex in range(len(match.capturedTexts())):
                value = match.captured(textIndex)

                position = 0
                for rule in self.__rules:
                    if rule.caseInsensitive():
                        options = QRegularExpression.CaseInsensitiveOption
                    else:
                        options = QRegularExpression.NoPatternOption

                    if rule.regEx(True).match(value).hasMatch():
                        tokenText = match.captured(textIndex)
                        token = Token(tokenText, rule,
                                      match.capturedStart(textIndex),
                                      match.capturedEnd(textIndex),
                                      match.capturedLength(textIndex),
                                      self.__simplifyTokenSpaces)

                        # ---- manage indent/dedent ----
                        if not rule.ignoreIndent() and indent != 0 and (re.search(r'^\s*$', tokenText) is None) and token.column() == 1:
                            # indent value is not zero => means that indent are managed
                            # token is not empty string (only spaces and/or newline)
                            if indent < 0 and token.indent() > 0:
                                # if indent is negative, define indent value with first indented token
                                indent = token.indent()

                            if indent > 0:
                                if previousIndent < token.indent():
                                    # token indent is greater than previous indent value
                                    # need to add INDENT token
                                    nbIndent, nbWrongIndent = divmod(token.indent() - previousIndent, indent)

                                    for numIndent in range(nbIndent):
                                        pStart = token.positionStart() + indent * numIndent
                                        pEnd = token.positionStart() + indent * (numIndent + 1)
                                        length = pEnd-pStart

                                        tokenIndent = Token(' ' * indent, Tokenizer.__TOKEN_INDENT_RULE, pStart, pEnd, length)
                                        tokenIndent.setPrevious(previousToken)
                                        returned.append(tokenIndent)
                                        previousToken = tokenIndent

                                    if nbWrongIndent > 0:
                                        pStart = token.positionStart() + indent * (numIndent + 1)
                                        pEnd = pStart+nbWrongIndent

                                        tokenIndent = Token(' ' * nbWrongIndent, Tokenizer.__TOKEN_WRONGINDENT_RULE, pStart, pEnd, nbWrongIndent)
                                        tokenIndent.setPrevious(previousToken)
                                        returned.append(tokenIndent)
                                        previousToken = tokenIndent

                                elif previousIndent > token.indent():
                                    # token indent is lower than previous indent value
                                    # need to add DEDENT token
                                    nbIndent, nbWrongIndent = divmod(previousIndent - token.indent(), indent)

                                    for numIndent in range(nbIndent):
                                        pStart = token.positionStart() + indent * numIndent
                                        pEnd = token.positionStart() + indent * (numIndent + 1)
                                        length = pEnd-pStart

                                        tokenIndent = Token(' ' * indent, Tokenizer.__TOKEN_DEDENT_RULE, pStart, pEnd, length)
                                        tokenIndent.setPrevious(previousToken)
                                        returned.append(tokenIndent)
                                        previousToken = tokenIndent

                                    if nbWrongIndent > 0:
                                        pStart = token.positionStart() + indent * (numIndent + 1)
                                        pEnd = pStart+nbWrongIndent

                                        tokenIndent = Token(' ' * nbWrongIndent, Tokenizer.__TOKEN_WRONGDEDENT_RULE, pStart, pEnd, nbWrongIndent)
                                        tokenIndent.setPrevious(previousToken)
                                        returned.append(tokenIndent)
                                        previousToken = tokenIndent

                                previousIndent = token.indent()

                        token.setPrevious(previousToken)
                        if previousToken is not None:
                            previousToken.setNext(token)
                        returned.append(token)
                        previousToken = token

                        # do not need to continue to check for another token type
                        break

        # add
        self.__setCache(hashValue, Tokens(text, returned))

        # need to clear unused items in cache
        self.clearCache(False)

        return self.__cache[hashValue][1]
