#!/usr/bin/env python

import sys
import os
import argparse
import ConfigParser
import subprocess
import glob
import logging
import random
import json
import re
import requests
import csv

WORKDIR = '/var/lib/subscription-manager-multifake'
RHSMCONF = '/etc/rhsm/rhsm.conf'

FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("subscription-manager-multifake")
logger.setLevel(logging.INFO)

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

def action_setfacts(factsfile, sysname=None):
    if sysname is None:
        c = ConfigParser.ConfigParser()
        c.readfp(open(RHSMCONF))
        path = c.get('rhsm', 'currentMultifakeSystem')
    else:
        path = WORKDIR + '/' + sysname
    return subprocess.check_call(['cp', factsfile, path + '/facts.json'])

def _namify(name, row):
    try:
        return name % row
    except TypeError:
        return name

def _register_system(username, password, org=None, sys_name=None, cores=1, sockets=1, memory=2, arch='x86_64', dist_name='RHEL', dist_version='6.4', installed_products=[], is_guest=False, virt_uuid='', auto_attach=False):
    if sys_name is None:
        sys_name = 'Testsys' + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

    facts = {}
    facts['virt.is_guest'] = is_guest
    if is_guest:
        facts['virt.uuid'] = virt_uuid
    facts['cpu.core(s)_per_socket'] = str(cores)
    facts['cpu.cpu_socket(s)'] = str(sockets)
    facts['memory.memtotal'] = str(int(memory) * 1024 * 1024)
    facts['uname.machine'] = arch
    facts['system.certificate_version'] = '3.2'
    facts['distribution.name'], facts['distribution.version'] = (dist_name, dist_version)

    action_newsystem(sys_name)
    path = WORKDIR + '/' + sys_name + '/facts.json'
    json.dump(facts, open(path, 'w'))

    for prod in installed_products:
        action_productadd(prod)

    command = ['subscription-manager', 'register', '--username', username, '--password', password, '--name', sys_name]
    if auto_attach:
        command += ['--auto-attach']
    if org is not None:
        command += ['--org', org]
    try:
        # subscribing
        output = subprocess.check_output(command)
        search = re.search('with ID: (.*)\n', output)
    except:
        logging.info("Got error status from subscription-manager while creating %s" % sys_name)
        # figuring out if system was registered
        output = subprocess.check_output(['subscription-manager', 'identity'])
        search = re.search('identity is: (.*)\n', output)

    assert search is not None
    uid = search.group(1)

    logger.info("Sys %s created with uid %s" % (sys_name, uid))
    return (sys_name, uid)

def action_createsystems(username, password, csv_file, org=None):
    """
    Register a bunch of systems from CSV file

    # CSV: Name,Count,Org Label,Environment Label,Groups,Virtual,Host,OS,Arch,Sockets,RAM,Cores,SLA,Product Files,Subscriptions
    """
    retval = 0

    all_systems = []
    host_systems = {}

    c = ConfigParser.ConfigParser()
    c.readfp(open(RHSMCONF))
    try:
        baseurl = 'https://' + c.get('server', 'hostname')
    except:
        logger.info('Can\'t get server:hostname seting from %s, host/guest allocation won\'t be set' % RHSMCONF)
        baseurl = None

    data = csv.DictReader(open(csv_file))
    for row in data:
        num = 0
        total = int(row['Count'])
        while num < total:
            num += 1
            name = _namify(row['Name'], num)
            cores = row['Cores']
            sockets = row['Sockets']
            memory = row['RAM']
            arch = row['Arch']
            if row['Virtual'] == 'Yes':
                is_guest = True
                virt_uuid = name
            else:
                is_guest = False
                virt_uuid = ''
            if row['OS'].find(' ') != -1:
                dist_name, dist_version = row['OS'].split(' ')
            else:
                dist_name, dist_version = ('RHEL', row['OS'])

            installed_products = []
            if row['Product Files'] and row['Product Files'] != '':
                installed_products = row['Product Files'].split(',')

            (sys_name, sys_uid) = _register_system(username, password, org, name, cores, sockets, memory, arch, dist_name, dist_version, installed_products, is_guest, virt_uuid)

            all_systems.append({'name': sys_name, 'uuid': sys_uid})

            if baseurl is not None:
                if row['Host'] is not None:
                    host_name = _namify(row['Host'], num)
                    if not host_name in host_systems:
                        for sys in all_systems:
                            if sys['name'] == host_name:
                                host_systems[host_name] = [sys['uuid']]
                    if host_name in host_systems:
                        host_systems[host_name].append(name)
                        params = {}
                        params['guestIds'] = host_systems[host_name][1::]
                        url = baseurl + "/subscription/consumers/%s" % host_systems[host_name][0]
                        data = json.dumps(params)
                        logger.debug("Setting host/guest allocation for %s, guests: %s, URL: %s DATA: %s" % (host_name, host_systems[host_name][1::], url, data))
                        req = requests.put(url, data=data, headers={'Content-Type': 'application/json'},
                                           verify=False, auth=(username, password))
                        if req.status_code != 204:
                            logging.error("Failed to set host/guest allocation for %s: %s" % (host_name, req.status_code))

if __name__ == '__main__':

    ALL_ACTIONS = ['currentsystem', 'newsystem', 'choose', 'productadd', 'setfacts', 'createsystems']

    argparser = argparse.ArgumentParser(description='Subscripiton manager multifake', epilog='vkuznets@redhat.com')

    argparser.add_argument('--action', required=True,
                           help='Requested action', choices=ALL_ACTIONS)

    [args, ignored_args] = argparser.parse_known_args()

    if args.action in ['newsystem', 'choose']:
        argparser.add_argument('--name', required=True, help='System name')

    if args.action == 'productadd':
        argparser.add_argument('--name', help='System name (defaults to current)')
        argparser.add_argument('--certfile', required=True, help='Product cert file')

    if args.action == 'setfacts':
        argparser.add_argument('--name', help='System name (defaults to current)')
        argparser.add_argument('--factsfile', required=True, help='JSON with facts')

    if args.action == 'createsystems':
        argparser.add_argument('--username', required=True, help='Username for system registration')
        argparser.add_argument('--password', required=True, help='Password for system registration')
        argparser.add_argument('--csvfile', required=True, help='CSV with systems')
        argparser.add_argument('--org', help='Organization fo system registration')

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
    elif args.action == 'setfacts':
        retval = action_setfacts(args.factsfile, args.name)
    elif args.action == 'createsystems':
        retval = action_createsystems(args.username, args.password, args.csvfile, args.org)

    sys.exit(retval)
