# -*- coding: utf-8 -*-

import yaml

from .core import fail_with_error


# Global configuration dictionary
config = {}


__all__ = ['config', 'load_config']


def load_config(config_path):
    """Loads YAML configuration file.

    @param config_path: config path
    """
    try:
        cfg = yaml.load(file(config_path))
    except IOError:
        fail_with_error("Config file not found ({0})".format(config_path))
    except yaml.YAMLError:
        fail_with_error("Error parsing {0}, specify --traceback option for "
                        "details".format(config_path))
    config.update(cfg)
