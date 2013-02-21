# -*- coding: utf-8 -*-

import os
import subprocess

from .core import logger, fail_with_error
from .config import config


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
            self.img_dir = os.path.join(config['static_dir'], 'img', png)
            self.command("set term pngcairo enhanced size 800, 600")
            self.command('set output "{0}"'.format(png))

        if title is not None:
            self.command('set title "{0}"'.format(title))

        self.command("""
                     set style line first lt 2 lc rgb "black" lw 2
                     set style line second lt 2 lc rgb "orange" lw 2
                     set style line third lt 2 lc rgb "green" lw 2
                     set style line fourth lt 2 lc rgb "darkorchid" lw 2
                     set style line fifth lt 2 lc rgb "dodgerblue" lw 2
                     """)

    def command(self, command):
        """Calls a gnuplot command.

        @param command: command string
        """

        logger.debug("Calling gnuplot command `{0}`".format(command))
        if self.gnuplot_proc.returncode is not None:
            fail_with_error("gnuplot crashed for unknown reason")

        self.gnuplot_proc.stdin.write(command, "\n")

    def set_labels(self, xlabel="t", ylabel="t"):
        self.command('set xlabel "{0}"\n'
                     'set ylabel "{1}"'.format(xlabel, ylabel))

    def set_ranges(self, x_range=None, y_range=None):
        x_range and self.command('set xrange "{0}"'.format(x_range))
        y_range and self.command('set yrange "{0}"'.format(y_range))

    def plot(self, points, style="first", title=None):
        self.command("plot '-' with lines ls {0} title"
                     .format(style, title or ""))

        # Dumping the points data
        self.command("\n".join("{0} {1}".format(*point) for point in points))
        self.gnuplot_proc.flush()

    def __del__(self):
        self.gnuplot_proc.terminate()
