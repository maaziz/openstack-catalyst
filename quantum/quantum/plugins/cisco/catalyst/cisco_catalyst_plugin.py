# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2011 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Abhinav Sonker, Cisco Systems, Inc.
# @author: Chinmay Kulkarni, Cisco Systems, Inc.
# @author: Harsh Prasad, Cisco Systems, Inc.
"""
PlugIn for Cisco OS driver
"""
import logging

from quantum.common import exceptions as exc
from quantum.openstack.common import importutils
from quantum.plugins.cisco.common import cisco_constants as const
from quantum.plugins.cisco.common import cisco_credentials as cred
from quantum.plugins.cisco.db import api as db
from quantum.plugins.cisco.db import l2network_db as cdb
from quantum.plugins.cisco.db import catalyst_db as ctst_db
from quantum.plugins.cisco.l2device_plugin_baseV2 import L2DevicePluginBaseV2
from quantum.plugins.cisco.catalyst import cisco_catalyst_configuration as conf
from quantum.db import db_base_plugin_v2 as qdb

LOG = logging.getLogger(__name__)


class CatalystPlugin(L2DevicePluginBaseV2):
    """
    Catalyst Plugin Main Class
    """
    _networks = {}
    _subnets = {}
    _port = 80

    def __init__(self):
        """
        Extracts the configuration parameters from the configuration file
        """
        self._client = importutils.import_object(conf.CATALYST_DRIVER)
        LOG.debug("Loaded driver %s\n" % conf.CATALYST_DRIVER)

    def create_subnet(self, context, subnet):
        """
        Create a subnet, which represents a range of IP addresses
        that can be allocated to devices
        """
        LOG.debug("CatalystPlugin:create_subnet() called\n")
        self._client.create_subnet(subnet)
        new_sub_dict = {'id': subnet['id'],
                        'network_id': subnet['network_id'],
                        'ip_version': subnet['ip_version'],
                        'cidr': subnet['cidr'],
                        'allocation_pools;': [{'start': pool['first_ip'],
                                               'end': pool['last_ip'],
                                                for pool in
                                                subnet['allocation_pools']}],
                        'gateway_ip': subnet['gateway_ip']}
        self._subnets[subnet['id']] = new_sub_dict
        return new_sub_dict

    def update_subnet(self, context, id, subnet):
        """
        Updates the subnet given by id with details given in subnet
        """
        sub_existing = qdb._get_subnet(context, id)
        if subnet['ip_version']:
            sub_existing['ip_version'] = subnet['ip_version']
        if subnet['cidr']:
            sub_existing['cidr'] = subnet['cidr']
        if subnet['gateway_ip']:
            sub_existing['gateway_ip'] = subnet['gateway_ip']
        # Allocation pool update needs to be added
        return sub_existing

    def get_subnet(self, context, id, fields=None, verbose=None):
        """
        Returns a subnet dictionary containing corres subnet info
        """
        subnet = qdb._get_subnet(context, id)
        vlan = cdb.get_vlan_binding(subnet['network_id'])
        subnet['vlan_id'] = vlan
        return subnet

    def delete_subnet(self, context, id):
        """
        deletes a subnet from the switch
        """
        LOG.debug("CatalystPlugin:delete_network() called\n")
        sub = qdb._get_subnet(context, id)
        self._client.delete_subnet(id)
        return sub

    def get_subnets(self, context, filters=None, fields=None, verbose=None):
        """
        Return all the subnets owned by the user
        """
        LOG.debug("Cisco get_subnets() called\n")
        return self._subnets.values()

    def create_network(self, context, network, vlan_name, vlan_id,):
        """
        Create a VLAN in the switch, and configure the appropriate interfaces
        for this VLAN
        """
        LOG.debug("CatalystPlugin:create_network() acalled\n")
        self._client.create_vlan(vlan_name, str(vlan_id))
        ctst_db.add_catalystport_binding(self._port, str(vlan_id))
        new_net_dict = {const.ID: network['id'],
                        const.NAME: network['name'],
                        const.TENANT_ID: network['tenant_id'],
                        const.ADMIN_STATE_UP: network['admin_state_up'],
                        const.STATUS: network['status']
                        const.SUBNETS: [subnet['id']
                           for subnet in network['subnets']]}
        self._networks[network['id']] = new_net_dict
        return new_net_dict

    def delete_network(self, tenant_id, id):
        """
        Deletes a VLAN in the switch, and removes the VLAN configuration
        from the relevant interfaces
        """
        LOG.debug("CatalystPlugin:delete_network() called\n")
        vlan_id = self._get_vlan_id_for_network(tenant_id, id)
        ports_id = ctst_db.get_catalystport_binding(vlan_id)
        LOG.debug("CatalystPlugin:Interfaces to be disassociated: %s"
                  % ports_id)
        ctst_db.remove_catalystport_binding(vlan_id)
        # (harspras) Add exception for Network not found
        net = qdb._get_network(context, id)
        self._client.delete_vlan(str(vlan_id))
        return net

    def get_network(self, context, id, fields=None, verbose=None):
        """
        might be a change in last two statements
        """
        # (harspras) Just return from _networks dict
        network =  qdb._get_network(context, id)
        vlan = cdb.get_vlan_binding(id)
        return {const.ID: id, const.NAME: network.name,
                const.NET_PORTS: network.ports,
                const.NET_VLAN_NAME: vlan.vlan_name,
                const.NET_VLAN_ID: vlan.vlan_id}

    def get_networks(self, context, filters=None, fields=None, verbose=None):
        """
        returing the dictionary
        """
        LOG.debug("CatalystPlugin:get_all_networks() called\n")
        return self._networks.values()

    def update_network(self, context, id, network):
        """
        Updates the properties of a particular
        Virtual Network.
        """
        LOG.debug("CatalystPlugin:update_network() called\n")
        network = qdb._get_network(context, id)
        # (harspras) what is n??
        network.update(n)
        return qdb._make_network_dict(network)

    def create_port(self, context, port):
        """
        This is probably not applicable to the Catalyst plugin.
        Delete if not required
        """
        LOG.debug("CatalystPlugin:create_port() called\n")

    def delete_port(self, context, id):
        """
        This is probably not applicable to the Catalyst plugin.
        Delete if not required.
        """
        LOG.debug("CatalystPlugin:delete_port() called\n")

    def update_port(self, context, id, port):
        """
        This is probably not applicable to the Catalyst plugin.
        Delete if not required.
        """
        LOG.debug("CatalystPlugin:update_port() called\n")

    def get_port(self, context, id, fields=None, verbose=None):
        """
        This is probably not applicable to Catalyst Plugin.
        Delete if not required.
        """
        LOG.debug("CiscoPlugin:get_port() called\n")


    def get_ports(self, context, filters=None, fields=None, verbose=None):
        """
        This is probably not applicable to the Catalyst plugin.
        Delete if not required.
        """
        LOG.debug("CiscoPlugin:get_ports() called\n")
