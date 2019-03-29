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
Integration tests for configuration reader.
"""
import os
from unittest import TestCase

from configs import XJConfig
from merci.deserialization import ConfigurationMapper, SingleValueDecoderFactory, ObjectValueDecoderFactory, InstantiationException
from merci.managers import ConfigurationManager
from merci.metrics import ConfigurationManagerMetrics, ConfigurationFetcherMetrics
from merci.readers import ConfigurationReader
from merci.fetchers import FilesystemConfigurationFetcher


class TestConfigurationReader(TestCase):
    """ Unit tests for configuration reader. """

    empty_context = {}
    qa_context = {"environment": "qa"}

    resource_dir = os.path.dirname(
        os.path.realpath('__file__')) + "/resources"

    def test_execute(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", False, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/featureflags.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()

        self.assertEqual(True, manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(False,manager.get_object("enable-feature-none", self.empty_context, True))
        self.assertEqual(0, manager_metrics.same_content_skips)
        self.assertEqual(1, fetcher_metrics.requests)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_twice(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", False, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/featureflags.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()
        reader.execute()

        self.assertEqual(True, manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(False, manager.get_object("enable-feature-none", self.empty_context, True))
        self.assertEqual(1, manager_metrics.same_content_skips)
        self.assertEqual(2, fetcher_metrics.requests)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_four_times(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", False, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/featureflags.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()
        reader.execute()
        reader.execute()
        reader.execute()

        self.assertEqual(True, manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(False, manager.get_object("enable-feature-none", self.empty_context, True))
        self.assertEqual(2, manager_metrics.same_content_skips)
        self.assertEqual(4, fetcher_metrics.requests)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_for_missing_file(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", False, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/featureflags.json", "/unknown-featureflags-file.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        try:
            reader.execute()
        except FileNotFoundError:
            self.assertEqual(1, fetcher_metrics.missing_files)
            self.assertEqual(1, fetcher_metrics.failures)
        else:
            self.fail('Expected FileNotFoundError did not get thrown.')

        self.assertEqual(False, manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(True, manager.get_object("enable-feature-none", self.empty_context, True))

    def test_execute_for_skipping_missing_file(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", True, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/unknown-featureflags-file.json", "/featureflags.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()

        self.assertEqual(True, manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(False, manager.get_object("enable-feature-none", self.empty_context,  True))
        self.assertEqual(1, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_for_file_with_bad_json(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", True, fetcher_metrics)

        mapper = ConfigurationMapper("feature-flags", SingleValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/featureflags-bad-json.json", "/featureflags.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        try:
            reader.execute()
        except IOError:
            self.assertEqual(1, manager_metrics.content_failures)

        else:
            self.fail('Expected FileNotFoundError did not get thrown.')

        self.assertEqual(False,manager.get_object("enable-feature-all", self.empty_context, False))
        self.assertEqual(True, manager.get_object("enable-feature-none", self.empty_context, True))
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_for_instantiable_config(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", True, fetcher_metrics)

        mapper = ConfigurationMapper("configs", ObjectValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/configs.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()

        xj_config: XJConfig = manager.get_object("configs.XJConfig", self.qa_context, None)

        self.assertEqual(["xj2001"], xj_config.hosts)
        self.assertEqual(1, manager_metrics.updates)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_for_file_with_non_instantiable_config(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", True, fetcher_metrics)

        mapper = ConfigurationMapper("configs", ObjectValueDecoderFactory(), False, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/configs-non-instantiable.json", "/configs.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        try:
            reader.execute()
        except InstantiationException:
            self.assertEqual(0, manager_metrics.non_instantiable_skips)

        else:
            self.fail('Expected InstantiationException did not get thrown.')

        xj_config: XJConfig = manager.get_object("configs.XJConfig", self.qa_context, None)

        self.assertEqual(None, xj_config)
        self.assertEqual(0, manager_metrics.updates)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

    def test_execute_for_skipping_non_instantiable_config(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        manager_metrics = ConfigurationManagerMetrics()

        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", True, fetcher_metrics)

        mapper = ConfigurationMapper("configs", ObjectValueDecoderFactory(), True, manager_metrics)
        manager = ConfigurationManager()

        reader = ConfigurationReader("first-app", ["/configs-non-instantiable.json", "/configs.json"],
                                     fetcher, mapper, manager, manager_metrics, 2)

        reader.execute()

        xj_config: XJConfig = manager.get_object("configs.XJConfig", self.qa_context, None)

        self.assertEqual(["xj2001"], xj_config.hosts)
        self.assertEqual(1, manager_metrics.updates)
        self.assertEqual(1, manager_metrics.non_instantiable_skips)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)
