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
# The setings module provides a generic class to use to manage configuration
# settings files (json format)
#
# Main class from this module
#
# - Settings:
#       Main class to extend to manage settings
#       Provide init/read/write static methods
#       Let define the default settings:
#       - configuration names
#       - default values
#       - perimeter/validity rules
#
# - SettingsRule
#       Manage validation rule for a setting configuration variable
#
# -----------------------------------------------------------------------------

from enum import Enum


from PyQt5.Qt import *
from PyQt5.QtCore import (
        pyqtSignal as Signal
    )

from os.path import (join, getsize)
import json
import os
import re
import sys
import shutil


from .utils import Debug

from ..pktk import *


class SettingsFmt(object):
    """Allows to define allowed format for a setting"""

    def __init__(self, settingType, values=None):
        if not isinstance(settingType, type):
            raise EInvalidType('Given `settingType` must be a type')

        self.__type = settingType
        self.__values = values

    def check(self, value, checkType=None):
        """Check if given value match setting format"""
        if checkType is None:
            checkType = self.__type

        if not isinstance(value, checkType):
            raise EInvalidType(f'Given `value` ({value}) is not from expected type ({checkType})')

        if self.__values is not None:
            if isinstance(value, (list, tuple)):
                # value is a list, need to check all items in the list
                if isinstance(self.__values, (list, tuple)):
                    # possible values provided as a list
                    # check if all items are of given type
                    for item in value:
                        if item not in self.__values:
                            raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter ({1})'.format(item, self.__values))
                else:
                    # check items values
                    for item in value:
                        self.check(item, self.__values)
            elif isinstance(self.__values, list):
                # check if given value is in list of defined values
                if value not in self.__values:
                    raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter ({1})'.format(value, self.__values))
            elif isinstance(self.__values, tuple):
                # check if given value is in range defined by tuple
                if self.__values[0] is None and self.__values[1] is None:
                    # stupid case but need to ensure taht both values are not None
                    return
                elif self.__values[0] is None:
                    # no minimum value, just check maximum
                    if value > self.__values[1]:
                        raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter [{0}<={1}])'.format(value, self.__values[1]))
                elif self.__values[1] is None:
                    # no maximum value, just check minimum
                    if value < self.__values[0]:
                        raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter [{1}<={0}])'.format(value, self.__values[1]))
                elif value < self.__values[0] or value > self.__values[1]:
                    raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter [{1}<={0}<={2}])'.format(value, self.__values[0], self.__values[1]))
            elif isinstance(self.__values, re.Pattern):
                # check if value match regular expression
                if self.__values.match(value) is None:
                    raise EInvalidValue('Given `value` ({0}) is not in authorized perimeter'.format(value))


class SettingsKey(Enum):
    """Settings key have to be defined as a derived class of SettingsKey"""
    def id(self, **param):
        if isinstance(param, dict):
            return self.value.format(**param)
        else:
            return self.value


class SettingsRule(object):
    """A rule"""

    def __init__(self, id, defaultValue, *settingsFmt):
        """Build a rule

        Given `id` is a <str> or a <SettingsKey> type
        Given `defaultValue` is default value that should be applied for id when initialising settings; it should match provided `settingsFmt` type(s)
        Given `settingsFmt` define zero to N valid format for id

        Example:
            rule('my.configuration.key1', 0,            SettingsFmt(int))                       # accept any integer value
            rule('my.configuration.key2', 0,            SettingsFmt(int, [0,1,2,3]))            # accept integer value 0, 1, 2, 3
            rule('my.configuration.key2', [100,100],    SettingsFmt(int), SettingsFmt(int))     # value must be a list of 2 items, each value in list must be integer
        """
        if isinstance(id, SettingsKey):
            id = id.id()

        if not isinstance(id, str):
            raise EInvalidType('Given `id` for SettingsRule must be a <str> or a <SettingsKey> type')

        self.__id = id
        self.__defaultValue = defaultValue
        self.__settingsFmt = []

        for settingFmt in settingsFmt:
            if not isinstance(settingFmt, SettingsFmt):
                raise EInvalidType('Given `settingsFmt` must be a <SettingsFmt> type')
            self.__settingsFmt.append(settingFmt)

    def id(self):
        """Return rule Id"""
        return self.__id

    def defaultValue(self):
        """Return default value"""
        return self.__defaultValue

    def checkValue(self, value):
        """Check if given value is valid (according to current rule) otherwise raise an exception"""
        if len(self.__settingsFmt) == 0:
            # in this case, we don't care about value
            return
        elif len(self.__settingsFmt) == 1:
            self.__settingsFmt[0].check(value)
        else:
            # In this case value must be a list
            # and we need to check each item in list
            if not isinstance(value, list):
                raise EInvalidType('Given `value` must be a list')

            if not isinstance(value, list):
                raise EInvalidType(f'Given value for id `{self.__id}` must be a list: {value}')

            # number of item must match number of rules
            if len(self.__settingsFmt) != len(value):
                raise EInvalidType(f'Given value for id `{self.__id}` is not a valid list: {value}')

            # check if each item match corresponding rule
            for index in range(len(value)):
                self.__settingsFmt[index].check(value[index])


