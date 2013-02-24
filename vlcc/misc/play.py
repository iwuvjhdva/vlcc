# -*- coding: utf-8 -*-
#
# Dummy video player
#

from __future__ import print_function

import time

import os
import sys

from ctypes import cdll

import vlc


if __name__ == "__main__":
    instance = vlc.Instance('--vout=x11')

    player = instance.media_player_new()

    media = instance.media_new(sys.argv[1])
    player.set_media(media)
    player.play()

    # Print media parameters
    print()

    # Waiting for VLC to start playing
    time.sleep(1.)

    if not player.is_playing():
        exit(-1)

    # Tracing for memory leaks

    malloc_trace = "/home/vlcc/mtrace"

    os.environ.update({
        'LANG': 'C',
        'MALLOC_TRACE': malloc_trace,
    })

    libc = cdll.LoadLibrary("libc.so.6")
    event_manager = player.event_manager()

    def end_callback(event):
        global instance

        instance.release()

        libc.muntrace()

        # Parcing the trace
        os.system('mtrace ' + malloc_trace + ' > ' + malloc_trace + '.txt')

        sys.exit()

    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached,
                               end_callback)

    libc.mtrace()

    while True:
        time.sleep(.1)
