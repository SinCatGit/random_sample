# -*- coding: utf-8 -*-
from __future__ import unicode_literals
__author__ = 'sincat'

STORE_OPTIONS = {
    'host': 'localhost',
    'port': 6379,
    'password': '',
    'db': 3
}

# import local conf
try:
    from local_conf import *
except ImportError:
    import sys
    import traceback
    sys.stderr.write(
        """Warning: Can't find the file 'local_conf.py' in the directory containing %r.
        It appears you've customized things.\n(If the file settings.py does indeed exist, it's causing
        an ImportError somehow.)\n""" % __file__)
    sys.stderr.write("\nFor debugging purposes, the exception was:\n\n")
    traceback.print_exc()
