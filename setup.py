# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.command.build_py import build_py


from vlcc import __version__


setup(
    name="vlcc",
    version=__version__,
    author="Konstantin Alexandrov",
    author_email="iwuvjhdva@gmail.com",
    description="VLC versions measurement and comparison tool",
    url="http://github.com/iwuvjhdva/vlcc",
    install_requires=[
        'psutil',
    ],
    packages=["vlcc"],
    scripts=(['bin/vlcc-cli', 'bin/vlcc-http']),
    cmdclass=dict(build_py=build_py)
)
