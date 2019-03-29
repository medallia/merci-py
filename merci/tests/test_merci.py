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
Unit tests for Merci class.
"""
import unittest
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from mockito import mock, when, verify
from mockito.matchers import Matcher

from merci.metrics import ConfigurationLoaderMetrics
from merci.readers import ConfigurationFetcher
from merci.merci import Merci, ConfigurationManagerMetrics


class TestMerci(unittest.TestCase):
    """ Unit tests for Merci class. """

    def test_feature_flag_manager(self):
        app = 'mini-app'
        first_features = '/first-features.json'
        second_features = '/second-features.json'
        enable_empty = '{ "feature-flags": { } }'
        enable_one = '{ "feature-flags": { "enable-feature-one": { "value": false, "modifiers": { "type": "user", "contexts": { "joe": { "value": true } } } } } }'
        enable_all = '{ "feature-flags": { "enable-all": { "value": true } } }'
        feature_contents_1 = {first_features: enable_one, second_features: enable_empty}
        feature_contents_2 = {first_features: enable_one, second_features: enable_all}

        configuration_fetcher: ConfigurationFetcher = mock()
        when(configuration_fetcher).fetch_files(app, [first_features, second_features])\
            .thenReturn(feature_contents_1)\
            .thenReturn(feature_contents_2)

        scheduler: BackgroundScheduler = mock()

        merci = Merci(configuration_fetcher, scheduler)

        feature_metrics = ConfigurationManagerMetrics()
        feature_manager = merci.add_feature_flag_manager(app)\
            .register_file(first_features)\
            .register_file(second_features)\
            .set_metrics(feature_metrics)\
            .build()

        loader_metrics = ConfigurationLoaderMetrics()
        merci.set_metrics(loader_metrics)
        loader = merci.create_loader(10)
        loader.start()

        self.assertEqual(1, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(1, feature_metrics.updates)
        self.assertEqual(0, feature_metrics.content_failures)
        self.assertEqual(0, feature_metrics.same_content_skips)
        self.assertEqual(1, feature_metrics.new_content_updates)
        self.assertEqual(0, feature_metrics.name_duplicates)
        self.assertEqual(0, feature_metrics.non_instantiable_skips)

        self.assertEqual(False, feature_manager.is_active("enable-all", {}, False))

        captor = ArgumentCaptor()
        verify(scheduler, times=1).add_job(captor, **{'trigger': 'interval'}, **{'seconds': 10})
        verify(scheduler, times=1).start()

        captured_execute_readers_method: classmethod = captor.get_value()
        captured_execute_readers_method()

        self.assertEqual(True, feature_manager.is_active("enable-all", {}, False))

        self.assertEqual(2, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(3, feature_metrics.updates)
        self.assertEqual(0, feature_metrics.content_failures)
        self.assertEqual(0, feature_metrics.same_content_skips)
        self.assertEqual(2, feature_metrics.new_content_updates)
        self.assertEqual(0, feature_metrics.name_duplicates)
        self.assertEqual(0, feature_metrics.non_instantiable_skips)

    def test_config_manager(self):
        app = 'mini-app'
        first_configs = '/first-configs.json'
        second_configs = '/second-configs.json'
        empty_config = '{ "configs": { } }'
        default_config = '{ "configs": { "test_merci.MiniConfig": { "value": { "hosts": [ "bad" ],  "port": -1 } } } }'
        one_host_config = '{ "configs": { "test_merci.MiniConfig": { "value": { "hosts": [ "one" ],  "port": 80 } } } }'
        one_name_config = '{ "configs": { "test_merci.MicroConfig": { "value": { "names": [ "me" ] } } } }'
        config_contents_1 = {
            first_configs: default_config,
            second_configs: empty_config
        }
        config_contents_2 = {
            first_configs: one_host_config,
            second_configs: one_name_config
        }

        configuration_fetcher: ConfigurationFetcher = mock()
        when(configuration_fetcher).fetch_files(app, [first_configs, second_configs]) \
            .thenReturn(config_contents_1) \
            .thenReturn(config_contents_2)

        scheduler: BackgroundScheduler = mock()

        merci = Merci(configuration_fetcher, scheduler)

        config_metrics = ConfigurationManagerMetrics()
        config_manager = merci.add_config_manager(app) \
            .register_file(first_configs) \
            .register_file(second_configs) \
            .set_metrics(config_metrics).build()

        loader_metrics = ConfigurationLoaderMetrics()
        merci.set_metrics(loader_metrics)
        merci.create_and_start_loader(10)

        self.assertEqual(1, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(1, config_metrics.updates)
        self.assertEqual(0, config_metrics.content_failures)
        self.assertEqual(0, config_metrics.same_content_skips)
        self.assertEqual(1, config_metrics.new_content_updates)
        self.assertEqual(0, config_metrics.name_duplicates)
        self.assertEqual(0, config_metrics.non_instantiable_skips)

        mini_config: MiniConfig = config_manager.get_config(MiniConfig, {})
        self.assertEqual(-1, mini_config.port)
        self.assertEqual(["bad"], mini_config.hosts)
        micro_config: MicroConfig = config_manager.get_config(MicroConfig, {})
        self.assertEqual([], micro_config.names)

        captor = ArgumentCaptor()
        verify(
            scheduler, times=1).add_job(captor, **{'trigger': 'interval'}, **{'seconds': 10})
        verify(scheduler, times=1).start()

        captured_execute_readers_method: classmethod = captor.get_value()
        captured_execute_readers_method()

        mini_config: MiniConfig = config_manager.get_config(MiniConfig, {})
        self.assertEqual(80, mini_config.port)
        self.assertEqual(["one"], mini_config.hosts)
        micro_config: MicroConfig = config_manager.get_config(MicroConfig, {})
        self.assertEqual(["me"], micro_config.names)

        self.assertEqual(2, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(3, config_metrics.updates)
        self.assertEqual(0, config_metrics.content_failures)
        self.assertEqual(0, config_metrics.same_content_skips)
        self.assertEqual(2, config_metrics.new_content_updates)
        self.assertEqual(0, config_metrics.name_duplicates)
        self.assertEqual(0, config_metrics.non_instantiable_skips)

    def test_skip_non_instantiable(self):
        app = 'mini-app'
        first_configs = '/first-configs.json'
        second_configs = '/second-configs.json'
        one_host_config = '{ "configs": { "test_merci.MiniConfig": { "value": { "hosts": [ "one" ],  "port": 80 } } } }'
        missing_class_config = '{ "configs": { "test_merci.MissingConfig": { "value": { "hosts": [ "one" ],  "port": 80 } } } }'
        config_contents = {
            first_configs: one_host_config,
            second_configs: missing_class_config
        }

        configuration_fetcher: ConfigurationFetcher = mock()
        when(configuration_fetcher).fetch_files(
            app, [first_configs, second_configs]).thenReturn(config_contents)

        scheduler: BackgroundScheduler = mock()

        merci = Merci(configuration_fetcher, scheduler)
        merci.skip_non_instantiable_configurations()

        config_metrics = ConfigurationManagerMetrics()
        config_manager = merci.add_config_manager(app) \
            .register_file(first_configs) \
            .register_file(second_configs) \
            .set_metrics(config_metrics).build()

        loader_metrics = ConfigurationLoaderMetrics()
        merci.set_metrics(loader_metrics)
        merci.create_and_start_loader(10)

        self.assertEqual(1, loader_metrics.configuration_requests)
        self.assertEqual(0, loader_metrics.configuration_failures)
        self.assertEqual(1, config_metrics.updates)
        self.assertEqual(0, config_metrics.content_failures)
        self.assertEqual(0, config_metrics.same_content_skips)
        self.assertEqual(1, config_metrics.new_content_updates)
        self.assertEqual(0, config_metrics.name_duplicates)
        self.assertEqual(1, config_metrics.non_instantiable_skips)

        mini_config: MiniConfig = config_manager.get_config(MiniConfig, {})
        self.assertEqual(80, mini_config.port)
        self.assertEqual(["one"], mini_config.hosts)

    def test_fail_non_instantiable(self):
        app = 'mini-app'
        first_configs = '/first-configs.json'
        second_configs = '/second-configs.json'
        one_host_config = '{ "configs": { "test_merci.MiniConfig": { "value": { "hosts": [ "one" ],  "port": 80 } } } }'
        missing_class_config = '{ "configs": { "test_merci.MissingConfig": { "value": { "hosts": [ "one" ],  "port": 80 } } } }'
        config_contents = {
            first_configs: one_host_config,
            second_configs: missing_class_config
        }

        configuration_fetcher: ConfigurationFetcher = mock()
        when(configuration_fetcher).fetch_files(
            app, [first_configs, second_configs]).thenReturn(config_contents)

        scheduler: BackgroundScheduler = mock()

        merci = Merci(configuration_fetcher, scheduler)
        merci.fail_non_instantiable_configurations()

        config_metrics = ConfigurationManagerMetrics()
        config_manager = merci.add_config_manager(app) \
            .register_file(first_configs) \
            .register_file(second_configs) \
            .set_metrics(config_metrics).build()

        loader_metrics = ConfigurationLoaderMetrics()
        merci.set_metrics(loader_metrics)

        merci.create_and_start_loader(10)

        self.assertEqual(1, loader_metrics.configuration_requests)
        self.assertEqual(1, loader_metrics.configuration_failures)
        self.assertEqual(0, config_metrics.updates)
        self.assertEqual(0, config_metrics.content_failures)
        self.assertEqual(0, config_metrics.same_content_skips)
        self.assertEqual(1, config_metrics.new_content_updates)
        self.assertEqual(0, config_metrics.name_duplicates)
        self.assertEqual(0, config_metrics.non_instantiable_skips)

        mini_config: MiniConfig = config_manager.get_config(MiniConfig, {})
        self.assertEqual(-1, mini_config.port)
        self.assertEqual([], mini_config.hosts)


class ArgumentCaptor(Matcher):
    """
    Captor for method arguments.
    """
    def __init__(self):
        """"""
        self.value = None

    def matches(self, arg):
        """"""
        self.value = arg
        return True

    def get_value(self):
        """"""
        return self.value


class MiniConfig:
    """
    Config class for unit tests.
    """
    def __init__(self, hosts: List[str] = None, port: int = -1):
        """ Initialize config object. """
        if hosts is None:
            self.hosts = []
        else:
            self.hosts = hosts
        self.port = port


class MicroConfig:
    """
    Config class for unit tests.
    """
    def __init__(self, names: List[str] = None):
        """ Initialize config object. """
        if names is None:
            self.names = []
        else:
            self.names = names
