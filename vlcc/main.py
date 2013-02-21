# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys
import commands

from multiprocessing import Pool

import logging

from argparse import ArgumentParser

from .core import __version__, __description__
from .core import logger, options, initialize, fail_with_error
from .conf import config

from .build import build
from .compare import compare


def get_dependencies():
    """Returns unsatisfied dependencies list.
    """

    dependencies = []
    for cmd in ['debootstrap', 'gnuplot', 'wget']:
        status, _ = commands.getstatusoutput(cmd + ' --version')

        if status != 0:
            dependencies.append(cmd)
    return dependencies


def main():
    """VLCC runner entry point function.
    """

    argparser = ArgumentParser(description=__description__)

    argparser.add_argument('movie', metavar='MOVIE',
                           help='A movie file to play')
    argparser.add_argument('versions', metavar='VERSION',
                           type=str.lower, nargs='+',
                           help='VLC version number')
    argparser.add_argument('--clean', action="store_true",
                           dest='clean', default=False,
                           help="clean build directory before doing a build")
    argparser.add_argument('-b', '--build-dir', dest='build_dir',
                           default="./build/",
                           help="build directory path, `./build/` by default")
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

    initialize(options.config)

    if os.getuid() != 0:
        fail_with_error("Root privileges are required to run this script")

    try:
        login = os.getlogin()
    except OSError:
        fail_with_error("Controlling terminal is not available")
    else:
        if login == 'root':
            fail_with_error("VLC cannot be run as root, sorry")

    if options.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Switched to debug mode")

    dependencies = get_dependencies()

    if dependencies:
        fail_with_error("Please install {0} to run this script"
                        .format(", ".join(dependencies)))

    try:
        os.makedirs(options.build_dir)
    except OSError:
        pass

    missing_versions = set(options.versions) - set(config.get('versions', {}))

    if missing_versions:
        fail_with_error("VLC version{0[s]} {0[ver]} description{0[s]} "
                        "not found in {0[config]}"
                        .format(dict(
                            s='s' if len(missing_versions) > 1 else '',
                            ver=", ".join(missing_versions),
                            config=options.config)
                        ))
    # Building
    pool = Pool()
    pool.map_async(build, options.versions).get(timeout=sys.maxint)

    # Uncomment for sequential build
    #[build(version)
    # for version in options.versions]

    # Comparing
    compare()

    logger.info("Finished.")