class Settings(QObject):
    """Manage all settings with open&save options

    Configuration is saved as JSON file
    """
    _settingsSaved = Signal()          # settings has been saved
    _settingsLoaded = Signal()         # settings has been loaded

    @classmethod
    def __init(cls):
        """Internal function to initialise class"""
        try:
            if cls.__name != cls.__name__:
                cls.__settings = cls()
                cls.__name = cls.__name__
        except Exception as e:
            cls.__settings = cls()
            cls.__name = cls.__name__

    @classmethod
    def load(cls):
        """load configuration"""
        cls.__init()
        return cls.__settings.loadConfig()

    @classmethod
    def save(cls):
        """save configuration"""
        cls.__init()
        return cls.__settings.saveConfig()

    @classmethod
    def fileName(cls):
        """return file name"""
        cls.__init()
        return cls.__settings.configurationFileName()

    @classmethod
    def instance(cls):
        """Return current instance of class"""
        cls.__init()
        return cls.__settings

    @classmethod
    def set(cls, id, value):
        """Set option value"""
        cls.__init()
        return cls.__settings.setOption(id, value)

    @classmethod
    def get(cls, id):
        """Get option value"""
        cls.__init()
        return cls.__settings.option(id)

    @classmethod
    def modified(cls):
        """Get option value"""
        cls.__init()
        return cls.__settings.isModified()

    @classmethod
    def settingsSaved(cls):
        """Get option value"""
        cls.__init()
        return cls.__settings._settingsSaved

    @classmethod
    def settingsLoaded(cls):
        """Get option value"""
        cls.__init()
        return cls.__settings._settingsLoaded

    # --------------------------------------------------------------------------
    def __init__(self, pluginId, rules=None):
        """Initialise settings"""
        super(Settings, self).__init__(None)
        if pluginId is None or pluginId == '':
            pluginId = ''

        # define automatically json filename from given plugin id
        self.__pluginCfgFile = os.path.join(QStandardPaths.writableLocation(QStandardPaths.GenericConfigLocation), f'krita-plugin-{pluginId}rc.json')
        self.__config = {}

        # define current rules for options
        self.__rules = {}

        # configuration has been modified and need to be saved?
        self.__modified = False

        if rules is not None:
            self.setRules(rules)
        self.setDefaultConfig()
        self.loadConfig()

    def __setValue(self, target, id, value):
        """From an id like 'a.b.c', set value in target dictionary"""
        keys = id.split('.', 1)

        if len(keys) == 1:
            if not self.__modified and (keys[0] not in target or target[keys[0]] != value):
                # value is created and/or modified
                self.__modified = True

            target[keys[0]] = value
        else:
            if keys[0] not in target:
                target[keys[0]] = {}

            self.__setValue(target[keys[0]], keys[1], value)

    def __getValue(self, target, id):
        """From an id like 'a.b.c', get value in target dictionary"""
        keys = id.split('.', 1)

        if len(keys) == 1:
            return target[keys[0]]
        else:
            return self.__getValue(target[keys[0]], keys[1])

    def configurationFileName(self):
        """Return the configuration file name"""
        return self.__pluginCfgFile

    def rules(self):
        """Return rules"""
        return self.__rules

    def setRules(self, rules):
        """Define new rules

        Note: current configuration will be initialised from default and reloaded
              if configuration file exists
        """
        # check if provided rule are valid
        if not isinstance(rules, list):
            raise EInvalidType('Given `rules` must be provided as a <list(<SettingsRule>)>')

        for rule in rules:
            if not isinstance(rule, SettingsRule):
                raise EInvalidType('Given rules keys must be provided as a <SettingsRule>')

            self.__rules[rule.id()] = rule

        self.__config = {}
        self.setDefaultConfig()
        self.loadConfig()

    def setDefaultConfig(self):
        """Reset default configuration"""
        self.__config = {}

        for ruleId in self.__rules:
            self.__setValue(self.__config, ruleId, self.__rules[ruleId].defaultValue())

        # just initialised with default values, consider that it's not modified
        self.__modified = False

    def loadConfig(self):
        """Load configuration from file

        If file doesn't exist return False
        Otherwise True
        """
        def setKeyValue(sourceKey, value):
            if isinstance(value, dict):
                for key in value:
                    setKeyValue(f'{sourceKey}.{key}', value[key])
            else:
                self.setOption(sourceKey, value)

        jsonAsDict = None

        if os.path.isfile(self.__pluginCfgFile):
            with open(self.__pluginCfgFile, 'r') as file:
                try:
                    jsonAsStr = file.read()
                except Exception as e:
                    Debug.print('[Settings.loadConfig] Unable to load file {0}: {1}', self.__pluginCfgFile, f"{e}")
                    self.configurationLoadedEvent(False)
                    return False

                try:
                    jsonAsDict = json.loads(jsonAsStr)
                except Exception as e:
                    Debug.print('[Settings.loadConfig] Unable to parse file {0}: {1}', self.__pluginCfgFile, f"{e}")
                    self.configurationLoadedEvent(False)
                    return False
        else:
            self.configurationLoadedEvent(False)
            return False

        # parse all items, and set current config
        for key in jsonAsDict:
            setKeyValue(key, jsonAsDict[key])

        self.configurationLoadedEvent(True)

        # just loaded, consider that it's not modified
        self.__modified = False
        self._settingsLoaded.emit()
        return True

    def saveConfig(self):
        """Save configuration to file

        If file can't be saved, return False
        Otherwise True
        """
        with open(self.__pluginCfgFile, 'w') as file:
            try:
                file.write(json.dumps(self.__config, indent=4, sort_keys=True))
            except Exception as e:
                Debug.print('[Settings.saveConfig] Unable to save file {0}: {1}', self.__pluginCfgFile, f"{e}")
                self.configurationSavedEvent(False)
                return False

        self.configurationSavedEvent(True)

        # just saved, consider that it's not modified
        self.__modified = False
        self._settingsSaved.emit()
        return True

    def configurationLoadedEvent(self, fileLoaded):
        """Called after configuration is loaded and before signal is emitted

        If file has not been loaded (doesn't exit, can't be read, ...), the
        given `fileLoaded` parameter will be False, otherwise True

        """
        # can overrided by classes
        pass

    def configurationSavedEvent(self, fileSaved):
        """Called after configuration is loaded and before signal is emitted

        If file has not been saved (can't be write, ...), the
        given `fileSaved` parameter will be False, otherwise True
        """
        # can overrided by classes
        pass

    def setOption(self, id, value):
        """Set value for given option

        Given `id` must be valid (a SettingsKey)
        Given `value` format must be valid (accordiing to id, a control is made)
        """
        # check if id is valid
        if isinstance(id, SettingsKey):
            id = id.id()

        if not isinstance(id, str) or id not in self.__rules:
            # raise EInvalidValue(f'Given `id` is not valid: {id}')
            Debug.print('[Settings.setOption] Given id `{0}` is not valid', id)
            return False

        # check if value is valid
        try:
            self.__rules[id].checkValue(value)
            # value is valid, set it
            self.__setValue(self.__config, id, value)
        except Exception as e:
            Debug.print('[Settings.setOption] Given value is not valid: {0}', f"{e}")
            return False

    def option(self, id):
        """Return value for option"""
        # check if id is valid
        if isinstance(id, SettingsKey):
            id = id.id()

        if not isinstance(id, str) or id not in self.__rules:
            raise EInvalidValue(f'Given `id` is not valid: {id}')

        return self.__getValue(self.__config, id)

    def options(self):
        return self.__config

    def isModified(self):
        """Return True if configuration has been modified"""
        return self.__modified
