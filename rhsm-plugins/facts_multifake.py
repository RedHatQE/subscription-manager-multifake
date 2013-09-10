from subscription_manager.base_plugin import SubManPlugin
requires_api_version = "1.0"

import subprocess
import ConfigParser
import simplejson as json


class FactsPlugin(SubManPlugin):
    """Plugin for providing fake facts"""
    name = "facts"

    def post_facts_collection_hook(self, conduit):
        """'post_facts_collection' hook to add facter facts

        Args:
            conduit: A FactsConduit()
        """
        conduit.log.info("post_facts_collection called")
        facts = conduit.facts

        cp = ConfigParser.ConfigParser()
        cp.readfp(open('/etc/rhsm/rhsm.conf'))
        try:
            sysdir = cp.get('rhsm', 'currentMultifakeSystem')
            newfacts = json.load(open(sysdir + '/facts.json'))
            conduit.facts.clear()
            conduit.facts.update(newfacts)
        except:
            pass
