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
Configs for integration tests.
"""
from typing import List


class XJConfig:
    """ Config class for integration tests. """
    def __init__(self,
                 hosts: List[str] = None,
                 port: int = -1,
                 timeout_seconds: int = -1,
                 description: str = 'hard-coded invalid config'):
        self.hosts = hosts
        if self.hosts is None:
            self.hosts = ['invalid-host']
        self.port = port
        self.timeout_seconds = timeout_seconds
        self.description = description
