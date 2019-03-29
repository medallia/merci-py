#
# Copyright 2019 Medallia, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
In-memory stores for feature flags and configs.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

from merci.structure import Configuration


class ConfigurationStoreUpdater(ABC):
    """ Base class for updating a configuration store. """
    def set_configuration_store(self,
                                configuration_store: Dict[str, Configuration]):
        """
        Update (set) entire configuration store with new dictionary of configurations
        :param configuration_store:  dictionary with new configurations
        :return:
        """


class ConfigurationStoreReader(ABC):
    """ Base class for reading from configuration store. """
    @abstractmethod
    def get_object(self, configuration_name: str,
                   runtime_context: Dict[str, str],
                   default_value: object) -> Optional:
        """
        Return evaluated value object for provided configuration name from store.
        :param configuration_name: name of configuration to look up
        :param runtime_context: runtime context value to be used for evaluation
        :param default_value: default value object if configuration could not be found
        :return: evaluated value object
        """


class ConfigurationManager(ConfigurationStoreUpdater,
                           ConfigurationStoreReader):
    """ Configuration manager used by feature flag and config manager. """
    def __init__(self):
        self._configuration_store: Dict[str, Configuration] = {}

    def set_configuration_store(self,
                                configuration_store: Dict[str, Configuration]):
        self._configuration_store = configuration_store

    def get_object(self, configuration_name: str,
                   runtime_context: Dict[str, str],
                   default_value: object) -> Optional:
        configuration: Configuration = self._configuration_store.get(
            configuration_name, None)
        if configuration is None:
            return default_value
        return configuration.get_value(runtime_context)


class FeatureFlagManager:
    """ Manager for feature flags. """
    def __init__(self, configuration_store: ConfigurationStoreReader):
        self._configuration_store: ConfigurationStoreReader = configuration_store

    def is_active(self, feature_flag_name: str,
                  runtime_context: Dict[str, str],
                  default_value: bool) -> bool:
        """
        Return True if feature flag is active for provided runtime context.
        :param feature_flag_name: name of feature flag to evaluate
        :param runtime_context: runtime context values
        :param default_value: default boolean value if feature flag could not be found
        :return:
        """
        return self._configuration_store.get_object(
            feature_flag_name, runtime_context, default_value)


class ConfigManager:
    """ Manager for runtime configs. """
    def __init__(self, configuration_store: ConfigurationStoreReader):
        self._configuration_store: ConfigurationStoreReader = configuration_store

    def get_config(self, config_class: type,
                   runtime_context: Dict[str, str]) -> object:
        """
        Return evaluated config value object for provided configuration name from store.
        :param config_class:
        :param runtime_context:
        :return:
        """
        config_class_name: str = _ClassUtil.full_class_name(config_class)
        config: Configuration = self._configuration_store.get_object(
            config_class_name, runtime_context, None)
        if config is None:
            return _ClassUtil.instantiate_with_defaults(config_class)
        return config


class _ClassUtil:
    """ Utility class for instantiating objects by class name. """
    @staticmethod
    def instantiate_with_defaults(clazz: type) -> object:
        """
        Return new object of provided class, initialized with default values
        :param clazz: class to use for instantiation
        :return: new object with default values
        """
        instance = getattr(clazz, '__new__')(clazz)
        initializer = getattr(clazz, '__init__')
        initializer(instance)
        return instance

    @staticmethod
    def full_class_name(clazz: type) -> str:
        """
        Return full class name of provided class.
        :param clazz: class to get full name for
        :return: full class name
        """
        module = clazz.__module__
        if module is None or module == 'builtins':
            return clazz.__qualname__
        return module + '.' + clazz.__qualname__
