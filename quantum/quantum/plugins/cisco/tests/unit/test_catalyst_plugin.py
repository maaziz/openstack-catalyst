# To test the methods under the Cisco catalyst Plugin
# Needs to expanded upon once cisco_catalyst_plugin is ready
# New methods to be added

import logging
import unittest

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
        creds.Store.initialize()
        db.configure_db({'sql_connection': 'sqlite:///:memory:',
                         'base': models_v2.models_base.BASEV2})

    def create_network(self, context, net):
        """
        Create a network
        """
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

    def tearDownNetwork(self, network):
        """
        Delete a created nework
        """
        self._cisco_catalyst_plugin.delete_network(context, network['id'])

    def _get_tenant_id_for_create(self, context, resource):
        """
        Returns tenant_id or exception
        """
        if context.is_admin and 'tenant_id' in resource:
            tenant_id = resource['tenant_id']
        elif ('tenant_id' in resource and
               resource['tenant_id'] != context.tenant_id):
            reason = _('Cannot create resource for another tenant')
            raise q_exc.AdminRequired(reason=reason)
        else:
            tenant_id = context.tenant_id
        return tenant_id

    def test_create_network(self):
        """
        Create a test network using the catalyst plugin
        """

        LOG.debug("test_create_network - START")

        net = {'name': self.network_name,
               'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, net)
        cdb.add_vlan_binding(self.vlan_name, self.vlan_id,
                             network_created['id'])
        network_plugin = self._cisco_catlyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        self.assertEqual(network_plugin[const.NAME], self.network_name)
        self.assertEqual(network_plugin[const.NET_VLAN_NAME], self.vlan_name)
        self.assertEqual(network_plugin[const.NET_VLAN_ID], self.vlan_id)
        self.tearDownNetwork(network_created)
        LOG.debug("test_create_network - END")

    def test_delete_network(self):
        """
        Create a network on a catalyst switch and then delete it
        """

        LOG.debug("test_delete_network - START")

        net = {'name': self.network_name,
               'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, net)
        cdb.add_vlan_binding(self.vlan_name, self.vlan_id,
                             network_created['id'])
        network_plugin = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        deleted_network_dict = self._cisco_catalyst_plugin.delete_network(
            context, network_created['id'])
        self.assertEqual(deleted_network_dict[const.ID],
                         network_created['id'])
        self.tearDownNetwork(network_created)
        LOG.debug("test_delete_network - END")

    def test_delete_network_DNE(self):
        """
        Tests the deletion of a non existant network
        """

        LOG.debug("test_delete_network_DNE - Start")

        network_DNE = {'id': self.net_id_DNE,
                       'tenant_id': context.tenant_id,
                       'admin_status_up': self.admin_status_up}
        self.assertRaises(exc.NetworkNotFound,
                          self._cisco_catalyst_plugin.delete_network,
                          context,  network_DNE['id'])
        LOG.debug("test_delete_network_DNE - END")

    def test_get_network(self):
        """
        Tests displaying the details of a created Virtual Network
        """

        LOG.debug("test_get_nework - START")

        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, network)
        cdb.add_vlan_bindings(self.vlan_name, self.vlan_id,
                              network_created['id'])
        network_plugin_dict = self._cisco_catalyst_plugin.create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        network_details_dict = self._cisco_catalyst_plugin.get_network(
            context, network_created)
        self.assertEqual(network_details_dict[const.ID], network_created['id'])
        self.assertEqual(network_details_dict[const.NAME], self.network_name)
        self.assertEqual(network_details_dict[const.NET_VLAN_ID], self.vlan_id)
        self.assertEqual(network_details_dict[const.NET_VLAN_NAME],
                         self.vlan_name)
        self.tearDownNetwork(network_created)
        LOG.debug("test_get_network - END")

    def test_get_networks(self):
        """
        Tests displaying the details of all created Virtual networks
        """

        LOG.debug("test_get_networks - START")

        network1 = {'name': self.network_name,
                    'admin_status_up': self.admin_status_up}
        network2 = {'name': self.network_name2,
                    'admin_status_up': self.admin_status_up}
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
        list_net_dict = self._cisco_catalyst_plugin.get_networks(context)
        self.assertTrue(net_temp_list[0] in list_net_dict)
        self.assertTrue(net_temp_list[1] in list_net_dict)
        self.tearDownNetwork(network_created1)
        self.tearDownNetwork(network_created2)
        LOG.debug("test_get_networks - END")

    def test_get_network_DNE(self):
        """
        Tests the displaying of details of a non existant network
        """
        LOG.debug("test_get_network_DNE - START")

        network = {'id': self.net_id_DNE,
                   'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        assertRaises(exc.NetworkNotFound,
                     self._cisco_catalyst_plugin.get_network,
                     context, network['id'])
        LOG.debug("test_get_network_DNE - END")

    def test_update_network(self):
        """
        Tests update of a Virtual Network
        """

        LOG.debug("test_update_network - START")

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
        self.assertEqual(rename_network_dict[const.NAME], 'new_name')
        self.tearDownNetwork(network_created)
        LOG.debug("test_update_network - END")

    def test_update_network_DNE(self):
        """
        Tests update of a Virtual Network which does not exist
        """
        LOG.debug("test_update_network_DNE - START")

        network = {'name': 'net_name'}
        self.assertRaise(exc.NetworkNotFound,
                         self._cisco_catalyst_plugin.update_network,
                         context, net_id_DNE, network)
        LOG.debug("test_update_network_DNE - END")

    def test_get_vlan_id_for_network(self):
        """
        Test retrieval of Vlan id for network
        """

        LOG.debug("test_get_vlan_id_for_network - START")

        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        network_created = self.create_network(context, network)
        cdb.add_vlan_binding(self.vlan_id, self.vlan_name,
                             network_created['id'])
        network_plugin_dict = self._cisco_create_network(
            context, network_created, self.vlan_name, self.vlan_id)
        result_vlan_id = self._get_vlan_id_for_network(
            network_created['tenant_id'], network_created['id'])
        self.assertEqual(result_vlan_id, self.vlan_id)
        self.tearDownNetwork(network_created)
        LOG.debug("test_get_vlan_id_for_network - END")

    def test_create_subnet(self):
        """
        Test creation of a subnet
        """

    def test_delete_subnet(self):
        """
        Test Deletion of an existing subnet
        """

    def test_delete_subnet_DNE(self):
        """
        Test Deletion of a non existant Subnet
        """

    def test_update_subnet(self):
        """
        Test Updating an existant Subnet
        """

    def test_get_subnet(self):
        """
        Tests the displaying of Subnet details
        """

    def test_get_subnets(self):
        """
        Tests the displaing all existing Subnets
        """

    def test_update_subnet_DNE(self):
        """
        Tests updating of a non existant subnet
        """

    def test_get_subnet_DNE(self):
        """
        Tests displaying a non existant Subnet
        """

    def tearDown(self):
        """
        Clear the test environment
        """
        #remove database contents
        db.clear_db()
