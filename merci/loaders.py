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
Classes for loading feature flags and configs.
"""
import time
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from merci.deserialization import InstantiationException
from merci.metrics import ConfigurationLoaderMetrics
from merci.readers import ConfigurationReader


class ConfigurationLoader:
    """
    """
    def __init__(self, readers: List[ConfigurationReader],
                 execution_scheduler: BackgroundScheduler,
                 refresh_interval_seconds: time,
                 metrics: ConfigurationLoaderMetrics):
        """
        Initialize loader with a list of configuration readers and a background scheduler.

        :param readers: list of configuration readers
        :param execution_scheduler: scheduler, that periodically reads, parses and stores configurations
        :param refresh_interval_seconds: time in seconds between scheduled loading tasks
        :param metrics: metrics for loader
        """
        self.readers: List[ConfigurationReader] = readers
        self.execution_scheduler: BackgroundScheduler = execution_scheduler
        self.refresh_interval_seconds: time = refresh_interval_seconds
        self.metrics = metrics

    def start(self):
        """ Immediately execute configuration readers, then schedule next execution. """
        self.execute_readers()
        self.execution_scheduler.add_job(
            self.execute_readers,
            trigger='interval',
            seconds=self.refresh_interval_seconds)
        self.execution_scheduler.start()

    def execute_readers(self):
        """ Sequentially execute configuration readers. """
        for reader in self.readers:
            try:
                self.metrics.increment_configuration_requests()
                reader.execute()
            except (IOError, InstantiationException):
                self.metrics.increment_configuration_failures()
            except Exception as exception:
                self.metrics.increment_configuration_failures()
                raise exception

    def shutdown(self):
        """ Stop scheduler. """
        self.execution_scheduler.shutdown()
