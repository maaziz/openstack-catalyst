# A test for all L2Networkplugin API's

import logging
import unittest

from quantum.plugins.cisco import l2network_plugin_v2

LOG = logging.getLogger('quantum.tests.test_core_api_func')


class CoreAPITESTFuncV2(unittest.TestCase):

    def setUp(object):
        self.network_name = 'test_cisco_network1'
        context.tenant_id = 'test_cisco_tenant1'
        self.admin_status_up = 'UP'
        self._l2network_plugin = l2network_plugin_v2.L2NetworkPluginV2
        self.new_net_name = 'new_cisco_network'

    def tearDownNetwork(context, net):
        """
        Tears down an existing network
        """
        self._l2network_plugin.delete_network(context, net['id'])

    def test_create_network(self):
        """
        Test Creation of a new Virtual NEtwork
        """

        LOG.debug("test_create_network - START")
        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        new_net_dict = self._l2network_plugin.create_network(context, network)
        net = _l2network_plugin._get_network(context, new_net_dict['id'])
        self.assertEqual(net['name'], new_net_dict['name'])
        self.assertEqual(net['id'], new_net_dict['id'])
        self.tearDownNetwork(new_net_dict)
        LOG.debug("test_create_network - END")

    def test_delete_network(self):
        """
        Test delete a network
        """

        LOG.debug("test_delete_network - START")
        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        new_net_dict = self._l2network_plugin.create_network(context, network)
        delete_dict = self._l2network_plugin.delete_network(context,
                        new_net_dict['id'])
        self.assertEqual(new_net_dict['id'], delete_dict['id'])
        self.tearDownNetwork(new_net_dict)
        LOG.debug("test_delete_network - END")

    def test_delete_network_DNE(self):
        """
        Tests deleting a non existant network
        """

        LOG.debug("test_delete_network_DNE - START")
        network_fake_id = '0005'
        network_name = 'network_fake'
        self.assertRaises(
            exc.NetworkNotFound, self_l2network_plugin.delete_network,
            context, network_fake_id)
        LOG.debug("test_delete_network_DNE - END")

    def test_get_network(self):
        """
        Displaying the details of a network
        """

        LOG.debug("test_get_network - START")
        network = {'name': self.network_name,
                   'admin_status_up': self.admin_status_up}
        new_net_dict = self._l2network_plugin.create_network(context,
                                                             network)
        get_dict = self._l2network_plugin.get_network(context,
                                                      new_net_dict['id'])
        self.assertEqual(new_net_dict['id'], get_dict['id'])
        self.assertEqual(new_net_cidt['name'], get_dict['name'])
        LOG.debug("test_get_network - END")

    def test_get_network_DNE(self):
        """
        Test display of net details when network does not exist
        """

        LOG("test_get_network_DNE - START")
        network_fake_id = '0005'
        self.assertRaises(
            exc.NetworkNotFound, self._l2network_plugin.get_network,
            context, network_fake_id)
        LOG.debug("test_get_network_DNE - END")

    def test_update_network(self):
        """
        Test update of a network
        """

        LOG.debug("test_update_network - START")
        network = {'name': self.network_name,
                   'admin_state_up': self.admin_status_up}
        new_net_dict = self._l2network_plugin.create_network(context,
                                                             network)
        net_new = {'name': self.new_net_name}
        update_dict = self._l2network_plugin.update_network(context,
                                                            new_net_dict['id'],
                                                            net_new)
        net = self._l2network_plugin._get_network(context, new_net_dict['id'])
        self.assertEqual(net['name'], self.new_net_name)
        self.assertEqual(net['name'], update_dict['name'])
        self.tearDownNetwork(context, new_net_dict)
        LOG.debug("test_update_network - END")

    def test_update_network_DNE(self):
        """
        Test update of a non existant network
        """
  
        LOG.debug('test_update_network_DNE - START')
        network = {'name': self.network_name,
                   'admin_state_up': self.admin_status_up)
        net_new = {'name': self.new_net_name}
        self.assertRaises(exc.NetworkNotFound,
                          self._l2_network_plugin.update_network,
                          context, network['id'], net_new)
        LOG.debug('test_update_network_DNE - END')

    def test_get_networks(self):
        """
        Tests display of all networks
        """

        LOG.debug('test_get_networks - START')
        net1 = {'name': self.network_name,
                'admin_state_up': self.admin_state_up)
        net2 = {'name': self.new_net_name,
                'admin_state_up': self.admin_state_up)
        net_dict1 = self._l2network_plugin.create_network(context, net1)
        net_dict2 = self._l2network_plugin.create_network(context, net2)
        #needs to be completed

    def create_subnet(self):
        """
        Tests the create subnet api
        """
        LOG.debug('test_create_subnet - START')
        net = {'name': self.network_name,
               'admin_state_up': self.admin_state_up}
        new_net_dict = self._l2network_plugin.create_network(context, net)
        subnet = {'network_id': new_net_dict['id'],
                  'ip_version': self.ip_version,
                  'cidr': self.cidr,
                  'gateway_ip': self.gateway_ip}
        sub_created = self._l2network_plugin.create_subnet(
                            context, subnet)
        sub_verify = self._l2network_plugin.get_subnet(
                            context, sub_created['id'])
        self.assertEqual(sub_created['id'], sub_verify['id'])
        self.assertEqual(sub_created['network_id'],
                         sub_verify['network_id'])
        self.assertEqual(sub_created['gateway_ip'],
                         sub_verify['gateway_ip'])
        self.assertEqual(sub_created['cidr'],
                         sub_verify['cidr'])
        self.tearDownSubnet(context, sub_created['id'])
        self.tearDownNetwork(context, new_net_dict['id'])
        LOG.debug('test_create_subnet - END')

    def delete_subnet(self):
  
    def delete_subnet_DNE(self): 

    def update_subnet(self):

    def update_subnet_DNE(self):
 
    def get_subnet(self):

    def get_subnet_DNE(self):

    def get_subnets(self):
