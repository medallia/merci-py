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
Core classes for feature flag and config evaluation.
"""
from abc import abstractmethod, ABC
from typing import Dict, Optional


class RuntimeEvaluator(ABC):
    """ Evaluates feature flags and configs at runtime based on a provided runtime context. """
    @abstractmethod
    def get_value(self, runtime_context: Dict[str, str]) -> object:
        """
        Evaluate hierarchy of configuration objects and return resulting Python object.
        :param runtime_context:  dictionary with context values
        :return: config value object
        """


class Context(RuntimeEvaluator):
    """
    A configuration context is a sub-tree in the definition of a configuration, that defines a (default) value object
    of type T at the current level, and an optional override hierarchy, called modifiers.

    I.e., in the following JSON representation of a feature flag configuration, the top default value (object)
    of type Boolean is 'false' and the modifiers hierarchy is defined to override the default value depending
    on each environment (context value).

    "enable-feature-one": {
        "value": false,
        "modifiers": {
            "type": "environment",
            "contexts": {
                "qa": {
                    "value": true
                },
                "prod": {
                    "value": false
                }
            }
        }
    }
    """
    def __init__(self, value, modifiers: Optional[RuntimeEvaluator] = None):
        # value is an object, i.e. a boolean value True or False
        self.value: object = value
        # reference to Modifiers object
        self.modifiers = modifiers

    def get_value(self, runtime_context: Dict[str, str]) -> object:
        if self.modifiers is not None:
            modifiers_value = self.modifiers.get_value(runtime_context)
            if modifiers_value is not None:
                return modifiers_value
        return self.value


class Modifiers(RuntimeEvaluator):
    """
    A configuration modifiers is an override hierarchy in the definition of a configuration.

    I.e., in the following JSON representation of a feature flag configuration, the modifiers hierarchy
    is defined to override the default value (object) 'false' with 'true' for (runtime) context values
    'qa' and 'prod' of type 'environment'.

    "enable-feature-one": {
        "value": false,
        "modifiers": {
            "type": "environment",
            "contexts": {
                "qa": {
                    "value": true
                },
                "prod": {
                    "value": false
                }
            }
        }
    }
    """
    def __init__(self, context_type, contexts: Dict[str, RuntimeEvaluator]):
        self.context_type: str = context_type  # i.e. 'environment'
        self.contexts: Dict[str, RuntimeEvaluator] = contexts

    def get_value(self, runtime_context: Dict[str, str]) -> object:
        runtime_context_value = runtime_context.get(self.context_type)
        if runtime_context_value is None:
            return None
        context = self.contexts.get(runtime_context_value, None)
        if context is None:
            return None
        return context.get_value(runtime_context)


class Configuration(RuntimeEvaluator):
    """
    A configuration is defined by a unique name and a context definition.

    I.e., in the following JSON representation of a (runtime) config, the context of the config
    with the unique name 'configs.XJConfig' is the dictionary defined by the curly braces.

    "configs.XJConfig": {
        "value": {
            "hosts": ["xj2001"],
            "port": 4554,
            "timeout_seconds": 30
        }
    }
    """
    def __init__(self, name: str, context: Context):
        self.name = name
        self.context = context

    def get_value(self, runtime_context: Dict[str, str]) -> object:
        return self.context.get_value(runtime_context)
