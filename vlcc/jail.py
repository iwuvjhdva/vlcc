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

    def exec_command(self, command, async=False, **popen_kwargs):
        """Executes a command.

        @param command: command string or sequence
        @param async: returns immediately if True
        @popen_kwargs: subprocess.Popen kwargs

        @return: process instance
        """
        self.logger.debug("Executing `{0}`".format(" ".join(command)))

        output_specified = (set(['stdout', 'stderr'])
                            .issubset(popen_kwargs.keys()))

        # Suppressing the output in non-verbose mode
        if not options.verbose and not output_specified:
            popen_kwargs['stdout'] = popen_kwargs['stderr'] = subprocess.PIPE

        process = subprocess.Popen(command, **popen_kwargs)

        if not async:
            if 0 != process.wait():
                fail_with_error("Execution of {0} failed".format(command[0]))

        return process

    def exec_chroot(self, command, cwd=None, userspec=None,
                    async=False, **popen_kwargs):
        """Executes a command with chroot.

        @param command: command string or sequence
        @param cwd: chroot working directory string
        @param userspec: `USER[:GROUP]` string to use
        @param async: returns immediately if True
        @popen_kwargs: subprocess.Popen kwargs
        """

        if isinstance(command, basestring):
            command = [command]

        cmd = ['chroot']

        if userspec is not None:
            cmd += ['--userspec=' + userspec]

        cmd += [self.chroot_dir]

        if cwd is not None:
            cmd += ['bash', '-c', 'cd {0}; {1}'
                    .format(cwd, " ".join(command))]
        else:
            cmd += command

        return self.exec_command(cmd, async, **popen_kwargs)

    def _log_exec(self, method, log_to, log_message, **kwargs):
        """Calls the method with kwargs passed and logs the results
        into a file.

        @param method: either self.exec_chroot or self.exec_command
        @param log_to: log file name
        @param log_message: message string to log
        """

        log_path = os.path.join(self.log_dir, log_to)

        self.logger.info("{0}, see {1} for details"
                         .format(log_message.capitalize(), log_path))

        with open(log_path, 'wt') as log_file:
            return method(stdout=log_file, stderr=log_file, **kwargs)

    def log_command(self, command, log_to, log_message):
        """Executes a command and logs the results into a file.

        @param command: command string or sequence
        @param log_to: log file name
        @param log_message: message string to log
        """

        kwargs = dict(command=command)
        return self._log_exec(self.exec_command, log_to, log_message, **kwargs)

    def log_chroot(self, command, log_to, log_message,
                   cwd=None, userspec=None):
        """Executes a chroot command and logs the results into a file.

        @param command: command string or sequence
        @param log_to: log file name
        @param log_message: message string to log
        @param cwd: chroot working directory string
        """

        kwargs = dict(command=command, cwd=cwd, userspec=userspec)
        return self._log_exec(self.exec_chroot, log_to, log_message, **kwargs)

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

        self.log_command(command, log_to='debootstrap.log',
                         log_message="Creating chroot jail for VLC")

        # Creating vlcc user
        self.exec_chroot(['useradd', 'vlcc'])
