# -*- coding: utf-8 -*-
#
# Dummy video player
#

from __future__ import print_function

import time
import sys

import vlc


if __name__ == "__main__":
    instance = vlc.Instance()

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

    while player.is_playing():
        time.sleep(1.)
