# -*- coding: utf-8 -*-

import itertools

import os
import subprocess

import psutil

from .core import options, get_child_logger, fail_with_error
from .jail import Jail
from .db import db


__all__ = ['compare']


class Sampler(object):
    """VLC version measurements class.
    """

    def __init__(self, version, comparison):
        """Initializes the sampler.

        @param version: VLC version string
        @param comparison: comparison ID
        """

        self.sample_logger = get_child_logger(version)
        self.movie_filename = os.path.basename(options.movie)
        self.jail = Jail(version, self.sample_logger)
        self.movie_info = {}

        cursor = db.execute("INSERT INTO comparison_build "
                            "(comparison_id, build_version) "
                            "VALUES(?, ?)",
                            [comparison, version])

        self.comparison_build = cursor.lastrowid

    def link(self):
        """Hardlinks the dummy player and the video into the jail.
        """

        # TODO: copy files to build_dir before making links as hard
        # links cannot cross filesystems

        misc = os.path.join(os.path.dirname(__file__), 'misc/')
        chdir = self.jail.chroot_dir + '/'

        # Hardlinks (src, dest) tuples
        hardlinks = (
            (misc + 'play.py', chdir + 'play.py'),
            (misc + 'vlc.py', chdir + 'vlc.py'),
            (os.path.abspath(options.movie), chdir + self.movie_filename),
        )

        for src, dest in hardlinks:
            if not os.path.exists(dest):
                try:
                    os.link(src, dest)
                except OSError as e:
                    fail_with_error("Unable to create hard link from {0} to "
                                    "{1}, the message was: `{2}`"
                                    .format(src, dest, e.message))

    def play(self):
        """Runs the dummy player.
        """

        self.sample_logger.info("Playing " + options.movie)

        command = ['python', 'play.py', self.movie_filename]
        self.process = self.jail.exec_chroot(command,
                                             async=True, userspec='vlcc:vlcc',
                                             stdout=subprocess.PIPE)

    def run(self):
        """Runner method.

        Launches VLC instance, measures, logs, saves and plots
        performance/resource related parameters while playing a movie.
        """

        self.link()
        self.play()

        process = psutil.Process(self.process.pid)

        counter = itertools.count()

        while self.process.poll() is None:
            interval = next(counter)
            cpu = int(process.get_cpu_percent(interval=1.))
            ram = int(process.get_memory_percent())
            ram_bytes = process.get_memory_info().rss
            threads = process.get_num_threads()

            message = ("CPU: {0[cpu]}%, "
                       "RAM: {0[ram]}%, threads: {0[threads]}")

            params = dict(
                id=self.comparison_build,
                interv=interval,
                cpu=cpu,
                ram=ram,
                ram_b=ram_bytes,
                threads=threads
            )
            self.sample_logger.info(message.format(params))

            db.execute("INSERT INTO sample VALUES "
                       "(:id, :interv, :cpu, :ram, :threads, :ram_b)",
                       params)

        if 0 != self.process.returncode:
            fail_with_error("Unable to start video playback "
                            "for unknown reason")

        return self.movie_info


def compare():
    """Compares given VLC versions.

    @param versions: versions list
    """

    cursor = db.execute("INSERT INTO comparison (movie) VALUES (?)",
                        (options.movie,))

    comparison = cursor.lastrowid

    [Sampler(version, comparison).run()
     for version in options.versions]

    # Write movie info

    # Finalizing comparison
    db.execute("UPDATE comparison SET ready=?", [True])
