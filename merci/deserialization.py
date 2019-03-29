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
Classes for de-serializing feature flag and runtime config JSON to Merci evaluation hierarchies.
"""
from abc import abstractmethod, ABC
import json
from json import JSONDecoder
from typing import Dict

from merci.metrics import ConfigurationMapperMetrics
from merci.structure import Modifiers, Context


class InstantiationException(Exception):
    """ Instantiation error. """


class ValueDecoderFactory(ABC):
    """ Factory of value decoders. """
    @abstractmethod
    def create_value_decoder(self, class_name: str) -> object:
        """
        Return new value decoder.
        :param class_name: name of class to be instantiated for configuration value objects
        :return: new value decoder instance
        """


class ObjectValueDecoder:
    """ Value decoder that de-serializes JSON to new config objects of a class with the provided name. """
    def __init__(self, class_name: str):
        """
        Initializes value decoder with provided class name.
        :param class_name: name of class to be used for de-serializing JSON to objects
        """
        self.class_name = class_name

    def decode_value(self, value_dict: Dict) -> object:
        """ Decodes dictionary of values to objects with values for fields. """
        return self.create_instance(value_dict)

    def create_instance(self, value_dict: Dict) -> object:
        """
        Creates instance of type class_name with values from provided dictionary.
        :param value_dict: values to be used for fields of new object
        :return: new object of type class_name with provided values
        """
        clazz = self.find_class()
        instance = getattr(clazz, '__new__')(clazz)
        initializer = getattr(clazz, '__init__')
        initializer(instance, **value_dict)
        return instance

    def find_class(self) -> type:
        """
        :return: type (class) from class_name.
        """
        try:
            class_name_parts = self.class_name.split('.')
            module_name = ".".join(class_name_parts[:-1])
            attribute = __import__(module_name)
            for components in class_name_parts[1:]:
                attribute = getattr(attribute, components)
            return attribute
        except (AttributeError, ModuleNotFoundError, ValueError) as exception:
            raise InstantiationException(
                'Could not instantiate class with name ' + self.class_name + '.') from exception


class ObjectValueDecoderFactory(ValueDecoderFactory):
    """ Factory of object value decoders. """
    def create_value_decoder(self, class_name: str) -> object:
        """
        Return new object value decoder.
        :param class_name: name of config class to be instantiated
        :return: new object value decoder instance
        """
        return ObjectValueDecoder(class_name)


class SingleValueDecoder:
    """ Value decoder that de-serializes JSON to single value objects based on the type of the value. """
    # noinspection PyMethodMayBeStatic
    def decode_value(self, value: object) -> object:
        """
        :return: value (object) as-is
        """
        return value


class SingleValueDecoderFactory(ValueDecoderFactory):
    """ Factory of single value decoders. """
    def create_value_decoder(self, class_name: str) -> object:
        """
        Return new single value decoder.
        :param class_name: ignored
        :return: new single value decoder
        """
        return SingleValueDecoder()


class ContextDecoder(JSONDecoder):
    """ JSON decoder for de-serializing JSON to feature flag and runtime config contexts. """
    def __init__(self, *args, **kwargs):
        self.value_decoder: type = kwargs.pop('value_decoder', dict)
        JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct: dict) -> object:
        if 'contexts' in dct:
            type_name = dct['type']
            contexts = dct['contexts']
            return Modifiers(type_name, contexts)
        elif 'modifiers' in dct:
            modifiers = dct['modifiers']
            value_object = self.value_decoder.decode_value(dct['value'])
            return Context(value_object, modifiers)
        elif 'value' in dct:
            value_object = self.value_decoder.decode_value(dct['value'])
            return Context(value_object, None)
        return dct


class ConfigurationMapper:
    """ De-serializes JSON to a dictionary of feature flag or runtime config contexts. """
    def __init__(self, root: str, value_decoder_factory: ValueDecoderFactory,
                 skip_non_instantiable: bool,
                 metrics: ConfigurationMapperMetrics):
        self.root = root
        self.value_decoder_factory = value_decoder_factory
        self.skip_non_instantiable = skip_non_instantiable
        self.metrics = metrics

    def read_value(self, json_content: str) -> Dict:
        """
        Parse JSON content to dictionary of feature flag or runtime config contexts
        :param json_content: JSON to be de-serialized
        :return: dictionary of feature flag or runtime config contexts
        """
        configurations: Dict[str, Context] = {}
        json_tree: Dict[str, Dict] = json.loads(json_content, encoding="utf-8")
        configuration_dict: Dict[str, object] = json_tree[self.root]
        for configuration_name, configuration in configuration_dict.items():  # i.e. "configs.XJConfig"
            try:
                configuration_json: str = json.dumps(configuration)
                value_decoder = self.value_decoder_factory.create_value_decoder(configuration_name)
                configuration_context: Context = json.loads(configuration_json, encoding="utf-8", cls=ContextDecoder, value_decoder=value_decoder)
                configurations[configuration_name] = configuration_context
            except Exception as exception:
                if self.skip_non_instantiable:
                    self.metrics.increment_non_instantiable_skips()
                else:
                    raise exception
        return configurations
