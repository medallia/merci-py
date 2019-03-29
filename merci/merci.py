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
Entry setup classes for using Merci.

Sample code on how to use Merci:

# Initialize file system or any application-specific configuration fetcher.
fetcher: ConfigurationFetcher = FilesystemConfigurationFetcher(self.resource_dir + "/configurations",
    False, ConfigurationFetcherMetrics())

# Instantiate Merci with configuration fetcher and default background scheduler. */
merci: Merci = Merci(fetcher)

# Create a new feature flag manager and register a JSON file with feature flags.
feature_flag_manager: FeatureFlagManager = merci.add_feature_flag_manager("myapp")
    .register_file("/featureflags.json")
    .build()

# Create a new config manager and register a JSON file with runtime configs.
config_manager: ConfigManager = merci.add_config_manager("myapp")
    .register_file("/configs.json")
    .build()

# Create configuration loader with three minutes refresh interval
loader: ConfigurationLoader = merci.create_loader(180)

# Start loader
loader.start()

"""
import time
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from merci.loaders import ConfigurationLoader
from merci.managers import ConfigurationManager, FeatureFlagManager, ConfigManager
from merci.deserialization import SingleValueDecoderFactory, ObjectValueDecoderFactory, ValueDecoderFactory
from merci.metrics import ConfigurationManagerMetrics, ConfigurationLoaderMetrics
from merci.readers import ConfigurationMapper, ConfigurationReader
from merci.fetchers import ConfigurationFetcher


class ConfigurationManagerBuilder:
    """ Builder for configuration manager. """
    def __init__(self, value_decoder_factory: ValueDecoderFactory,
                 root_node: str, application: str,
                 fetcher: ConfigurationFetcher,
                 readers: List[ConfigurationReader],
                 skip_non_instantiable: bool, maximum_skips: int):
        self.value_decoder_factory = value_decoder_factory
        self.application = application
        self.fetcher = fetcher
        self.readers = readers
        self.skip_non_instantiable = skip_non_instantiable
        self.maximum_skips = maximum_skips
        self.file_names = []
        self.root_node = root_node
        self.metrics: ConfigurationManagerMetrics = None

    def set_metrics(self, metrics: ConfigurationManagerMetrics):
        """ Set metrics collector for config manager. """
        self.metrics = metrics
        return self

    def register_file(self, file_name: str):
        """ Register name of file with configurations. """
        self.file_names.append(file_name)
        return self

    def build(self) -> ConfigurationManager:
        manager = ConfigurationManager()
        if self.metrics is None:
            self.metrics = ConfigurationManagerMetrics()
        mapper = ConfigurationMapper(self.root_node,
                                     self.value_decoder_factory,
                                     self.skip_non_instantiable, self.metrics)
        reader = ConfigurationReader(self.application, self.file_names,
                                     self.fetcher, mapper, manager,
                                     self.metrics, self.maximum_skips)
        self.readers.append(reader)
        return manager


class FeatureFlagManagerBuilder:
    """ Builder for feature flag manager. """
    def __init__(self, application: str, fetcher: ConfigurationFetcher,
                 readers: List[ConfigurationReader], skip_non_instantiable: bool,
                 maximum_skips: int):
        self.builder = ConfigurationManagerBuilder(SingleValueDecoderFactory(),
                                                   "feature-flags", application,
                                                   fetcher, readers,
                                                   skip_non_instantiable, maximum_skips)

    def register_file(self, file_name: str):
        """ Register name of file with feature flags. """
        self.builder.register_file(file_name)
        return self

    def set_metrics(self, metrics: ConfigurationManagerMetrics):
        """ Set metrics collector for feature flags manager. """
        self.builder.set_metrics(metrics)
        return self

    def build(self) -> FeatureFlagManager:
        configuration_manager = self.builder.build()
        return FeatureFlagManager(configuration_manager)


class ConfigManagerBuilder:
    """ Builder for config manager. """
    def __init__(self, application: str, fetcher: ConfigurationFetcher,
                 readers: List[ConfigurationReader], skip_non_instantiable: bool,
                 maximum_skips: int):
        self.builder = ConfigurationManagerBuilder(ObjectValueDecoderFactory(),
                                                   "configs", application,
                                                   fetcher, readers,
                                                   skip_non_instantiable, maximum_skips)

    def register_file(self, file_name: str):
        """ Register name of file with configs. """
        self.builder.register_file(file_name)
        return self

    def set_metrics(self, metrics: ConfigurationManagerMetrics):
        """ Set metrics collector for config manager. """
        self.builder.set_metrics(metrics)
        return self

    def build(self) -> ConfigManager:
        configuration_manager: ConfigurationManager = self.builder.build()
        return ConfigManager(configuration_manager)


class Merci:
    """ Entry setup class for Merci. """
    def __init__(self,
                 fetcher: ConfigurationFetcher,
                 scheduler: BackgroundScheduler = BackgroundScheduler()):
        """
        Initialize Merci with configuration fetcher and a background scheduler.
        :param fetcher: configuration fetcher
        :param scheduler: scheduler, used by configuration loader
        """
        self.fetcher = fetcher
        self.scheduler = scheduler
        self.readers: List[ConfigurationReader] = []
        self.skip_non_instantiable = True
        self.maximum_skips = 0
        self.loader_metrics: ConfigurationLoaderMetrics = None

    def set_metrics(self, metrics: ConfigurationLoaderMetrics):
        """ Set metrics collector for configuration loader. """
        self.loader_metrics = metrics

    def maximum_skips(self, maximum_skips: int):
        """ Set maximum number of times the in-memory configuration store will not be updated in case of same content. """
        self.maximum_skips = maximum_skips

    def skip_non_instantiable_configurations(self):
        """ Continue loading configurations, just skip each non-instantiable configuration. """
        self.skip_non_instantiable = True

    def fail_non_instantiable_configurations(self):
        """ Stop loading of all configurations in case of a non-instantiable configuration. """
        self.skip_non_instantiable = False

    def add_feature_flag_manager(self, application: str):
        """ Create builder with new feature flag manager for provided application. """
        return FeatureFlagManagerBuilder(application, self.fetcher, self.readers,
                                         self.skip_non_instantiable, self.maximum_skips)

    def add_config_manager(self, application: str):
        """ Create builder with new config manager for provided application. """
        return ConfigManagerBuilder(application, self.fetcher, self.readers,
                                    self.skip_non_instantiable, self.maximum_skips)

    def create_and_start_loader(self, refresh_interval_seconds: time) -> ConfigurationLoader:
        """ Create new configuration loader with provided refresh interval and immediately start it. """
        loader = self.create_loader(refresh_interval_seconds)
        loader.start()
        return loader

    def create_loader(self, refresh_interval_seconds: int) -> ConfigurationLoader:
        """ Creates new configuration loader with provided refresh interval. """
        if self.loader_metrics is None:
            self.loader_metrics = ConfigurationLoaderMetrics()
        loader = ConfigurationLoader(self.readers, self.scheduler,
                                     refresh_interval_seconds,
                                     self.loader_metrics)
        # clear readers list
        self.readers = []
        return loader
