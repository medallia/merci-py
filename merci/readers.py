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
Classes for reading and storing feature flags and configs.
"""
import collections
import hashlib
from json import JSONDecodeError
from typing import Dict, List

from merci.fetchers import ConfigurationFetcher
from merci.metrics import ConfigurationReaderMetrics
from merci.structure import Configuration, Context
from merci.managers import ConfigurationStoreUpdater
from merci.deserialization import ConfigurationMapper


class ConfigurationReader:
    """
    Reader for feature flags and configs. Uses configuration fetcher to retrieve JSON content, i.e.
    from a local file system or a remote server. After mapping the JSON to an in-memory feature flag
    or config hierarchy , it stores the new value structure in the configuration store.
    """
    def __init__(self, application: str, file_names: List[str],
                 fetcher: ConfigurationFetcher,
                 mapper: ConfigurationMapper,
                 configuration_store: ConfigurationStoreUpdater,
                 metrics: ConfigurationReaderMetrics,
                 maximum_skips: int):
        self.application: str = application
        self.file_names: List[str] = file_names
        self.fetcher: ConfigurationFetcher = fetcher
        self.mapper: ConfigurationMapper = mapper
        self.configuration_store: ConfigurationStoreUpdater = configuration_store
        self.metrics = metrics
        # Hash of configuration content from response of previous fetch request. */
        self.previous_hash: bytes = 0
        # Maximum number of times the injected configuration store will not be updated in case of same content. */
        self.maximum_skips = maximum_skips
        # Number of same-content skips left before updating the injected configuration store. */
        self.skips_left = maximum_skips

    def execute(self):
        """ Execute fetch, parse and store of configurations. """
        digest = hashlib.sha256()
        content_map: Dict[str, str] = self.fetcher.fetch_files(
            self.application, self.file_names)
        ordered_content_map: Dict[str, str] = collections.OrderedDict(
            sorted(content_map.items()))
        for file_name, content in ordered_content_map.items():
            digest.update(bytes(file_name, 'UTF-8'))
            digest.update(bytes(content, 'UTF-8'))
        latest_hash: bytes = digest.digest()
        if self.skips_left > 0 and self.previous_hash == latest_hash:
            self.skips_left -= 1
            self.metrics.increment_same_content_skips()
        else:
            self.metrics.increment_new_content_updates()
            self.__update_configuration_store(content_map)
            self.previous_hash = latest_hash
            self.skips_left = self.maximum_skips

    def __update_configuration_store(self, content_map: Dict[str, str]):
        """ Parse configuration content and Update configuration store with latest values. """
        configuration_cache: Dict[str, Configuration] = {}
        num_configurations = 0
        num_content_failures = 0
        for content in content_map.values():
            try:
                configurations: Dict[str, Context] = self.mapper.read_value(content)
                num_configurations += len(configurations)
                configuration_cache.update(configurations)
            except (JSONDecodeError, IOError):
                num_content_failures += 1
        self.metrics.increment_content_failures(num_content_failures)
        if num_content_failures > 0:
            raise IOError("Bad configuration content.")
        self.metrics.increment_name_duplicates(num_configurations -
                                               len(configuration_cache))
        self.metrics.increment_updates(len(configuration_cache))
        self.configuration_store.set_configuration_store(configuration_cache)
