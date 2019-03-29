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
"""
from abc import ABC, abstractmethod


class ConfigurationMapperMetrics(ABC):
    """ Metrics for configuration mapper. """
    @abstractmethod
    def increment_non_instantiable_skips(self, count: int = 1):
        """ Increment counter for skipped updates of configs due to instantiation problems with Python classes for configs. """


class ConfigurationReaderMetrics(ABC):
    """ Metrics for configuration reader. """
    @abstractmethod
    def increment_updates(self, count: int = 1):
        """ Increment counter for successful updates of configurations. """

    @abstractmethod
    def increment_content_failures(self, count: int = 1):
        """ Increment counter for failed updates of configurations due to deserialization problems with textual content. """

    @abstractmethod
    def increment_same_content_skips(self, count: int = 1):
        """ Increment number of skipped update cycles of configurations due to same textual contents. """

    @abstractmethod
    def increment_new_content_updates(self, count: int = 1):
        """ Increment number of successful update cycles of configurations due to new textual contents. """

    @abstractmethod
    def increment_name_duplicates(self, count: int = 1):
        """ Increment counter for duplicate configuration name detections. """


class ConfigurationManagerMetrics(ConfigurationMapperMetrics,
                                  ConfigurationReaderMetrics):
    """ Metrics for configuration manager. """
    def __init__(self):
        self.updates = 0
        self.content_failures = 0
        self.same_content_skips = 0
        self.new_content_updates = 0
        self.name_duplicates = 0
        self.non_instantiable_skips = 0

    def increment_updates(self, count: int = 1):
        """ Increment counter for successful updates of configurations. """
        self.updates += count

    def increment_content_failures(self, count: int = 1):
        """ Increment counter for failed updates of configurations due to deserialization problems with textual content. """
        self.content_failures += count

    def increment_same_content_skips(self, count: int = 1):
        """ Increment number of skipped update cycles of configurations due to same textual contents. """
        self.same_content_skips += count

    def increment_new_content_updates(self, count: int = 1):
        """ Increment number of successful update cycles of configurations due to new textual contents. """
        self.new_content_updates += count

    def increment_name_duplicates(self, count: int = 1):
        """ Increment counter for duplicate configuration name detections. """
        self.name_duplicates += count

    def increment_non_instantiable_skips(self, count: int = 1):
        """ Increment counter for skipped updates of configs due to instantiation problems with Python classes for configs. """
        self.non_instantiable_skips += count


class ConfigurationFetcherMetrics:
    """ Metrics for configuration fetcher. """
    def __init__(self):
        self.requests = 0
        self.failures = 0
        self.missing_files = 0

    def increment_requests(self, count: int = 1):
        """ Increment counter for all requests, failed and successful. """
        self.requests += count

    def increment_failures(self, count: int = 1):
        """ Increment counter for failed requests. """
        self.failures += count

    def increment_missing_files(self, count: int = 1):
        """ Increment counter for missing files. """
        self.missing_files += count


class ConfigurationLoaderMetrics:
    """ Metrics for configuration loader. """
    def __init__(self):
        self.configuration_requests = 0
        self.configuration_failures = 0

    def increment_configuration_requests(self, count: int = 1):
        """ Increment counter for all requests, failed and successful. """
        self.configuration_requests += count

    def increment_configuration_failures(self, count: int = 1):
        """ Increment counter for failed requests. """
        self.configuration_failures += count
