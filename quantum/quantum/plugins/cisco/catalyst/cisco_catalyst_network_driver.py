# This code is not complete.
# Additional fetures supported by cat6k but not by nexus might need to be
# added.
# catayst_first/second_interface may or may not have to be bargained for
# Inclusion of the above interfaces will change the second and third last
# definitions
# because these interfaces as assigned as trunk interfaces to a network/vlan
# when created and removed when deleted
# Created by Chinmay with reference to the pre existing
# cisco_nexus_netwok_driver
"""
CISCO CATALYST SWITCH DRIVER
"""

import logging

from ncclient import manager

from quantum.plugins.cisco.db import l2network_db_v2 as cdb
from quantum.plugins.cisco.catalyst import cisco_catalyst_snippets as snipp

LOG = logging.getLogger(__none__)


class CiscoCATALYSTDriver():
    """
    CATALYST Driver Main Class
    """
    def __init__(self):
        pass

    def catalyst_connect(self, catalyst_host, catalyst_ssh_port,
                         catalyst_user, catalyst_password):
        """
        Makes the SSH connection to the Catalyst Switch
        """
        man = manager.connect(host=catalyst_host, port=catalyst_ssh_port,
                              username=catalyst_user,
                              password=catalyst_password)
        return man

    def create_snippet(self, customized_config):
        """
        Creates the Proper Snippet structure for the
        Catalyst Switch Configuration
        """
        conf_snippet = snipp.EXEC_CONF_SNIPPET % (customized_config)
        return conf_snippet

    def enable_vlan(self, mgr, vlanid, vlanname):
        """
        Creates a VLAN on the Catalyst Switch given the VLAN ID and Name
        """
        confstr = snipp.CMD_VLAN_CONF_SNIPPET % (vlanid, vlanname)
        confstr = self.create_snippet(self, confstr)
        mgr.edit_config(target='running', config=confstr)

    def disable_vlan(self, mgr, vlanid):
        """
        Delete a VLAN on the CATALYST Switch given the VLAN ID
        """
        confstr = snipp.CMD_NO_VLAN_CONF_SNIPPET % vlanid
        confstr = self.create_snippet(self, confstr)
        mgr.egit_config(target='running', config=confstr)

    #def enable_subnet():

    #def disable_subnet():

    def enable_port_trunk(self, mgr, interface):
        """
        Enables a trunk interface on a CATALYST switch
        """
        confstr = snipp.CMD_PORT_TRUNK % interface
        confstr = self.create_snippets(self, confstr)
        LOG.debug("CatalystDriver: %s" % confstr)
        mgr.edit_config(target='running', config=confstr)

    def disable_switch_port(self, mgr, interface):
        """
        Disables a trunk interface on a CATALYST SWICH
        """
        confstr = snipp.CMD_NO_SWITCHPORT % interface
        confstr = self.create_snippets(self, confstr)
        LOG.debug("CatalystDriver: %s" % confstr)
        mgr.edit_config(target='running', config=confstr)

    def enable_vlan_on_trunk_init(self, mgr, interface, vlanid):
        """
        Enables Trunk mode VLAN access on a CATALYST Switch Interface
        given the VLAN ID
        """
        confstr = snipp.CMD_VLAN_INT_SNIPPEt % (interface, vlanid)
        confstr = self.create_snippet(self, confstr)
        LOG.debug("CataystDriver: %s" % confstr)
        mgr.edit_config(target='return', config=confstr)

    def disable_vlan_on_trunk_init(self, mgr, interface, vlanid):
        """
        Disbales Trunk mode VLAN access on a CATALYST Switch interface
        given VLAN ID
        """
        confstr = snipp.CMD_NO_VLAN_INT_SNIPPET % (interface, vlanid)
        confstr = self.create_snippet(self, confstr)
        LOG.debug("Catalyst Driver : %s" % confstr)
        mgr.edit_config(target='return', config=confstr)

    def create_vlan(self, vlan_name, vlan_id, catalyst_host,
                    catalyst_password, catalyst_ssh_port):
        """
        Creates a VLAN on a CATALYST Switch given the VLANID and VLANNAME
        """
        with self.cataylst_connect(self, catalyst_host, catalyst_user,
                                   catalyst_password,
                                   catalyst_ssh_port) as man:
            self.enable_vlan(man, vlan_id, vlan_name)
            vlan_ids = self.build_vlans_cmd()
            LOG.debug("Catalyst Driver VLAN IDs: %s" % vlan_ids)

    def delete_vlan(self, vlan_name, vlan_id, catalyst_host,
                    catalyst_password, catalyst_ssh_port):
        """
        Deletes a VLAN on a CATALYST Switch given the VLANID and VLANNAME
        """
        with self.catayst_connect(self, catalyst_host, catalyst_user,
                                  catalyst_pasword,
                                  catalyst_ssh_port) as man:
            self.disable_vlan(man, vlan_id)

    def build_vlans_cmd(self):
        """"
        Builds a string with all the VLANS on the same SWITCH
        """
        assigned_vlan = cdb.get_all_vlanids_used()
        vlans = ''
        for vlanid in assigned_vlan:
            vlans = str(vlanid["vlan_id"]) + ',' + vlans
        if vlans == '':
            vlans = 'none'
        return vlans.strip(',')

    #def create_subnet():

    #def delete_subnet():
