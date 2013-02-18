# -*- coding: utf-8 -*-

import time

import os

import subprocess

from .core import logger, options, fail_with_error
from .conf import config


__all__ = ['build']


class Builder(object):
    """Builder class to create a chroot jail with debootstrap and building a
    VLC version.

    Call the run() method to start a build.
    """

    def __init__(self, version):
        self.version = version
        self.build_logger = logger.getChild(version)
        self.build_logger.setLevel(logger.level)
        self.version_config = config['versions'][version]
        self.log_dir = os.path.join(options.build_dir, 'log-' + version)
        self.build_dir = os.path.join(options.build_dir, 'jail-' + version)

        try:
            os.makedirs(self.log_dir)
        except OSError:
            pass

    def debug_command(self, command):
        self.build_logger.debug("Executing `{0}`".format(" ".join(command)))

    def start_download(self):
        params = dict(
            url=config['download_url'],
            ver=self.version,
            ext='xz' if self.version[0] == '2' else 'bz2',
        )

        self.download_url = ("{0[url]}/{0[ver]}/vlc-{0[ver]}.tar.{0[ext]}"
                             .format(params))

        command = ['wget', '-c', '-p', '-P',
                   options.build_dir, self.download_url]

        self.debug_command(command)
        self.download_proc = subprocess.Popen(command)

        self.build_logger.info("Starting download from " + self.download_url)

    def finish_download(self):
        """Waits for the download to finish.
        """

        while True:
            retval = self.download_proc.poll()

            if retval is None:
                time.sleep(.1)
            elif retval != 0:
                fail_with_error("Download failed :-(")

    def create_jail(self):
        """Creates a chroot jail with debootstrap.
        """

        debootsrap_log_path = os.path.join(self.log_dir, 'debootstrap.log')

        self.build_logger.info("Creating chroot jail for VLC {0}, see {1} for "
                               "details"
                               .format(self.version, debootsrap_log_path))

        command = ['debootstrap']

        if 'dependencies' in self.version_config:
            command.append('--include=' +
                           ",".join(self.version_config['dependencies']))

        if 'arch' in self.version_config:
            command.append('--arch=' +
                           self.version_config['arch'])

        command += [self.version_config['distr'], self.build_dir]

        self.debug_command(command)

        with open(debootsrap_log_path, 'wt') as log_file:
            if 0 != subprocess.call(command, stdout=log_file, stderr=log_file):
                fail_with_error(
                    "Execution of {0} failed, see the log for details"
                    .format('debootstrap'))

    def configure(self):
        """Unpacks the downloaded archive and launches configure.
        """

        self.build_logger.info("Unpacking the downloaded archive")

        configure_log_path = os.path.join(self.log_dir, 'configure.log')

        self.build_logger.info("Configuring VLC, see {0} for details"
                               .format(configure_log_path))

        # Starting ./configure
        # vlc_dir = '/usr/local/src/vlc-' + self.version
        #
        # command = ['chroot', self.build_dir,
        # os.path.join(vlc_dir, 'configure')]

    def make(self):
        pass

    def install(self):
        pass

    def run(self):
        """This makes the whole magic.
        """

        self.start_download()
        self.create_jail()
        self.finish_download()
        self.configure()
        self.make()
        self.install()


def build(version):
    """Creates a chroot jail with debootstrap and builds a VLC version.

    @param version: VLC version string
    """

    return Builder(version).run()
