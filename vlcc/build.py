# -*- coding: utf-8 -*-

import time

import os

import subprocess

from .core import logger, options, fail_with_error
from .conf import config


__all__ = ['build']


def build_state(state):
    """Updates the build state in case of successful execution of the
    decorated method.
    """

    def _build_state(method):
        def __build_state(*args, **kwargs):
            result = method(*args, **kwargs)

            states = ['jail_created',
                      'source_unpacked',
                      'configured',
                      'compiled',
                      'installed']

            assert state in states

            return result
        return __build_state
    return _build_state


class Builder(object):
    """Builder class to create a chroot jail with debootstrap and building a
    VLC version.

    Call the run() method to start a build.
    """

    def __init__(self, version):
        self.version = version
        self.build_logger = logger.getChild(version)
        self.build_logger.setLevel(logger.level)
        self.log_dir = os.path.join(options.build_dir, 'log-' + version)
        self.version_config = config['versions'][version]
        self.chroot_dir = os.path.join(options.build_dir, 'jail-' + version)
        self.chroot_src_path = os.path.join('/usr/local/src', 'vlc-' + version)

        try:
            os.makedirs(self.log_dir)
        except OSError:
            pass

    def debug_command(self, command):
        self.build_logger.debug("Executing `{0}`".format(" ".join(command)))

    def exec_command(self, command, log_to=None, action=None):
        """Executes a command.

        @param command: command string
        @param log_to: log file name
        @param action: action string to log
        """

        exec_log_path = log_to and os.path.join(self.log_dir, log_to)

        if action is not None:
            message = ("{0} VLC" +
                       ("" if log_to is None else ", see {1} for details"))
            self.build_logger.info(message.format(action.capitalize(),
                                                  exec_log_path))

        self.debug_command(command)

        if log_to is None:
            retcode = subprocess.call(command)
        else:
            with open(exec_log_path, 'wt') as log_file:
                retcode = subprocess.call(command,
                                          stdout=log_file, stderr=log_file)

        if 0 != retcode:
            message = ("Execution of {0} failed" +
                       ("" if log_to is None else ", see the log for details"))

            fail_with_error(message.format(command[0]))

    def exec_chroot(self, command, log_to, action):
        """Executes a command with chroot. Accepts same parameters as
        exec_command() method.
        """

        command = ['chroot', self.chroot_dir, 'sh', '-c',
                   'cd {0}; {1}'.format(self.chroot_src_path, command)]

        self.exec_command(command, log_to, action)

    def start_download(self):
        """Downloads the sources archive with wget.
        """

        ext = 'xz' if self.version[0] == '2' else 'bz2'
        filename = "vlc-{0}.tar.{1}".format(self.version, ext)

        self.download_url = "/".join((config['download_url'],
                                      self.version, filename))
        self.archive_path = os.path.join(options.build_dir, filename)

        command = ['wget', '-c', '-P', options.build_dir, '-O',
                   self.archive_path, self.download_url]

        self.debug_command(command)

        if options.verbose:
            output = None
        else:
            output = subprocess.PIPE

        self.download_proc = subprocess.Popen(command,
                                              stdout=output, stderr=output)

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
            else:
                return

    @build_state('jail_created')
    def create_jail(self):
        """Creates a chroot jail with debootstrap.
        """

        command = ['debootstrap']

        if 'dependencies' in self.version_config:
            deps = ['build-essential'] + self.version_config['dependencies']
            command.append('--include=' + ",".join(set(deps)))

        if 'arch' in self.version_config:
            command.append('--arch=' + self.version_config['arch'])

        command += [self.version_config['distr'], self.chroot_dir]

        self.exec_command(command, log_to='debootstrap.log',
                          action="Creating chroot jail for ")

    @build_state('source_unpacked')
    def unpack(self):
        """Unpacks the downloaded sources archive.
        """

        self.build_logger.info("Unpacking the downloaded archive")

        command = ['tar', '-C',
                   os.path.join(self.chroot_dir, 'usr/local/src/'),
                   '-xf', self.archive_path]

        self.exec_command(command)

    @build_state('configured')
    def configure(self):
        """Launches the `configure` script from jail.
        """

        configure_args = self.version_config.get('configure', '')
        command = './configure --prefix=/usr ' + configure_args

        self.exec_chroot(command, log_to='configure.log', action="configuring")

    @build_state('compiled')
    def make(self):
        self.exec_chroot('make', log_to='make.log', action="compiling")

    @build_state('installed')
    def install(self):
        self.exec_chroot('make install', log_to='install.log',
                         action="installing")

    def run(self):
        """This one makes the whole magic.
        """

        self.start_download()
        self.create_jail()
        self.finish_download()
        self.unpack()
        self.configure()
        self.make()
        self.install()


def build(version):
    """Creates a chroot jail with debootstrap and builds a VLC version.

    @param version: VLC version string
    """

    return Builder(version).run()
