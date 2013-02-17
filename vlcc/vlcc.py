#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys

import subprocess
import commands

import yaml

from argparse import ArgumentParser

import logging


__description__ = "VLC versions measurement and comparison tool"
__version__ = "0.01"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('vlcc')


config = None
options = None

argparser = ArgumentParser(description=__description__)


def fail_with_error(message):
    """Prints the error message and terminates the program execution.

    @param message: error message
    """

    exc_info = options.traceback and any(sys.exc_info())
    logger.error(message, exc_info=exc_info)

    sys.exit(-1)


def get_dependencies():
    """Returns unsatisfied dependencies list.
    """

    dependencies = []
    for cmd in ['debootstrap', 'gnuplot']:
        status, _ = commands.getstatusoutput(cmd + ' --version')

        if status != 0:
            dependencies.append(cmd)
    return dependencies


def build(version):
    """Creates a chroot jail with debootstrap and builds a VLC version.

    @param version: VLC version string
    """

    build_logger = logger.getChild(version)
    build_logger.setLevel(logger.level)

    version_config = config['versions'][version]

    log_dir = os.path.join(options.build_dir, 'log-' + version)
    try:
        os.makedirs(log_dir)
    except OSError:
        pass

    log_path = os.path.join(log_dir, 'debootstrap.log')

    build_logger.info("Creating chroot jail for VLC {0}, see {1} for details"
                      .format(version, log_path))

    # Creating a chroot jail
    command = ['debootstrap']

    if 'dependencies' in version_config:
        command.append(
            '--include=' +
            ",".join(version_config['dependencies'])
        )

    if 'arch' in version_config:
        command.append(
            '--arch=' + version_config['arch']
        )

    build_dir = os.path.join(options.build_dir, 'jail-' + version)
    command += [version_config['distr'], build_dir]

    build_logger.debug("Executing `{0}`".format(" ".join(command)))

    error = "Execution of {0} failed, see the log for details"

    with open(log_path, 'wt') as log_file:
        if 0 != subprocess.call(command, stdout=log_file, stderr=log_file):
            fail_with_error(error.format('debootstrap'))

    log_path = os.path.join(log_dir, 'configure.log')

    build_logger.info("Configuring VLC, see {0} for details".format(log_path))

    # Starting ./configure
    vlc_dir = '/usr/local/src/vlc-' + version

    command = ['chroot', build_dir, os.path.join(vlc_dir, 'configure')]


if __name__ == "__main__":
    argparser.add_argument('versions', metavar='VERSION', nargs='+',
                           help='VLC version number')
    argparser.add_argument('--clean', action="store_true",
                           dest='clean', default=False,
                           help="clean build directory before doing a build")
    argparser.add_argument('-b', '--build-dir', dest='build_dir',
                           default="./build/",
                           help="build directory path, `./build/` by default")
    argparser.add_argument('-c', '--config', dest='config',
                           default="./config.yaml",
                           help="config file path, `config.yaml` by default")
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

    options = argparser.parse_args()

    # Checking privileges
    if os.getuid() != 0:
        fail_with_error("Root privileges are required to run this script")

    if options.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Switched to debug mode")

    # Checking dependencies
    dependencies = get_dependencies()

    if dependencies:
        fail_with_error("Please install {0} to run this script".format(
            ", ".join(dependencies)))

    try:
        os.makedirs(options.build_dir)
    except OSError:
        pass

    # Loading the config
    try:
        config = yaml.load(file(options.config))
    except IOError as e:
        fail_with_error("Config file not found ({0})".format(options.config))
    except yaml.YAMLError:
        fail_with_error("Error parsing {0}, specify --traceback option for "
                        "details".format(options.config))

    # Extending the config by default values
    # ...

    missing_versions = set(options.versions) - set(config.get('versions', {}))
    if missing_versions:
        fail_with_error("VLC version{0[s]} {0[ver]} description{0[s]} "
                        "not found in {0[config]}"
                        .format(dict(
                            s='s' if len(missing_versions) > 1 else '',
                            ver=", ".join(missing_versions),
                            config=options.config)
                        ))
    [build(version)
     for version in options.versions]
