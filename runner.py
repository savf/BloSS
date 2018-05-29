#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import sys

from ryu.cmd import manager

from bloss.manager import BloSS


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "dc:", ["debug", "controller="])
    except getopt.GetoptError:
        print 'runner.py -c "controller.py" [-c "simple_router.py"] [-d]'
        sys.exit(2)
    sys.argv = [sys.argv[0]]
    sys.argv.append('--ofp-tcp-listen-port')
    sys.argv.append('6633')

    for opt, arg in opts:
        if opt in ("-d", "--debug"):
            sys.argv.append('--enable-debugger')
            sys.argv.append('--verbose')
        if opt in ("-c", "--controller"):
            sys.argv.append(arg)

    BloSS()
    manager.main()


if __name__ == '__main__':
    main(sys.argv[1:])
