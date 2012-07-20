# tests for the catalyst plugin
# Defined for the v2 api
# only network and subnet tests are supported

import logging
import unittest
import netaddr

from quantum.plugins.v2 import router as api_router
from quantum.plugins.cisco.catalyst import cisco_catalyst_plugin
from quantum.plugins.cisco.db import l2network_db as cdb
from quantum.plugins.cisco.db import cisco_models_v2 as models_v2
from quantum.common import exceptions as q_exc
from quantum.plugins.cisco.common import cisco_constants as const
from quantum.plugins.cisco.common import cisco_exceptions as exc
from quantum.db import api as db

LOG = logging.getLogger('quantum.test_catalyst')


class TestCatalystPlugin(unittest.TestCase):

    def setUp(object):
        """
        Setup method for network_id, vlan_id etc
        """
        self.network_name = "test_network_cisco1"
        self.network_name2 = "test_network_cisco2"
        context.tenant_id = "test_tenant_cisco1"
        self.admin_state_up = "UP"
        self._cisco_catalyst_plugin = cisco_catalyst_plugin.CatalystPlugin
        self.vlan_id = 257
        self.vlan_id2 = 258
        self.vlan_name = "q-" + self.network_name + "vlan"
        self.vlan_name2 = "q-" + self.network_name2 + "vlan"
        self.net_id_DNE = '0005'
        self.cidr = '10.0.0.0/24'
        self.ip_version = '4'
        self.gateway_ip = '10.0.0.1'
        creds.Store.initialize()
        db.configure_db({'sql_connection': 'sqlite:///:memory:',
                         'base': models_v2.models_base.BASEV2})

    def create_network(self, context, net):
        """
        Create a network
        """
        # similar to the def in db_plugin_base_v2

        LOG.debug("Creating a network\n")
        try:
            tenant_id = self._get_tenant_id_for_create(context, net)
            with context.session.begin():
                network = models_v2.Network(
                                tenant_id=tenant_id, name=net['name'],
                                admin_state_up=net['admin_state_up'],
                                status="ADMIN")
                context.session.add(network)
                LOG.debug("Creates network %s" % network['id'])
            return self._make_net_dict(network)
        except Exception, exc:
            LOG.error("Failed to create network %s " % net['id'])

    def create_subnet(self, context, subnet):
        """
        Create a subnet
        """
        # Similar to the def in db_base_plugin_v2
        LOG.debug("creating a subnet\n")
        net = netaddr.IPNetwork(subnet['cidr'])
        if subnet['gateway_ip'] == api_router.ATTR_NOT_SPECIFIED:
            subnet['gateway_ip'] == str(netaddr.IPAddress(net.first + 1))

        with context.session.begin():
            subnet = models_v2.Subnet(network_id=subnet['network_id'],
                                      ip_version=subnet['ip_version'],
                                      cidr=subnet['cidr'],
                                      gateway_ip=subnet['gateway_ip'])
            context.session.add(subnet)
            pools = self._allocate_pools_for_subnet(context, subnet)
            for pool in pools:
                ip_pool = models_v2.IPAllocationPool(subnet=subnet,
                                                     first_ip=pool['start'],
                                                     last_ip=pool['end'])
                context.session.add(ip_pool)
                ip_range = models_v2.IPAvailabilityRange(
                    ipallocationpool=ip_pool,
                    first_ip=pool['start'],
                    last_ip=pool['end'])
                context.session.add(ip_range)
        return self._make_subnet_dict(subnet)
   
    def _make_net_dict(self, network):
        """
        Return a network Dictionary
        """
        res = {'id': network['id'],
               'name': network['name'],
               'tenant_id': network['tenant_id'],
               'admin_state_up': network['admin_state_up'],
               'status': network['status'],
               'subnets': [subnet['id']
                           for subnet in network['subnets']]}
        return res

    def _make_subnet_dict(self, subnet):
        """
        Return a subnet dictionary
        """
        res = {'id': subnet['id'],
               'network_id': subnet['network_id'],
               'ip_version': subnet['ip_vrsion'],
               'cidr': subnet['cidr'],
               'allocation_pools': [{'start': pool['first_ip'],
                                     'end': pool['last_ip']}
                                     for pool in subnet['allocation_pools']],
               'gateway_ip': subnet['gateway_ip']}
        return res

    def _allocate_pools_for_subnet(self, context, subnet):
        """
        Allocate ip pools to the subnet.
        pools are allocated around the gateway ip 
        """
        pools = []
        gw_ip = int(netaddr.IPAddress(subnet['gateway_ip']))
        net = netaddr.IPNetwork(subnet['cidr'])
        first_ip = net.first + 1
        last_ip = net.last -1
        if gw_ip > first_ip:
            pools.append({'start': str(netaddr.IPAddress(first_ip))
                          'end': str(netaddr.IPAddress(gw_ip - 1))})
        if gw_ip < last_ip:
            pools.append({'start': str(netaddr.IPAddress(gw_ip + 1))
                          'end': str(netaddr.IPAddress(last_ip))})
        return pools

    def tearDownNetwork(self, network):
        """
        Delete a created nework
        """
        self._cisco_catalyst_plugin.delete_network(context, network['id'])

    def tearDownSubnet(self, subnet):
        """
        Delete a created subnet
        """
        self.cisco_catalyst_plugin.delete_subnet(context, subnet['id'])

    def _get_tenant_id_for_create(self, context, resource):
        """
        Returns tenant_id or exception
        """
        # Similar to the definition in db_bas_plugin_v2
        if context.is_admin and 'tenant_id' in resource:
            tenant_id = resource['tenant_id']
        elif ('tenant_id' in resource and
               resource['tenant_id'] != context.tenant_id):
            reason = _('Cannot create resource for another tenant')
            raise q_exc.AdminRequired(reason=reason)
        else:
            tenant_id = context.tenant_id
        return tenant_id

    # The following are tests for methods defined wrt networks

    def test_create_network(self):
        """
        Create a test network using the catalyst plugin
        """

        LOG.debug("test_create_network - START\n")

        net = {'name': self.network_name,
               'admin_status_up': self.admin_status_up}
        # Create the network first by using a locally defined method
        # and calling create_network in the catalyst plugin
        network_created = self.create_network(context, net)
        cdb.add_vlan_binding(self.vlan_name, self.vlan_id,
                             network_created['id'])
        network_plugin = self._cisco_catlyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        # Check if the locally created network id is equal
        # to the id returned by the catalyst plugin
        self.assertEqual(network_plugin[const.NAME], self.network_name)
        self.assertEqual(network_plugin[const.NET_VLAN_NAME], self.vlan_name)
        self.assertEqual(network_plugin[const.NET_VLAN_ID], self.vlan_id)
        # Destroy the created network
        self.tearDownNetwork(network_created)
        LOG.debug("test_create_network - END\n")

    def test_delete_network(self):
        """
        Create a network on a catalyst switch and then delete it
        """

        LOG.debug("test_delete_network - START\n")
        # network dict for create
        net = {'name': self.network_name,
               'admin_status_up': self.admin_status_up}
        # create a network using a locally defined method
        # and call create_network in the catalyst plugin
        network_created = self.create_network(context, net)
        cdb.add_vlan_binding(self.vlan_name, self.vlan_id,
                             network_created['id'])
        network_plugin = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        # delete the created network by calling delete_network defined at the cat plugin
        # returns a dictionary
        deleted_network_dict = self._cisco_catalyst_plugin.delete_network(
            context, network_created['id'])
        # Check if network id returned by delete_network and create_network
        # are the same
        self.assertEqual(deleted_network_dict[const.ID],
                         network_created['id'])
        # destroy the created network
        self.tearDownNetwork(network_created)
        LOG.debug("test_delete_network - END\n")

    def test_delete_network_DNE(self):
        """
        Tests the deletion of a non existant network
        """

        LOG.debug("test_delete_network_DNE - Start\n")
        # Create a dictionary with a fake network id(non existant)
        network_DNE = {'id': self.net_id_DNE,
                       'tenant_id': context.tenant_id,
                       'admin_status_up': self.admin_status_up}
        # Check if the appr exeception is raised
        # when delete_network is called
        self.assertRaises(exc.NetworkNotFound,
                          self._cisco_catalyst_plugin.delete_network,
                          context,  network_DNE['id'])
        LOG.debug("test_delete_network_DNE - END\n")

    def test_get_network(self):
        """
        Tests displaying the details of a created Virtual Network
        """

        LOG.debug("test_get_nework - START\n")

        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        # first create a network
        network_created = self.create_network(context, network)
        cdb.add_vlan_bindings(self.vlan_name, self.vlan_id,
                              network_created['id'])
        network_plugin_dict = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        # invoke catalyst plugin to obtain the networks details
        network_details_dict = self._cisco_catalyst_plugin.get_network(
            context, network_created)
        # check if returned networks details match with the details
        # of the network that was created
        self.assertEqual(network_details_dict[const.ID], network_created['id'])
        self.assertEqual(network_details_dict[const.NAME], self.network_name)
        self.assertEqual(network_details_dict[const.NET_VLAN_ID], self.vlan_id)
        self.assertEqual(network_details_dict[const.NET_VLAN_NAME],
                         self.vlan_name)
        self.tearDownNetwork(network_created)
        LOG.debug("test_get_network - END\n")

    def test_get_networks(self):
        """
        Tests displaying the details of all created Virtual networks
        """

        LOG.debug("test_get_networks - START\n")

        network1 = {'name': self.network_name,
                    'admin_status_up': self.admin_status_up}
        network2 = {'name': self.network_name2,
                    'admin_status_up': self.admin_status_up}
        # Create two networks first
        network_created1 = self.create_network(context, network1)
        cdb.add_vlan_bindings(self.vlan_name, self.vlan_id,
                              network_created['id'])
        network_plugin_dict_1 = self._cisco_catalyst_plugin.create_network(
            context, network_created1, self.vlan_name, self.vlan_id)
        network_created2 = self.create_network(contex, network2)
        cdb.add_vlan_bindings(self.vlan_id2, self.vlan_name2,
                              network_created2['id'])
        network_plugin_dict_2 = self._cisco_catalyst_plugin.create_network(
            context, network_created2, self.vlan_name2, self.vlan_id2)
        net_temp_list = [network_plugin_dict_1, network_plugin_dict_2]
        # invoke get_networks method in catalyst plugin
        list_net_dict = self._cisco_catalyst_plugin.get_networks(context)
        # Check if details of returned network matches with that of the created network
        self.assertTrue(net_temp_list[0] in list_net_dict)
        self.assertTrue(net_temp_list[1] in list_net_dict)
        # Destroy the created network
        self.tearDownNetwork(network_created1)
        self.tearDownNetwork(network_created2)
        LOG.debug("test_get_networks - END\n")

    def test_get_network_DNE(self):
        """
        Tests the displaying of details of a non existant network
        """
        LOG.debug("test_get_network_DNE - START\n")
        # First create a fake network dict
        network = {'id': self.net_id_DNE,
                   'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        # invoke get_network method with the fake dict
        # and check if appropriate exception is raised
        assertRaises(exc.NetworkNotFound,
                     self._cisco_catalyst_plugin.get_network,
                     context, network['id'])
        LOG.debug("test_get_network_DNE - END\n")

    def test_update_network(self):
        """
        Tests update of a Virtual Network
        """

        LOG.debug("test_update_network - START\n")
        # create a new network on the switch 
        # and then update the name of the network
        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name,
                             network_created['id'])
        network_plugin_dict = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        rename_network = {'name': 'new_name'}
        rename_network_dict = self._cisco_catalyst_plugin.update_network(
            context, network_created['id'], rename_network_dict)
        # check if the updated name is same as the update name sent 
        # to the plugin
        self.assertEqual(rename_network_dict[const.NAME], 'new_name')
        self.tearDownNetwork(network_created)
        LOG.debug("test_update_network - END\n")

    def test_update_network_DNE(self):
        """
        Tests update of a Virtual Network which does not exist
        """
        LOG.debug("test_update_network_DNE - START\n")
        # create a fake network dict
        network = {'name': 'net_name'}
        # Check if the appr exception is called
        # when update_network is called for the same 
        self.assertRaise(exc.NetworkNotFound,
                         self._cisco_catalyst_plugin.update_network,
                         context, net_id_DNE, network)
        LOG.debug("test_update_network_DNE - END\n")

    def test_get_vlan_id_for_network(self):
        """
        Test retrieval of Vlan id for network
        """

        LOG.debug("test_get_vlan_id_for_network - START\n")
        # Create a network   
        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name,
                             network_created['id'])
        network_plugin_dict = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        # Obtain vlan id for the created network
        result_vlan_id = self._cisco_catalyst_plugin.
                        _get_vlan_id_for_network(
            network_created['tenant_id'], network_created['id'])
        # check if vlan id returned is the vlan id assigned to the net
        self.assertEqual(result_vlan_id, self.vlan_id)
        self.tearDownNetwork(network_created)
        LOG.debug("test_get_vlan_id_for_network - END\n")

    # Following are tests for subnet methods

    def test_create_subnet(self):
        """
        Test creation of a subnet
        """
        LOG.debug("test_create_subnet - START\n")
        # first create a network
        net = {'name': self.network_name,
               'admin_state_up': self.admin_state_up}
        network_created = self.create_network(context, net)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name,
                             network_created['id'])
        network_plugin_dict = self._cisco_catayst_plugin.create_network(
                context, network_created, self.vlan_name, self.vlan_id)
        # Do a sanity check wrt network id
        self.assertEqual(network_created['id'],
                         network_plugin_dict['id'])
        # Then create a subnet on the network
        subnet = {'network_id': network_created['id'],
                  'ip_version': self.ip_version,
                  'cidr': self.cidr,
                  'gateway_ip': self.gateway_ip}
        subnet_created = self.create_subnet(context, subnet)
        subnet_plugin_dict = self._cisco_catalyst_plugin.create_subnet(
            context, subnet)
        # Check if subnet created using the local create_subnet method 
        # Is the same as that returned by the device method 
        # create_subnet
        self.assertEqual(network_created['id'],
                         network_plugin_dict['id'])
        self.assertEqual(network_created['id'],
                         subnet_created['network_id'])
        self.assertEqual(subnet_created['network_id'],
                         subnet_plugin_dict['network_id'])
        self.assertEqual(subnet_created['cidr'],
                         subnet_plugin_dict['cidr'])
        self.assertEqual(subnet_created['gateway_ip'],
                         subnet_plugin_dict['gateway_ip'])
        self.assertEqual(subnet_created['id'],
                         subnet_plugin_dict['id'])
        # First destroy the subnet and then destroy 
        # the network
        self.tearDownSubnet(context, subnet_created['id'])
        self.tearDownNetwork(context, network_created['id'])
        LOG.debug("test_create_subnet - END\n")

    def test_delete_subnet(self):
        """
        Test Deletion of an existing subnet
        """
        LOG.debug("test_delete_network - START\n")
        # First create a network
        network = {'name': self.nework_name,
                   'admin_state_up': self.admin_state_up}
        net_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name, net_created['id'])
        net_plugin_dict = self._cisco_catalyst_plugin.create_network(
                context, net_created, self.vlan_name, self.vlan_id)
        # perform a sanity check wrt network id
        self.assertEqual(net_created['id'],
                         net_plugin_dict['id'])
        # Then create a subnet on the network
        subnet = {'network_id': net_created['id'],
                  'ip_version': self.ipversion,
                  'cidr': self.cidr,
                  'gateway_ip': self.gateway_ip}
        subnet_created = self.create_subnet(context, subnet)
        subnet_plugin_dict = self._cisco_catalyst_plugin.create_subnet(
                context, subnet)
        # Sanity check wrt subnet id
        self.assertEqual(subnet_created['network_id'],
                         subnet_plugin_dict['network_id'])
        # Delete the subnet by calling the delete_subnet method defined 
        # by the device plugin
        sub_del_dict = self._cisco_catalyst_plugin.delete_subnet(
                context, subnet['id'])
        # Check if the deleted subnet id is the same as the
        # created subnet id
        assertEqual(subnet_created['id'], sub_del_dict['id'])
        assertEqual(subnet_created['network_id'],
                    sub_del_dict['network_id'])
        # delete the network
        tearDownNetwork(context, network_created['id'])
        LOG.debug("test_delete_subnet - END")

    def test_delete_subnet_DNE(self):
        """
        Test Deletion of a non existant Subnet
        """
        LOG.debug("test_delete_subnet_DNE - START\n")
        # Create a fake subnet id
        subnet_id = '0005'
        # Invoke delete_subnet on the fake subnet
        # and check if the corres exception is called
        self.assertRaises(q_exc.SubnetNotFound,
                          self._cisco_catalyst_plugin.delete_network,
                          context, subnet_id)
        LOG.debug("test_delete_network_DNE - END")

    def test_update_subnet(self):
        """
        Test Updating an existant Subnet
        """
        LOG.debug("test_update_subnet - START\n")
        # first create a network
        network = {'name': self.network_name,
                   'admin_state_up': self.admin_state_up}
        net_created = self.create_network(context, network)
        cdb.add_vlan_binding(context, self.vlan_id, self.vlan_name,
                             net_created['id'])
        net_plugin_dict = self._cisco_catalyst_plugin.create_network(
                context, net_created, self.vlan_name, self.vlan_id)
        # sanity check on the network id
        self.assertEqual(net_created['id'], net_plugin_dict['id'])
        # Then create the subnet
        subnet = {'network_id': net_created['id'],
                  'ip_version': self.ipversion,
                  'cidr': self.cidr,
                  'gateway_ip': self.gateway_ip}
        subnet_created = self.create_subnet(context, subnet)
        sub_plugin_dict = self._cisco_catalyst_plugin.create_subnet(
                            context, subnet_created)
        # sanity check on the subnet id
        assertEqual(subnet_created['id'],
                    sub_plugin_dict['id'])
        # try to update the ip version from 4 to 6
        sub_new = {'ip_version': '6'}
        sub_update = self._cisco_catalyst_plugin.update_subnet(
                            context, subnte_created['id'], sub_new)
        # Check if the version has been updated
        assertEqual(sub_update['ip_version'],
                    sub_new['ip_version'])
        # First destroy subnet and then destroy the network
        self.tearDownSubnet(context, subnet_created['id'])
        self.tearDownNetwork(context, network_created['id'])

    def test_get_subnet(self):
        """
        Tests the displaying of Subnet details
        """
        LOG.debug("test_get_subnet - START"\n)
        # Create a network
        network = {'name': self.network_name,
                   'admin_state_up': self.admin_state_up}
        network_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.van_name, self.vlan_id,
                             network_created['id'])
        net_plugin_dict = self._cisco_catalys_plugin.create_network(
                context, network_created, self.vlan_name, self.vlan_id)
        # Do a sanity check on the network id
        self.assertEqual(network_created['id'],
                         net_plugin_dict['id'])
        # Create a subnet
        subnet = {'network_id': network_created['id'],
                  'ip_version': self.ipversion,
                  'cidr': self.cidr,
                  'gateway_ip': self.gateway_ip}
        subnet_created = self.create_subnet(context, subnet)
        sub_plugin_dict = self._cisco_catalyst_plugin.create_subnet(
                            context, subnet)
        # Sanity check on the subnet id
        assertEqual(subnet_created['id'], sub_plugin_dict['id'])
        # Get subnet details
        sub_get_dict = _cisco_catalyst_plugin.get_subnet(
                            context, subnet_created['id'])
        # Check if returned details match those of the
        # created subnet
        assertEqual(subnet_created['id'], sub_get_dict['id'])
        assertEqual(subnet_created['network_id'],
                    sub_plugin_dict['network_id'])
        # Destroy network and subnet
        tearDownSubnet(context, subnet_created['id'])
        tearDownNetwork(context, network_created['id'])
        LOG.debug("test_get_subnet - END\n")

    def test_get_subnets(self):
        """
        Tests the displaing all existing Subnets
        """
        LOG.debug("test_get_subnets - START\n")
        # create a network
        network = {'name': self.network_name,
                   'admin_state_up': self.admin_state_up)
        network_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name,
                             network_created['id'])
        net_plugin_dict = self._cisco_catalyst_plugin.create_network(
                            context, network_created, self.vlan_name,
                            self.vlan_id)
        # Sanity check
        self.assertEqual(network_created['id'],
                         net_plugin_dict['id'])
        # Create 2 subnets
        subnet1 = {'id': network_created['id'],
                   'ip_version': self.ipversion,
                   'cidr': self.cidr,
                   'gateway_ip': self.gateway_ip)
        subnet_created1 = self.create_subnet(context, subnet1)
        sub_plugin_dict1 = self._cisco_catalyst_plugin.create_subnet(
                            context, subnet_created1)
        # Subnet1 sanity check
        self.assertEqual(subnet_created1['id'],
                         sub_plugin_dict1['id'])
        subnet2 = {'id': network_created['id'],
                   'ip_version': '4',
                   'cidr': '10.10.0.0/16',
                   'gateway_ip': self.gateway_ip}
        subnet_created2 = self.create_subnet(context, subnet2)
        sub_plugin_dict2 = self._cisco_catalyst_plugin.create_subnet(
                            context, subnet_created2)
        # Subnet2 sanity check
        self.assertEqual(subnet_created2['id'],
                         sub_plugin_dict2['id'])
        sub_temp_list = [sub_plugin_dict1, sub_plugin_dict2]
        # Use get_subnets to get a list of subnets
        subnet_list = _cisco_catayst_plugin.get_subnets(context)
        # Check if these match those of the created subnets
        self.assertTrue(sub_temp_list[0] in subnet_list)
        self.assertTrue(sub_temp_list[1] in subnet_list)
        # Destroy both subnets and the network
        self.tearDownSubnet(context, subnet_created1['id'])
        self.tearDownsubnet(context, subnet_created2['id'])
        self.tearDownNetwork(context, network_created['id'])
        LOG.debug("test_get_subnets - END\n")

    def test_update_subnet_DNE(self):
        """
        Tests updating of a non existant subnet
        """
        LOG.debug("test_update_subnet_DNE - START\n")
        # Create a fake subnet id
        sub_fake_id = '0005'
        subnet = {'cidr': '10.10.0.0/16'}
        # Check if valid exception is raised when 
        # this subnet is updated
        self.assertRaises(q_exc.SubnetNotFound,
                          _cisco_catalyst_plugin.update_subnet,
                          context, sub_fake_id, subnet)
        LOG.debug("test_update_subnet_DNE - END\n")

    def test_get_subnet_DNE(self):
        """
        Tests displaying a non existant Subnet
        """
        LOG.debug("test_get_subnet_DNE - START\n")
        # Create a fake subnet id
        subnet_id = '0005'
        # Check id corres exception is raised when
        # get_subnet is called 
        assertRaises(q_exc.SubnetNotFound,
                     _cisco_catalyst_plugin.get_subnet,
                     context, subnet_id)
        LOG.debug("test_get_subnet_DNE - END\n")
 
    # Following tests for methods defined wrt ports
    # The following methods are not supported by the catalyst switch
    # They have been defined here only for name sake
    # delete if not required

    def test_create_port(self):
        """
        Test the create port api
        NOT SUPPORTED BY THE DEVICE
        """
        LOG.debug("test_create_port - START\n")
        LOG.debug("test_create_port - END\n")

    def test_delete_port(self):
        """
        Test deleting a port.
        NOT SUPPORTED BY THE DEVICE
        """
        LOG.debug("test_delete_port - START\n")
        LOG.debug("test_delete_port - END\n")

    def test_delete_port_DNE(self):
        """
        Tests deleting a port that does not exist
        NOT SUPPORTED BY THE DEVICE
        """
        LOG.debug("test_delete_port_DNE - START\n")
        LOG.debug("test_delete_port_DNE - END\n")

    def test_update_port(self):
        """
        Tests updating a port
        NOT SUPPORTEDBY BY THE DEVICE
        """
        LOG.debug("test_update_port - START\n")
        LOG.debug("test_update_port - END\n")

    def test_update_port_DNE(self):
        """
        Tests update of a non existant port
        """
        LOG.debug("test_update_port_DNE - START\n")
        LOG.debug("test_update_port_DNE - END\n")

    def test_get_port(self):
        """
        Tests obtaining port details
        NOT SUPPORTED BY THE DEVICE
        """
        LOG.debug("test_get_port - START\n")
        LOG.debug("test_get_port - END\n")

    def test_get_port_DNE(self):
        """
        Tests obtainig details of a port which does
        not exist
        NOT SUPPORTED BY DEVICE
        """
        LOG.debug("test_get_port_DNE - START\n")
        LOG.debug("test_get_port_DNE - END\n")

    def test_get_ports(self):
        """
        Tests obtaining all ports created by a tenant
        NOT SUPPORTED BY DEVICE
        """
        LOG.debug("test_get_ports - START\n")
        LOG.debug("test_get_ports - END\n")

    def tearDown(self):
        """
        Clear the test environment
        """
        #remove database contents
        db.clear_db()
