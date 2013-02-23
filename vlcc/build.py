# -*- coding: utf-8 -*-

from functools import wraps

import os

from .core import options, get_child_logger, fail_with_error
from .conf import config
from .jail import Jail
from .db import db


__all__ = ['build']


def build_state(state):
    """Updates the build state in case of successful execution of the
    decorated method.

    This actually implements build states failback.
    """

    def _build_state(method):
        @wraps(method)
        def __build_state(builder, *args, **kwargs):
            states = [None,
                      'jail_created',
                      'source_unpacked',
                      'configured',
                      'compiled',
                      'installed']

            assert state in states

            if states.index(state) > states.index(builder.state):
                result = method(builder, *args, **kwargs)

                db.execute("UPDATE build SET state=? WHERE version=?",
                           [state, builder.version])
                return result
            else:
                builder.build_logger.debug("Skipping build state `{0}`"
                                           .format(state))
        return __build_state
    return _build_state


class Builder(object):
    """Builder class to create a chroot jail with debootstrap and building a
    VLC version.

    Call the run() method to start a build.
    """

    def __init__(self, version):
        self.version = version
        self.state = None
        self.build_logger = get_child_logger(version)
        self.chroot_src_dir = os.path.join('/usr/local/src', 'vlc-' + version)

        self.jail = Jail(version, self.build_logger)  # chroot jail object

        # Getting current build version

        cursor = db.query("SELECT state FROM build WHERE version=?", [version])
        res = cursor.fetchone()

        if res is None:
            db.execute("INSERT INTO build (version) VALUES (?)", [version])
        else:
            self.state = res[0]

    def start_download(self):
        """Downloads the sources archive with wget.
        """

        ext = 'xz' if self.version[0] == '2' else 'bz2'
        filename = "vlc-{0}.tar.{1}".format(self.version, ext)

        self.download_url = "/".join((config['download_url'],
                                      self.version, filename))
        self.archive_path = os.path.join(options.build_dir, filename)

        command = ['wget', '-c', '-P', options.build_dir, '-O',
                   self.archive_path, self.download_url]

        self.download_proc = self.jail.exec_command(command, async=True)
        self.build_logger.info("Starting download from " + self.download_url)

    def finish_download(self):
        """Waits for the download to finish.
        """

        if 0 != self.download_proc.wait():
            fail_with_error("Download failed :-(")

    @build_state('jail_created')
    def create_jail(self):
        """Creates a chroot jail.
        """

        self.jail.create()

    @build_state('source_unpacked')
    def unpack(self):
        """Unpacks the downloaded sources archive.
        """

        self.build_logger.info("Unpacking the downloaded archive")

        command = ['tar', '-C',
                   self.jail.get_path('/usr/local/src/'),
                   '-xf', self.archive_path]

        self.jail.exec_command(command)

    @build_state('configured')
    def configure(self):
        """Launches the `configure` script from jail.
        """

        configure_args = config['versions'][self.version].get('configure', '')
        command = './configure --prefix=/usr ' + configure_args

        self.jail.log_chroot(command,
                             cwd=self.chroot_src_dir,
                             log_to='configure.log',
                             log_message="Configuring VLC")

    @build_state('compiled')
    def make(self):
        self.jail.log_chroot('make',
                             cwd=self.chroot_src_dir,
                             log_to='make.log',
                             log_message="Compiling VLC")

    @build_state('installed')
    def install(self):
        self.jail.log_chroot('make install',
                             cwd=self.chroot_src_dir,
                             log_to='install.log',
                             log_message="Installing VLC")

    def run(self):
        """This one makes the whole magic.
        """

        self.start_download()
        self.create_jail()
        self.finish_download()
        self.unpack()
        self.configure()
        self.make()
        self.install()


def build(version):
    """Creates a chroot jail with debootstrap and builds a VLC version.

    @param version: VLC version string
    """

    return Builder(version).run()
