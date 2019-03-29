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
Classes for fetching feature flag and config JSON content locally or from remote servers.
"""
import os
from abc import ABC, abstractmethod
from typing import List, Dict

from merci.metrics import ConfigurationFetcherMetrics


class ConfigurationFetcher(ABC):
    """ Fetches JSON configuration content. """
    @abstractmethod
    def fetch_files(self, application: str, file_names: List[str]) -> dict:
        """
        Fetch JSON configuration files.
        :param application: application name
        :param file_names: list of file names
        :return: dictionary of JSON configuration content
        """


class FilesystemConfigurationFetcher(ConfigurationFetcher):
    """ Fetches JSON configuration content from a local file system. """
    def __init__(self, base_path: str, skip_missing_files: bool,
                 metrics: ConfigurationFetcherMetrics):
        self.base_path: str = base_path
        self.skip_missing_files: bool = skip_missing_files
        self.metrics = metrics

    def fetch_files(self, application: str,
                    file_names: List[str]) -> Dict[str, str]:
        """
        Fetch JSON configuration content based on provided application and file names.
        :param application: application name
        :param file_names: list of file names
        :return: dictionary of JSON configuration content
        """
        contents: Dict[str, str] = {}
        try:
            self.metrics.increment_requests()
            for file_name in file_names:
                try:
                    content = self.fetch_file(application, file_name)
                    contents[file_name] = content
                except FileNotFoundError as exception:
                    self.metrics.increment_missing_files()
                    if not self.skip_missing_files:
                        raise exception
            return contents
        except IOError as exception:
            self.metrics.increment_failures()
            raise exception

    def fetch_file(self, application: str, file_name: str) -> str:
        """
        Fetch JSON configuration content based on provided application and a single file name.
        :param application: application name
        :param file_name: file name
        :return: JSON configuration content
        """
        path = os.path.join(self.base_path, application + file_name)
        with open(path, 'r', encoding="utf-8") as file:
            return file.read()
