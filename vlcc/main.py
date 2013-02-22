# -*- coding: utf-8 -*-

import os
import sys
import commands

from multiprocessing import Pool

from .core import logger, options, argparser
from .core import initialize, fail_with_error
from .conf import config

from .build import build
from .compare import compare


__all__ = ['main']


def main():
    """VLCC runner entry point function.
    """

    # VLCC runner specific arguments
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

    # Initializing the core
    initialize()

    if os.getuid() != 0:
        fail_with_error("Root privileges are required to run this script")

    # Checking dependencies
    dependencies = []

    for cmd in ['debootstrap', 'gnuplot', 'wget']:
        status, _ = commands.getstatusoutput(cmd + ' --version')

        if status != 0:
            dependencies.append(cmd)

    if dependencies:
        fail_with_error("Please install {0} to run this script"
                        .format(", ".join(dependencies)))

    # Creating build directory
    try:
        os.makedirs(options.build_dir)
    except OSError:
        pass

    # Checking versions
    missing_versions = set(options.versions) - set(config.get('versions', {}))

    if missing_versions:
        params = dict(
            s='s' if len(missing_versions) > 1 else '',
            ver=", ".join(missing_versions),
            config=options.config,
        )
        fail_with_error("VLC version{0[s]} {0[ver]} description{0[s]} "
                        "not found in {0[config]}"
                        .format(params))

    # Building
    pool = Pool(len(options.versions))
    pool.map_async(build, options.versions).get(timeout=sys.maxint)

    # Uncomment for building sequentially
    #[build(version)
    # for version in options.versions]

    # Comparing
    compare()

    logger.info("Finished.")
