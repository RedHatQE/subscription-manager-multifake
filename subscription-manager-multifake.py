#!/usr/bin/env python

import sys
import os

if __name__ == '__main__':

    ALL_ACTIONS = ['newsystem', 'choose']

    argparser = argparse.ArgumentParser(description='Subscripiton manager multifake', epilog='vkuznets@redhat.com')

    argparser.add_argument('--action', required=True,
                           help='Requested action', choices=ALL_ACTIONS)

    [args, ignored_args] = argparser.parse_known_args()

    if args.action == 'newsystem' or args.action == 'choose':
        argparser.add_argument('--name', required=True, help='System name')

    [args, ignored_args] = argparser.parse_known_args()
