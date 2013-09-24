Use subscription-manager to register multiple (fake) systems
============================================================

Overview
--------
This tool allows registering multiple systems with mocked facts (including socket count, host/guest allocation, ...) and arbitary product set using same subscription-manager. It is possible to switch between theese systems to e.g. check content access with different subscriptions.

Usage example
-------------
    # Create new 'fake' system
    $ subscription-manager-multifake --action newsystem --name system0001

    # Setting 'fake' facts for system
    $cat > fakefacts.json << EOF
    > {"distribution.name": "Red Hat Enterprise Linux Server", "memory.memtotal": "1695216", "distribution.version": "6.4", "lscpu.architecture": "x86_64", "lscpu.socket(s)": "4", "uname.machine": "x86_64","system.certificate_version": "3.2"}
    > EOF
    $ subscription-manager-multifake --action setfacts --factsfile fakefacts.json
    # facts can be checked with 'subscription-manager facts'

    # Adding 'product'
    $ subscription-manager-multifake --action productadd --certfile /usr/share/rhsm/product/RHEL-6/Server-Server-x86_64-23d36f276d57-69.pem

    It's possible to register and subscribe this system now with 'subscription-manager register' and 'subscription-manager subscribe', check content access, ...

    # Switching between 'fake' systems
    # Figuring out current 'fake' system:
    $ subscription-manager-multifake --action currentsystem
      Current multifake system: testsys1

    # Choosing 'fake' system:
    $ subscription-manager-multifake --action choose --name testsys2

    # Registering bunch of 'fake' systems based on csv file (there is an example in examples/). Current settings in /etc/rhsm/rhsm.conf are used.
    $ python subscription-manager-multifake.py --action createsystems --username testuser --password testpassword --csvfile test-syscreate.csv
    ...

Contact
-------
vkuznets at redhat.com
