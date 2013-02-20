# -*- coding: utf-8 -*-

import time

import os
import ctypes
import pwd

import vlc

from .core import options, get_child_logger
from .jail import Jail


__all__ = ['sample', 'compare']


class Sampler(object):
    def __init__(self, version):
        pass

    def preload(self, lib_name):
        pass


def sample(version):
    """Launches VLC instance, measures, logs, saves and plots
    performance/resource related parameters while playing a movie.

    @param version: VLC version string
    """

    logger = get_child_logger(version)

    jail = Jail(version, logger)
    jail.exec_chroot(['ldconfig', '-v', "/dev/null | grep -v ^$'\t'"])

    lib_path = os.path.join(jail.chroot_dir, 'usr/lib')
    ctypes.cdll.LoadLibrary(os.path.join(lib_path, 'libvlccore.so'))
    ctypes.cdll.LoadLibrary(os.path.join(lib_path, 'libavutil.so'))
    ctypes.cdll.LoadLibrary(os.path.join(lib_path, 'libavcodec.so'))

    # Monkey-patching the VLC lib with libraries loaded from jail.
    vlc.dll = ctypes.CDLL(os.path.join(lib_path, 'libvlc.so'))
    vlc.plugin_path = os.path.join(lib_path, 'vlc/plugins')

    # Setting effective UID to current user's instead of root
    os.setreuid(0, pwd.getpwnam(os.getlogin()).pw_uid)

    instance = vlc.Instance()

    # Restoring effective UID

    player = instance.media_player_new()

    media = instance.media_new(options.movie)
    player.set_media(media)
    player.play()

    # Waiting for VLC to start playing
    time.sleep(.1)

    while player.is_playing():
        time.sleep(1.)


def compare(versions):
    pass
