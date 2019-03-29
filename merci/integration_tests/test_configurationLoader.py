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
Integration tests for configuration loader.
"""
import os

from unittest import TestCase
from apscheduler.schedulers.background import BackgroundScheduler

from configs import XJConfig
from merci.loaders import ConfigurationLoader
from merci.deserialization import ConfigurationMapper, SingleValueDecoderFactory, ObjectValueDecoderFactory
from merci.metrics import ConfigurationManagerMetrics, ConfigurationFetcherMetrics, ConfigurationLoaderMetrics
from merci.readers import ConfigurationReader
from merci.fetchers import FilesystemConfigurationFetcher
from merci.managers import ConfigurationManager, ConfigManager, FeatureFlagManager


class TestConfigurationLoader(TestCase):
    """ Unit tests for configuration loader. """

    empty_context = {}
    qa_context = {"environment": "qa"}

    resource_dir = os.path.dirname(
        os.path.realpath('__file__')) + "/resources"

    def test_loader(self):
        fetcher_metrics = ConfigurationFetcherMetrics()
        fetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations", False, fetcher_metrics)

        feature_metrics = ConfigurationManagerMetrics()
        feature_mapper = ConfigurationMapper("feature-flags",
                                             SingleValueDecoderFactory(),
                                             False, feature_metrics)

        feature_configuration_manager = ConfigurationManager()
        feature_manager = FeatureFlagManager(feature_configuration_manager)
        feature_reader = ConfigurationReader("first-app",
                                             ["/featureflags.json"],
                                             fetcher,
                                             feature_mapper,
                                             feature_configuration_manager,
                                             feature_metrics,
                                             2)

        config_metrics = ConfigurationManagerMetrics()
        config_mapper = ConfigurationMapper("configs",
                                            ObjectValueDecoderFactory(), False,
                                            config_metrics)

        config_configuration_manager = ConfigurationManager()
        config_manager = ConfigManager(config_configuration_manager)
        config_reader = ConfigurationReader("first-app",
                                            ["/configs.json"],
                                            fetcher,
                                            config_mapper,
                                            config_configuration_manager,
                                            config_metrics,
                                            2)

        loader_metrics = ConfigurationLoaderMetrics()
        configuration_loader = ConfigurationLoader([feature_reader, config_reader],
                                                   BackgroundScheduler(), 3,
                                                   loader_metrics)

        configuration_loader.start()

        self.assertEqual(True, feature_manager.is_active("enable-feature-all", self.empty_context, False))
        self.assertEqual(False, feature_manager.is_active("enable-feature-none", self.empty_context, True))

        xj_config: XJConfig = config_manager.get_config(XJConfig, self.qa_context)

        self.assertEqual(["xj2001"], xj_config.hosts)

        self.assertEqual(2, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(2, fetcher_metrics.requests)
        self.assertEqual(0, fetcher_metrics.missing_files)
        self.assertEqual(0, fetcher_metrics.failures)

        configuration_loader.shutdown()
