# -*- coding: utf-8 -*-

import os

import subprocess

from .core import logger, options, fail_with_error
from .conf import config


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
