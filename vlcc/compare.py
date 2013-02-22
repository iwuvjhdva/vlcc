# -*- coding: utf-8 -*-

import collections
import itertools

import os
import subprocess

import psutil

from .core import options, get_child_logger, fail_with_error
from .jail import Jail
from .db import db, dict_factory

from .plot import Plot


__all__ = ['compare']


class Sampler(object):
    """VLC version measurements class.
    """

    def __init__(self, version, comparison):
        """Initializes the sampler.

        @param version: VLC version string
        @param comparison: comparison ID
        """

        self.version = version
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

        interval_counter = itertools.count()
        avg_counter = collections.Counter()

        while self.process.poll() is None:
            interval = next(interval_counter)
            cpu = process.get_cpu_percent(interval=1.)
            ram = process.get_memory_percent()
            ram_bytes = process.get_memory_info().rss
            threads = process.get_num_threads()

            params = dict(
                cpu=cpu,
                ram=ram,
                ram_b=ram_bytes,
                threads=threads
            )
            avg_counter.update(params)

            message = ("Interval: {0[interv]}, CPU: {0[cpu]:.2f}%, "
                       "RAM: {0[ram]:.2f}%, RAM: {0[ram_b]} bytes, "
                       "threads: {0[threads]}")

            params.update(dict(
                id=self.comparison_build,
                interv=interval,
            ))
            self.sample_logger.info(message.format(params))

            db.execute("INSERT INTO sample VALUES "
                       "(:id, :interv, :cpu, :ram, :threads, :ram_b)",
                       params, commit=False)

        db.commit()
        if 0 != self.process.returncode:
            fail_with_error("Unable to start video playback "
                            "for unknown reason")

        # Updating comparison build overview with average values
        intervals_num = next(interval_counter)

        if intervals_num:
            for key, value in avg_counter.iteritems():
                avg_counter[key] = ("{0:.2f}"
                                    .format(value / float(intervals_num)))

            avg_counter['id'] = self.comparison_build
            db.execute("INSERT INTO overview VALUES "
                       "(:id, :cpu, :ram, :threads, :ram_b)",
                       avg_counter)

        return self


def compare():
    """Compares given VLC versions.

    @param versions: versions list
    """

    cursor = db.execute("INSERT INTO comparison (movie, ready) VALUES (?, ?)",
                        (os.path.basename(options.movie), False))

    comparison = cursor.lastrowid

    samplers = [Sampler(version, comparison).run()
                for version in options.versions]

    # Write movie info
    # ...

    db.row_factory(dict_factory)

    # Plotting comparison results

    plots = [
        dict(
            name='cpu',
            title="CPU comparison",
            ylabel="CPU load, %",
        ),
        dict(
            name='ram',
            title="RAM comparison",
            ylabel="RAM load, %",
        ),
        dict(
            name='threads',
            title="Threads count comparison",
            ylabel="Threads count",
        ),
    ]

    for plot_data in plots:
        png_path = '{0}/{1}.png'.format(comparison, plot_data['name'])
        plot = Plot(png=png_path, title=plot_data['title'])

        plot.set_labels("Time, s", plot_data['ylabel'])

        # Draw a plot for each specific VLC version

        style_counter = itertools.count(1)

        graph_list = []

        for sampler in samplers:
            cursor = db.query("SELECT s.interval, s.cpu, s.ram, s.threads "
                              "FROM sample s, comparison_build cb, "
                              "     comparison c "
                              "WHERE s.comparison_build_id=cb.id "
                              "AND cb.comparison_id=c.id "
                              "AND c.id=? "
                              "AND cb.build_version=?",
                              [comparison, sampler.version])

            points = (
                (row['interval'], row[plot_data['name']])
                for row in cursor
            )

            graph_list.append(dict(
                title="VLC {0}".format(sampler.version),
                style=next(style_counter),
                points=points,
            ))

        plot.plot_multiple(graph_list)
        del plot

    db.row_factory()

    # Finalizing comparison
    db.execute("UPDATE comparison SET ready=? WHERE id=?", [True, comparison])
