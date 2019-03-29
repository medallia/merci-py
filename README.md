<!--
Copyright 2019 Medallia, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

<img src="merci-logo.png" height="180px" />

Merci is a framework for feature flags and runtime configuration, that relies on an easy-to-learn, recursive JSON structure. It was originally developed for Java<sup>(TM)</sup> applications and is available at [https://github.com/medallia/merci](https://github.com/medallia/merci). This Merci-Py framework is the Python implementation of the Java<sup>(TM)</sup> version, and works exactly the same way.

## Quick Start

This guide describes with examples how to use Merci-Py.

### Central Configuration Files

The core idea behind Merci-Py is to use a small set of central, easy to read files with a recursive JSON or YAML structure. These files are fetched by Merci-Py's configuration loader through a scheduled, asynchronous task.

The following example of a configuration file contains a feature flag called "enable-international-welcome". Its evaluation at runtime results in a true or false value, depending on the environment of the deployed application and the current user. The feature flag would only be true, which means active, if the current user is 'joe' and the environment of the deployed application instance is 'qa'.

```JSON
{
  "feature-flags": {
    "enable-international-welcome": {
      "value": false,
      "modifiers": {
        "type": "environment",
        "contexts": {
          "qa": {
            "value": false,
            "modifiers": {
              "type": "user",
              "contexts": {
                "joe": {
                  "value": true
                }
              }
            }
          },
          "production": {
            "value": false
          }
        }
      }
    }
  }
}
```

Runtime configurations - or short configs - share the same recursive structure but instead of boolean values, their values are objects, that are deserialized to config objects.

```JSON
{
  "configs": {
    "configs.DBConfig": {
      "value": {
        "hosts": [ "invalid-host" ],
        "port": -1
      },
      "modifiers": {
        "type": "environment",
        "contexts": {
          "qa": {
            "value": {
              "hosts": [ "db1.somewhere.in.qa" ],
              "port": 9889
            }
          },
          "production": {
            "value": {
              "hosts": [ "db1.somewhere.in.prod", "db2.somewhere.in.prod", "db3.somewhere.in.prod" ],
              "port": 9889
            }
          }
        }
      }
    }
  }
}
```

### Initializing Merci-Py
 
Merci-Py's configuration loader, which is responsible for scheduling retrieval and processing of configuration changes, relies on a registered configuration fetcher to retrieve the latest configuration content from a local or remote source. The library provides a generic interface, that applications implement for fetching their configuration files. For testing purposes and for applications, which only read configurations from the local file system, Merci-Py's Filesystem Configuration Fetcher class should be sufficient.

```Python
from merci.fetchers import ConfigurationFetcher
from typing import Dict, List
'''
Configuration fetcher for this application.
'''
class MyAppConfigurationFetcher(ConfigurationFetcher): 
    def fetch_files(self, application: str, file_names: List[str]) -> Dict[str,str]:
        content_dict: Dict[str,str] = {}
        # return new dictionary with requested file names and latest configuration content for the provided application name.
        return content_dict
```

Initializing Merci-Py's components should follow the example below. Both configuration manager singletons, the feature flag manager and the config manager instances should be made available to the rest of the application code.

```Python
from merci.merci import Merci

# Initialize configuration fetcher.
fetcher = MyAppConfigurationFetcher(...)

# Use Merci to initialize configuration managers and loader. */
merci = Merci(fetcher)

feature_flag_manager = merci.add_feature_flag_manager("myapp").register_file("/featureflags.json").build()
config_manager = merci.add_config_manager("myapp").register_file("/configs.json").build()

loader = merci.create_loader(180)
loader.start()
```

### Toggling Features with Merci-Py

Merci-Py's feature flag manager allows developers to selectively enable and disable parts of their code without redeploying or restarting application instances. In the following code example, the execution path is determined by applying the runtime configuration context to the external definition of the "enable-international-welcome" feature flag.

```Python
from merci.managers import FeatureFlagManager


class HelloWorld:

    feature_flag_manager: FeatureFlagManager

    def __init__(self, feature_flag_manager: FeatureFlagManager):
        self.feature_flag_manager = feature_flag_manager

    def get(self) -> str:
        runtime_context = ...
        # Evaluate, if feature flag is active based on provided runtime context.
        if self.feature_flag_manager.is_active("enable-international-welcome", runtime_context):
            return Translator().translate("Hello World!", request.locale().language())
        return "Hello World!"
```

### Using Merci-Py for Runtime Configuration

Runtime configs are managed by a registered instance of Merci-Py's config manager class. Using config objects of type HelloWorldConfig allows an external list of supported languages to be passed in at runtime.

```Python
from merci.managers import ConfigManager
from typing import List, Set


class HelloWorld:

    config_manager: ConfigManager

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def get(self) -> str:
        runtime_context = ...
        # Get config object based on provided runtime context.
        config: HelloWorldConfig = self.config_manager.get_config(HelloWorldConfig, runtime_context)
        if config.is_supported_language(request.locale().language()):
            return Translator().translate("Hello World!", request.locale().language())
        return "Hello World!"


class HelloWorldConfig:
    """
    Config class.
    """
    languages: Set[str]

    def __init__(self, languages: List[str] = None):
        if languages is None:
            self.languages = set()
        else:
            self.languages = set(languages)

    def is_supported_language(self, language: str)-> bool:
        return language in self.languages
```
