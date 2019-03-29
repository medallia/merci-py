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
Unit tests for structure classes, like Context, Modifiers and Configuration.
"""
from unittest import TestCase

from merci.structure import Context, Modifiers, Configuration
from merci.tests.configs import MessageConfig


class TestConfiguration(TestCase):
    """ Unit tests for Merci structure classes. """

    empty = {}
    qa = {"environment": "qa"}
    prod = {"environment": "prod"}
    cem341 = {"environment": "qa", "cluster": "cem341"}
    cem1001 = {"environment": "prod", "cluster": "cem1001"}
    joe_on_cem341_in_qa = {"environment": "qa", "cluster": "cem341", "user": "joe"}
    joe_on_cem1001_in_prod = {"environment": "prod", "cluster": "cem1001", "user": "joe"}
    jack_on_cem341_in_qa = {"environment": "qa", "cluster": "cem341", "user": "jack"}

    # Value of feature flag (Boolean) context is only true for user "joe" in environment "qa".
    only_true_for_joe_in_qa_feature_flags = '{ "feature-flags": { "enable-none": { "value": false } } }'
    only_true_for_joe_in_qa = Context(False, Modifiers("environment",
                                                       {"qa": Context(False, Modifiers("user", {"joe": Context(True)})),
                                                        "prod": Context(False)}))

    config_context = Context(MessageConfig("I just started."),
                             Modifiers("environment",
                                       {"qa": Context(MessageConfig("I am almost there."),
                                                      Modifiers("cluster",
                                                                {"cem341": Context(MessageConfig("Someone is testing in cem341."),
                                                                                   Modifiers("user",
                                                                                             {"joe": Context(MessageConfig("I am testing in cem341, Joe."))}))})),
                                        "prod": Context(MessageConfig("Yeah. I made it."))}))

    def test_context_for_enable_feature_all(self):
        true_for_all = Context(True)
        self.assertTrue(true_for_all.get_value(self.empty))
        self.assertTrue(true_for_all.get_value(self.qa))
        self.assertTrue(true_for_all.get_value(self.prod))
        self.assertTrue(true_for_all.get_value(self.cem341))
        self.assertTrue(true_for_all.get_value(self.cem1001))
        self.assertTrue(true_for_all.get_value(self.joe_on_cem341_in_qa))
        self.assertTrue(true_for_all.get_value(self.joe_on_cem1001_in_prod))
        self.assertTrue(true_for_all.get_value(self.jack_on_cem341_in_qa))

    def test_context_for_enable_feature_none(self):
        false_for_all = Context(False)
        self.assertFalse(false_for_all.get_value(self.empty))
        self.assertFalse(false_for_all.get_value(self.qa))
        self.assertFalse(false_for_all.get_value(self.prod))
        self.assertFalse(false_for_all.get_value(self.cem341))
        self.assertFalse(false_for_all.get_value(self.cem1001))
        self.assertFalse(false_for_all.get_value(self.joe_on_cem341_in_qa))
        self.assertFalse(false_for_all.get_value(self.joe_on_cem1001_in_prod))
        self.assertFalse(false_for_all.get_value(self.jack_on_cem341_in_qa))

    def test_context_for_enable_feature_one(self):
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.empty))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.qa))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.prod))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.cem341))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.cem1001))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.joe_on_cem1001_in_prod))
        self.assertFalse(self.only_true_for_joe_in_qa.get_value(self.jack_on_cem341_in_qa))
        self.assertTrue(self.only_true_for_joe_in_qa.get_value(self.joe_on_cem341_in_qa))

    def test_context_for_enable_config_one(self):
        message_config = self.config_context.get_value(self.empty)
        self.assertEqual("I just started.", message_config.message)
        message_config = self.config_context.get_value(self.qa)
        self.assertEqual("I am almost there.", message_config.message)
        message_config = self.config_context.get_value(self.prod)
        self.assertEqual("Yeah. I made it.", message_config.message)
        message_config = self.config_context.get_value(self.cem341)
        self.assertEqual("Someone is testing in cem341.", message_config.message)
        message_config = self.config_context.get_value(self.cem1001)
        self.assertEqual("Yeah. I made it.", message_config.message)
        message_config = self.config_context.get_value(self.joe_on_cem1001_in_prod)
        self.assertEqual("Yeah. I made it.", message_config.message)
        message_config = self.config_context.get_value(self.jack_on_cem341_in_qa)
        self.assertEqual("Someone is testing in cem341.", message_config.message)
        message_config = self.config_context.get_value(self.joe_on_cem341_in_qa)
        self.assertEqual("I am testing in cem341, Joe.", message_config.message)

    def test_configuration(self):
        enable_joe_configuration = Configuration("enable-joe", self.only_true_for_joe_in_qa)
        self.assertTrue(enable_joe_configuration.get_value(self.joe_on_cem341_in_qa))
        self.assertFalse(enable_joe_configuration.get_value(self.joe_on_cem1001_in_prod))
