# -*- coding: utf-8 -*-

import os

import subprocess

from .core import logger as core_logger, options, fail_with_error
from .conf import config


__all__ = ['Jail']


class Jail(object):
    """Chroot jail managing class.
    """

    def __init__(self, version, logger=core_logger):
        self.logger = logger
        self.version_config = config['versions'][version]
        self.log_dir = os.path.join(options.build_dir, 'log-' + version)
        self.chroot_dir = os.path.join(options.build_dir, 'jail-' + version)

        try:
            os.makedirs(self.log_dir)
        except OSError:
            pass

    def debug_command(self, command):
        self.logger.debug("Executing `{0}`".format(" ".join(command)))

    def exec_command(self, command, log_to=None, log_message=None):
        """Executes a command.

        @param command: command string
        @param log_to: log file name
        @param action: action string to log
        """

        if log_to is None:
            exec_log_path = None
            log_details = ""
        else:
            exec_log_path = os.path.join(self.log_dir, log_to)
            log_details = ", see {1} for details"

        if log_message is not None:
            message = log_message + log_details
            self.logger.info(message.format(log_message.capitalize(),
                                            exec_log_path))

        self.debug_command(command)

        if log_to is None:
            retcode = subprocess.call(command)
        else:
            with open(exec_log_path, 'wt') as log_file:
                retcode = subprocess.call(command,
                                          stdout=log_file, stderr=log_file)

        if 0 != retcode:
            message = "Execution of {0} failed" + log_details
            fail_with_error(message.format(command[0], "the log"))

    def exec_chroot(self, command, cwd="/", log_to=None, log_message=None):
        """Executes a command with chroot. Accepts same parameters as
        exec_command() method.
        """

        command = ['chroot', self.chroot_dir, 'bash', '-c',
                   'cd {0}; {1}'.format(cwd, command)]

        return self.exec_command(command, log_to, log_message)

    def create(self):
        """Creates a chroot jail with debootstrap.
        """

        command = ['debootstrap']

        if 'dependencies' in self.version_config:
            deps = (['build-essential', 'python'] +
                    self.version_config['dependencies'])
            command.append('--include=' + ",".join(set(deps)))

        if 'arch' in self.version_config:
            command.append('--arch=' + self.version_config['arch'])

        command += [self.version_config['distr'], self.chroot_dir]

        self.exec_command(command, log_to='debootstrap.log',
                          log_message="Creating chroot jail for VLC")

        # Creating vlcc user
        self.exec_chroot("useradd vlcc")
