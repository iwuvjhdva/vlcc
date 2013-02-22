# -*- coding: utf-8 -*-

import os
import shutil

import yaml

from .core import fail_with_error


# Global configuration dictionary
config = {}


__all__ = ['config', 'load_config']


def load_config(config_path):
    """Loads YAML configuration file.

    @param config_path: config path
    """

    if not os.path.exists(config_path):
        # Copying default config into the current working dir

        cfg_path = os.path.join(os.path.dirname(__file__), 'misc/config.yaml')

        try:
            shutil.copy2(cfg_path, '.')
        except OSError:
            pass
        else:
            config_path = './config.yaml'

    try:
        cfg = yaml.load(file(config_path))
    except IOError:
        fail_with_error("Config file not found ({0})".format(config_path))
    except yaml.YAMLError:
        fail_with_error("Error parsing {0}, specify --traceback option for "
                        "details".format(config_path))
    config.update(cfg)
