#!/usr/bin/env python
# runTests.py -- Portage Unit Test Functionality
# Copyright 2006-2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import os.path as osp
import sys
import grp
import platform
import pwd
import signal
import tempfile
from distutils.dir_util import copy_tree


def debug_signal(signum, frame):
    import pdb

    pdb.set_trace()


if platform.python_implementation() == "Jython":
    debug_signum = signal.SIGUSR2  # bug #424259
else:
    debug_signum = signal.SIGUSR1

signal.signal(debug_signum, debug_signal)

# Pretend that the current user's uid/gid are the 'portage' uid/gid,
# so things go smoothly regardless of the current user and global
# user/group configuration.
os.environ["PORTAGE_USERNAME"] = pwd.getpwuid(os.getuid()).pw_name
os.environ["PORTAGE_GRPNAME"] = grp.getgrgid(os.getgid()).gr_name

# Insert our parent dir so we can do shiny import "tests"
# This line courtesy of Marienz and Pkgcore ;)
repoman_pym = osp.dirname(osp.dirname(osp.dirname(osp.realpath(__file__))))
sys.path.insert(0, repoman_pym)

# Add in the parent portage python modules
portage_pym = osp.dirname(osp.dirname(repoman_pym)) + "/lib"
sys.path.insert(0, portage_pym)

# import our centrally initialized portage instance
from repoman._portage import portage

portage._internal_caller = True
import repoman.tests as tests

# Ensure that we don't instantiate portage.settings, so that tests should
# work the same regardless of global configuration file state/existence.
portage._disable_legacy_globals()
from portage.util._eventloop.global_event_loop import global_event_loop
from portage.const import PORTAGE_BIN_PATH

if os.environ.get("NOCOLOR") in ("yes", "true"):
    portage.output.nocolor()

path = os.environ.get("PATH", "").split(":")
path = [x for x in path if x]

insert_bin_path = True
try:
    insert_bin_path = not path or not os.path.samefile(path[0], PORTAGE_BIN_PATH)
except OSError:
    pass

if insert_bin_path:
    path.insert(0, PORTAGE_BIN_PATH)
    os.environ["PATH"] = ":".join(path)

# Copy GPG test keys to temporary directory
gpg_path = tempfile.mkdtemp(prefix="gpg_")

copy_tree(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".gnupg"), gpg_path)

os.chmod(gpg_path, 0o700)
os.environ["PORTAGE_GNUPGHOME"] = gpg_path

if __name__ == "__main__":
    try:
        sys.exit(tests.main())
    finally:
        global_event_loop().close()
