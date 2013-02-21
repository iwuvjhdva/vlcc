# -*- coding: utf-8 -*-

import os
import subprocess

from .core import logger, fail_with_error
from .conf import config


__all__ = ['Plot']


class Plot(object):
    """Simple gnuplot wrapper class.
    """

    def __init__(self, png=None, title=None):
        """Initializes the plot.

        @param png: png output file path
        @param title: plot title
        """

        self.gnuplot_proc = subprocess.Popen(['gnuplot', '--persist'],
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
        if png is not None:
            self.img_path = os.path.join(config['static_dir'], 'img', png)
            self.command("set term pngcairo enhanced size 800, 600")
            self.command('set output "{0}"'.format(self.img_path))

            try:
                os.makedirs(os.path.dirname(self.img_path))
            except OSError:
                pass

        if title is not None:
            self.command('set title "{0}"'.format(title))

        self.command("""
                     set style line 1 lt 2 lc rgb "black" lw 2
                     set style line 2 lt 2 lc rgb "orange" lw 2
                     set style line 3 lt 2 lc rgb "green" lw 2
                     set style line 4 lt 2 lc rgb "#9932CC" lw 2
                     set style line 5 lt 2 lc rgb "#1E90FF" lw 2
                     """)

    def command(self, command, flush=False):
        """Calls a gnuplot command.

        @param command: command string
        """

        logger.debug("Calling gnuplot command `{0}`"
                     .format(" ".join(command.split()))[:100])
        if self.gnuplot_proc.returncode is not None:
            fail_with_error("gnuplot crashed for unknown reason")

        self.gnuplot_proc.stdin.write(command + "\n")

        if flush:
            self.gnuplot_proc.stdin.flush()

    def set_labels(self, xlabel="t", ylabel="t"):
        """Sets X and Y axes labels.

        @param xlabel: X label
        @param ylabel: X label
        """

        self.command('set xlabel "{0}"\n'
                     'set ylabel "{1}"'.format(xlabel, ylabel))

    def set_ranges(self, x_range=None, y_range=None):
        """Sets X and Y axes ranges.

        @param x_range: X range
        @param y_range: X range
        """

        x_range and self.command('set xrange "{0}"'.format(x_range))
        y_range and self.command('set yrange "{0}"'.format(y_range))

    def plot_multiple(self, plots):
        """Plots multiple graphs on the same plot.

        @param plots: list of plot dictionaries, their format is
            identical to plot() method kwargs
        """

        plot_strings = (
            ("""'-' with lines ls {0} title "{1}" """
             .format(plot['style'], plot['title'] or ""))
            for plot in plots)

        command = "plot " + ", ".join(plot_strings)

        self.command(command)

        for plot in plots:
            points = ("{0} {1}".format(*point) for point in plot['points'])
            self.command("\n".join(points))
            self.command('e')
        self.command('', flush=True)

    def plot(self, points, style=1, title=None):
        """Plots a plot.

        @param points: points tuples list
        @param style: style name, from 1 to 5
        @param title: plot title
        """

        return self.plot_multiple([dict(
            points=points,
            style=style,
            title=title,
        )])

    def __del__(self):
        self.command("exit", flush=True)
