# -*- coding: utf-8 -*-
import sys

import argparse

import logging


__description__ = "VLC versions measurement and comparison tool"
__version__ = "0.01"


__all__ = ['options', 'logger', 'initialize', 'get_child_logger',
           'fail_with_error']


options = argparse.Namespace()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('vlcc')

argparser = argparse.ArgumentParser(description=__description__)

# Exit function to call on failure
_exit_func = lambda: sys.exit(-1)


def initialize(exit_func=None):
    """Initializes the core.

    @param config_path: config path string
    """
    from .conf import load_config
    from .db import db

    global _exit_func

    # Adding common options to argparser

    argparser.add_argument('--verbose', action="store_true",
                           dest='verbose',
                           help="force verbose output")
    argparser.add_argument('-d', '--debug', action="store_true",
                           dest='debug', default=False,
                           help="enable debug mode")
    argparser.add_argument('-t', '--traceback', action="store_true",
                           dest='traceback',
                           help="dump traceback on errors")
    argparser.add_argument('-v', '--version', action="version",
                           version=__version__,
                           help="print program version")
    argparser.add_argument('-c', '--config', dest='config',
                           default="./config.yaml",
                           help="config file path, `config.yaml` by default")

    argparser.parse_args(namespace=options)

    if options.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Switched to debug mode")

    if exit_func is not None:
        _exit_func = exit_func

    load_config(options.config)
    db.connect()


def get_child_logger(suffix):
    """Returns new core logger's descendant with the same logging level.

    @param suffix: suffix string
    """
    child = logger.getChild(suffix)
    child.setLevel(logger.level)

    return child


def fail_with_error(message):
    """Prints the error message and terminates the program execution.

    @param message: error message
    """

    exc_info = getattr(options, 'traceback', False) and any(sys.exc_info())
    logger.critical(message, exc_info=exc_info)

    _exit_func()
