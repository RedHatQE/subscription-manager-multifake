#!/usr/bin/env python

import sys
import os
import argparse
import ConfigParser
import subprocess
import glob

WORKDIR = '/var/lib/subscription-manager-multifake'
RHSMCONF = '/etc/rhsm/rhsm.conf'

def _select_system(name):
    sysdir = WORKDIR + '/' + name
    if not os.path.exists(sysdir):
        sys.stderr.write("System %s does not exist!" % name)
        return 1
    c = ConfigParser.ConfigParser()
    c.readfp(open(RHSMCONF))
    c.set('rhsm', 'productCertDir', sysdir + '/product')
    c.set('rhsm', 'entitlementCertDir', sysdir + '/entitlement')
    c.set('rhsm', 'consumerCertDir', sysdir + '/consumer')
    # custom current system path setting
    c.set('rhsm', 'currentMultifakeSystem', sysdir)
    c.write(open(RHSMCONF, 'w'))
    subprocess.check_call(['rm', '-f'] + glob.glob('/var/lib/rhsm/cache/*.json'))
    return 0

def action_currentsystem():
    c = ConfigParser.ConfigParser()
    c.readfp(open(RHSMCONF))
    try:
        currentsys = c.get('rhsm', 'currentMultifakeSystem')
        print "Current multifake system: %s" % currentsys.split('/')[-1:][0]
    except:
        sys.stderr.write("No multifake system chosen!")
        return 1
    return 0

def action_newsystem(name):
    sysdir = WORKDIR + '/' + name
    if os.path.exists(sysdir):
        sys.stderr.write("System %s already exists!" % name)
        return 1
    os.mkdir(sysdir)
    os.mkdir(sysdir + '/product')
    os.mkdir(sysdir + '/entitlement')
    os.mkdir(sysdir + '/consumer')
    return _select_system(name)

def action_choose(name):
    if _select_system(name) == 0:
        return subprocess.check_call(['yum', 'clean', 'all'])

def action_productadd(certfile, sysname=None):
    if sysname is None:
        c = ConfigParser.ConfigParser()
        c.readfp(open(RHSMCONF))
        path = c.get('rhsm', 'productCertDir')
    else:
        path = WORKDIR + '/' + sysname + '/product'
    return subprocess.check_call(['cp', certfile, path])

if __name__ == '__main__':

    ALL_ACTIONS = ['currentsystem', 'newsystem', 'choose', 'productadd']

    argparser = argparse.ArgumentParser(description='Subscripiton manager multifake', epilog='vkuznets@redhat.com')

    argparser.add_argument('--action', required=True,
                           help='Requested action', choices=ALL_ACTIONS)

    [args, ignored_args] = argparser.parse_known_args()

    if args.action in ['newsystem', 'choose']:
        argparser.add_argument('--name', required=True, help='System name')

    if args.action == 'productadd':
        argparser.add_argument('--name', help='System name (defaults to current)')
        argparser.add_argument('--certfile', required=True, help='Product cert file')

    [args, ignored_args] = argparser.parse_known_args()

    retval = 0

    if args.action == 'currentsystem':
        retval = action_currentsystem()
    if args.action == 'newsystem':
        retval = action_newsystem(args.name)
    elif args.action == 'choose':
        retval = action_choose(args.name)
    elif args.action == 'productadd':
        retval = action_productadd(args.certfile, args.name)

    sys.exit(retval)
