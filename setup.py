# -*- coding: utf-8 -*-

try:
    from setuptools import setup
    using_setuptools = True
except ImportError:
    from distutils.core import setup
    using_setuptools = False

from distutils.command.build_py import build_py


setup(
    name="vlcc",
    version='0.02',
    author="Konstantin Alexandrov",
    author_email="iwuvjhdva@gmail.com",
    description="VLC versions measurement and comparison tool",
    url="http://github.com/iwuvjhdva/vlcc",
    install_requires=[
        'psutil',
        'flask',
        'PyYAML',
        'pysqlite',
    ],
    packages=['vlcc', 'vlcc.http'],
    package_data={
        'vlcc': ['misc/*.*'],
        'vlcc.http': ['static/css/*.*', 'templates/*.*'],
    },
    entry_points={
        'console_scripts': [
            'vlcc-run = vlcc.main:main',
            'vlcc-http = vlcc.http.main:main',
        ],
    },
    scripts=([] if using_setuptools else ['bin/vlcc-run', 'bin/vlcc-http']),
    cmdclass=dict(build_py=build_py)
)
