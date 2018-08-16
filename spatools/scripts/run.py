
import sys, os
import argparse
import importlib
from spatools.lib.utils import cerr
import spatools.scripts.dbmgr


def greet():
    cerr('spatools - Python-based SNP processing tools')


def usage():
    cerr('Usage:')
    cerr('\t%s command [options]' % sys.argv[0])
    sys.exit(0)


def main():

    greet()

    command = sys.argv[1]
    opt_args = sys.argv[2:]

    cerr('Running command: %s' % command)

    try:
        M = importlib.import_module('spatools.scripts.' + command)
    except ImportError:
        cerr('Cannot import script name: %s' % command)
        sys.exit(101)

    parser = M.init_argparser()
    args = parser.parse_args(opt_args)
    M.main( args )
