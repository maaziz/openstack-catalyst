"""
Cisco Catalyst Driver
Sends config info to the switch through TCP packets
"""
import logging
from socket import socket, AF_INET, SOCK_STREAM

from quantum.plugis.cisco.catalyst import cisco_catalyst_configuration as conf
from quantum.openstack.common import importutils
from quantum.plugins.cisco.db import l2network_db as cdb


LOG = logging.getLogger(__name__)


class CiscoCATALYSTDriver():
    """
    Catalyst Driver main class
    """
    def __init__(self):
        """
        Extract ip and port from config file
        """
        LOG.debug("Extracting device ip and port\n")
        self._catalyst_ip = conf.CATALYST_IP_ADDRESS
        self._catalyst_port = conf.CATALYST_PORT
        LOG.debug("Device ip and port obtained\n")

    def sendpacket(self, payload):
        """
        Sends a TCP packet to the extracted ip and port
        """
        LOG.debug("Sending packet to device\n")
        IP = self._catalyst_ip
        PORT = self._catalyst_port
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((IP,PORT))
        s.send(payload)
        LOG.debug("Config data sent to the device\n")
        data = client.recv(1024)
        LOG.debug("Recieved reply - %s\n" % data)
        s.close()

    def create_vlan(self, vlan_name, vlan_id):
        """
        Creates a vlan on the device
        """
        LOG.debug("Create vlan(DRIVER) called\n")
        self.enable_vlan(vlan_name, vlan_id)
        # here, we just print all the used vlan ids on the LOG 
        vlan_ids = self.build_vlans_cmd()
        LOG.debug("CatalystDriver VLAN IDs: %s" %vlan_ids)

    def delete_vlan(self, vlan_id):
        """
        Removes a vlan from the device
        """
        LOG.debug("delete vlan(DRIVER) called\n")
        self.disable_vlan(vlan_id)

    def enable_vlan(self, vlan_name, vlan_id):
        """
        Enables a vlan on the switch by creating the necessary
        config packet and calling sendpacket
        """
        LOG.debug("Obtaining config packet\n")
        # payload = Corres method defined in snippets
        LOG.debug("Calling sendpacket\n")
        self.sendpacket(payload)

    def disable_vlan(self, vlan_id):
        """
        Disables a vlan on the switch by creating the required
        config packet and calling sendpacket
        """
        LOG.debug("Obtaining config packet\n")
        # payload = Corres method defined in snippets
        LOG.debug("Calling sendpacket\n")
        self.sendpacket(payload)

    def build_vlans_cmd(self):
        """
        Builds a string with all the vlans on the Switch
        """
        assigned_vlan = cdb.get_all_vlanids_used()
        vlans = ''
        for vlanid in assigned_vlan:
            vlans = str(vlanid['vlan_id']) + ',' + vlans
        if vlans = '':
            vlans = 'none'
        return vlans.strip(',')

    def create_subnet(self, subnet):
        """
        Adds a subnet to the given switch
        """
        LOG.debug("Create subnet(DRIVER) called\n")
        self.enable_subnet(subnet)

    def delete_subnet(self, sub_id):
        """
        Removes a subnet from the given device
        """
        LOG.debug("Remove subnet called\n")
        self.disable_subnet(sub_id)

    def enable_subnet(self, subnet):
        """
        Called by create_subnet and does so by creating a packet and
        invoking sendpacket
        """
        LOG.debug("Obtaining config packet\n")
        # payload = Corres method in snippets
        LOG.debug("Calling sendpacket\n")
        self.sendpacket(payload)

    def disable_subnet(self, sub_id):
        """
        Disables a subnet on the switch by creating a corresponding
        config packet and invoking sendpacket
        """
        LOG.debug("Obtaining config packet\n")
        # payload = corres method in snippets
        LOG.debug("Calling sendpacket\n")
        self.sendpacket(payload)
