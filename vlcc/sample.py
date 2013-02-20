# -*- coding: utf-8 -*-

import itertools

import os
import subprocess

import psutil

from .core import options, get_child_logger, fail_with_error
from .jail import Jail


__all__ = ['sample', 'compare']


class Sampler(object):
    def __init__(self, version):
        self.sample_logger = get_child_logger(version)
        self.movie_filename = os.path.basename(options.movie)
        self.jail = Jail(version, self.sample_logger)

        # Hardlinking the dummy player and the video into the jail
        misc = os.path.join(os.path.dirname(__file__), 'misc/')
        chdir = self.jail.chroot_dir + '/'

        # Hardlinks (src, dest) tuples
        hardlinks = (
            (misc + 'play.py', chdir + 'play.py'),
            (misc + 'vlc.py', chdir + 'vlc.py'),
            (os.path.abspath(options.movie), chdir + self.movie_filename),
        )

        for src, dest in hardlinks:
            try:
                os.link(src, dest)
            except OSError:
                pass

    def play(self):
        """Puts the dummy player into the jail and runs it.
        """

        # Calling the player
        command = ['chroot', '--userspec', 'vlcc:vlcc',
                   self.jail.chroot_dir, 'python', 'play.py',
                   self.movie_filename]

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE)

    def run(self):
        self.play()

        process = psutil.Process(self.process.pid)

        counter = itertools.count()
        retcode = None

        while retcode is None:
            retcode = self.process.poll()

            interval = next(counter)
            cpu = int(process.get_cpu_percent(interval=1.))
            ram = int(process.get_memory_percent())
            threads = process.get_num_threads()

            if options.verbose:
                message = ("CPU: {0[cpu]}%, "
                           "RAM: {0[ram]}%, threads: {0[threads]}")

                self.sample_logger.info(message.format(dict(
                    interv=interval,
                    cpu=cpu,
                    ram=ram,
                    threads=threads)))

        if 0 != retcode:
            fail_with_error("Unable to start video playback "
                            "for unknown reason")


def sample(version):
    """Launches VLC instance, measures, logs, saves and plots
    performance/resource related parameters while playing a movie.

    @param version: VLC version string
    """

    return Sampler(version).run()


def compare(versions):
    pass