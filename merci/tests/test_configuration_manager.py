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
Unit tests for configuration manager.
"""
import unittest

from merci.managers import ConfigurationManager, FeatureFlagManager
from merci.structure import Context, Modifiers, Configuration


class TestConfigurationManager(unittest.TestCase):
    """ Unit tests for configuration manager. """

    joe_in_qa = {"environment": "qa", "user": "joe"}
    joe_in_prod = {"environment": "prod", "user": "joe"}

    def test_set_contexts(self):
        configuration = Configuration(
            "enable-welcome", Context(False,
                                      Modifiers(
                                          'environment', {
                                              'qa': Context(False,
                                                            Modifiers(
                                                                'user', {
                                                                    'joe': Context(True, None)
                                                                })),
                                              'prod': Context(False, None)
                                          })))

        configuration_manager = ConfigurationManager()

        configuration_store = {"enable-welcome": configuration}
        configuration_manager.set_configuration_store(configuration_store)

        is_welcome_enabled = configuration_manager.get_object("enable-welcome", self.joe_in_qa, False)

        self.assertTrue(is_welcome_enabled)

        configuration_manager = ConfigurationManager()
        feature_flag_manager = FeatureFlagManager(configuration_manager)

        configuration_manager.set_configuration_store(configuration_store)

        is_welcome_enabled = feature_flag_manager.is_active("enable-welcome", self.joe_in_qa, False)

        self.assertTrue(is_welcome_enabled)

        is_welcome_enabled = feature_flag_manager.is_active("enable-welcome", self.joe_in_prod, False)

        self.assertFalse(is_welcome_enabled)
