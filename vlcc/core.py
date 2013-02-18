# -*- coding: utf-8 -*-
import sys

import argparse

import logging


__description__ = "VLC versions measurement and comparison tool"
__version__ = "0.01"


options = argparse.Namespace()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('vlcc')


def fail_with_error(message):
    """Prints the error message and terminates the program execution.

    @param message: error message
    """

    exc_info = getattr(options, 'traceback', False) and any(sys.exc_info())
    logger.critical(message, exc_info=exc_info)

    sys.exit(-1)
