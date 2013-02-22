vlcc
====

VLC versions measurement and comparison tool

Foreword
--------
Frankly, the tool was only tested on Debian Wheezy and Kubuntu 12.10 distributions.

You should expect issues in case of use of another systems, but it will probably work well on all modern Debian-based distros.

Well, you also should run VLCC with Python 2.7.

There are no valid reasons why it couldn't be implemented to run with 2.6 or 3.x, but it actually works on 2.7.


Installation
------------
Run

```bash
$ sudo python setup.py install
```

This will install VLCC and its additional requirements.

Note that you should have setuptools package installed in order to install all the dependencies.

If you don't have setuptools, you'll need psutil, flask, PyYAML and pysqlite to install.

Well, for now your system was enriched with the vlcc lib and two binaries:
*   _vlcc-run_ does all the building and comparison job
*   _vlcc-http_ is a simple HTTP server which hosts the VLCC Web page

Configuration
-------------
In order to run, debootstrap, gnuplot and wget packages are required by VLCC runner script (i. e. _vlcc-run_).

The script will warn you If any of these packages are absent.

Configuration file (usually config.yaml) can be specified with _-c_ or _--config_ option to both _vlcc-run_ and _vlcc-http_ scripts.

If you don't have one, both scripts will try to create its basic reincarnation on first run in current directory.

Configuration with config.yaml is quite simple and intuitive, if you want to change paths or add new VLC version, just follow the example configuration in the default config file.

Note that, using the default config, the database file and images folder will be created in current directory.

Also note that both _vlcc-http_ and _vlcc-run_ should use the same config (nevermind, just run them both in one directory).

Usage
-----

Note that root privileges are required to run _vlcc-run_ since debootstrap & chroot do need them.

I've actually spent some time on playing with fakeroot/fakechroot stuff but it eventually doesn't work properly, so run with sudo.

The very basic launch of _vlcc-run_ script follows:
```bash
$ sudo vlcc-run <video_file_path> 1.1.3 2.0.3
```

Where 1.1.3 and 2.0.3 are sample VLC versions available in the default config file.

This will create ./build/ dir in current directory and will start to make chroot jails, configuring, compiling, installing and comparing.

For _vlcc-http_ just do
```bash
$ vlcc-http
```
And visit http://127.0.0.1:5000 in your favourite browser (in fact, you better run it with Chrome or Firefox :-) ).

For advanced usage information, run the scripts with _--help_ option.

### Failback

Note that VLCC has failback functionality, so you don't have to repeat all the previous build states on each run.

The available build states which describe the atomicity of the failback functionality are: _jail_created_, _source_unpacked_, _configured_, _compiled_, _installed_.


So it goes. Feel free to ask any questions.
