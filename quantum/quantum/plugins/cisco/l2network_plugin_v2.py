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
# @author: Sumit Naiksatam, Cisco Systems, Inc.

import inspect
import logging

from sqlalchemy.orm import exc

from quantum.db.db_base_plugin_v2 import QuantumDbPluginV2
from quantum.common import exceptions as q_exc
from quantum.openstack.common import importutils
from quantum.plugins.cisco import l2network_plugin_configuration as conf
from quantum.plugins.cisco.common import cisco_constants as const
from quantum.plugins.cisco.common import cisco_credentials as cred
from quantum.plugins.cisco.common import cisco_exceptions as cexc
from quantum.plugins.cisco.common import cisco_utils as cutil
from quantum.plugins.cisco.db import api as db
from quantum.plugins.cisco.db import l2network_db as cdb
from quantum.plugins.cisco.db import models_v2


LOG = logging.getLogger(__name__)


class L2NetworkV2(QuantumDbPluginV2):
    """ L2 Network Framework Plugin """
    supported_extension_aliases = ["Cisco Multiport", "Cisco Credential",
                                   "Cisco Port Profile", "Cisco qos",
                                   "Cisco Nova Tenant"]

    def __init__(self):
        cdb.initialize()
        cred.Store.initialize()
        self._model = importutils.import_object(conf.MODEL_CLASS)
        self._vlan_mgr = importutils.import_object(conf.MANAGER_CLASS)
        """
        Changes for configure_db accordingly will be done later
        """

        sql_connection = "mysql://%s:%s@%s/%s" % (conf.DB_USER,
                          conf.DB_PASS, conf.DB_HOST, conf.DB_NAME)
        db.configure_db({'sql_connection': sql_connection,
                         'base': models_v2.model_base.BASEV2})
        LOG.debug("L2Network plugin initialization done successfully\n")

    def create_network(self, context, network):
        LOG.debug("L2Network's create_network() called")
        n = super().create_network(context, network)
        tenant_id = n['tenant_id']
        new_net_id = n['id']
        net_name = n['name']
        vlan_id = self._get_vlan_for_tenant(tenant_id, net_name)
        vlan_name = self._get_vlan_name(new_net_id, str(vlan_id))
        self._invoke_device_plugins(self._func_name(), [context,
                                                        n, vlan_name,
                                                        vlan_id])
        cdb.add_vlan_binding(vlan_id, vlan_name, new_net_id)
        return n

    def update_network(self, context, id, network):
        LOG.debug("L2Network's update_network() called")
        n = super().update_network(context, id, network)
        self._invoke_device_plugins(self._func_name(), [context, id,
                                                        network])
        return n

    def delete_network(self, context, id):
        LOG.debug("L2Network's delete_network() called")
        """
        Keep checking db_base_plugin_v2 until ovs plugin not released
        """
        with context.session.begin():
            network = super()._get_network(context, id)

            filter = {'network_id': [id]}
            ports = super.get_ports(context, filters=filter)
            if ports:
                raise q_exc.NetworkInUse(net_id=id)

            subnets_qry = context.session.query(models_v2.Subnet)
            subnets_qry.filter_by(network_id=id).delete()
            net_id = network['id']
            tenant_id = context.tenant_id
            self._invoke_device_plugins(self._func_name(), [context, id])
            self._release_vlan_for_tenant(tenant_id, net_id)
            cdb.remove_vlan_binding(net_id)

            context.session.delete(network)

    def get_network(self, context, id, fields=None, verbose=None):
        LOG.debug("L2Network's get_network() called")

        network = super().get_network(context, id, fields=fields,
                                      verbose=verbose)
        self._invoke_device_plugins(self._func_name(), [context, id, fields,
                                                        verbose])
        return network

    def get_networks(self, context, filters=None, fields=None, verbose=None):
        LOG.debug("L2Network's get_networks() called")
        networks = super().get_networks(self, context, filters=filters,
                                        fields=fields, verbose=verbose)
        self._invoke_device_plugins(self._func_name(), [context, filters,
                                                        fields, verbose])
        return networks

    def create_subnet(self, context, subnet):
        LOG.debug("L2Network's reate_subnet() called")
        """
        Method for subnet-vlan binding yet to be added
        """
        subnet = super().create_subnet(context, subnet)
        self._invoke_device_plugins(self._func_name(), [context, subnet])
        return subnet

    def update_subnet(self, context, id, subnet):
        LOG.debug("L2Network's update_subnet() called")
        """
        Methods for subnet binding to vlan yet to be added.
        """
        subnet = super().update_subnet(context, id, subnet)
        self._invoke_device_plugins(self._func_name(), [context, id, subnet])
        return subnet

    def delete_subnet(self, context, id):
        LOG.debug("L2Network's delete_subnet() called")
        """
        Methods for vlan and subnet release yet to be added.
        """
        with context.session.begin():
            subnet = super()._get_subnet(context, id)

            allocations_qry = context.session.query(models_v2.IPAllocation)
            allocations_qry.filter_by(subnet_id=id).delete()
            self._invoke_device_plugins(self._func_name(), [context, id])
            context.session.delete(subnet)

    def get_subnet(self, context, id, fields=None, verbose=None):
        LOG.debug("L2Network's get_subnet() called")
        """
        Methods for vlan and subnet binding yet to be added.
        """
        subnet = super().get_subnet(context, id, fields=fields,
                                    verbose=verbose)
        self._invoke_device_plugins(self._func_name(), [context, id, fields,
                                                        verbose])
        return subnet

    def get_subnets(self, context, filters=None, fields=None, verbose=None):
        LOG.debug("L2Network's get_subnets() called")
        """
        Methods for vlan and subnet binding yet to be added.
        """
        subnets = super().get_subnets(context, filters=filters, fields=fields,
                                      verbose=verbose)
        self._invoke_device_plugins(self._func_name(), [context, filters,
                                                        fields, verbose])
        return subnets

    def create_port(self, context, port):
        LOG.debug("L2Network's create_port() called")
        port = super().create_port(context, port)
        self._invoke_device_plugins(self._func_name(), [context, port])

        return port

    def update_port(self, context, id, port):
        LOG.debug("L2Network's update_port() called")
        port = super().update_port(context, id, port)
        self._invoke_device_plugins(self._func_name(), [context, id, port])
        return port

    def delete_port(self, context, id):
        LOG.debug("L2Network's delete_port() called")
        with context.session.begin():
            port = super()._get_port(context, id)

            allocations_qry = context.session.query(models_v2.IPAllocation)
            allocations_qry.filter_by(port_id=id).delete()
            self._invoke_device_plugins(self._func_name(), [context, id])
            context.session.delete(port)

    def get_port(self, context, id, fields=None, verbose=None):
        LOG.debug("L2Network's get_port() called")
        port = super().get_port(context, id, fields, verbose)
        self._invoke_device_plugins(self._func_name(), [context, id, fields,
                                                        verbose])
        return port

    def get_ports(self, context, filters=None, fields=None, verbose=None):
        LOG.debug("L2Network's get_ports() called")
        """
        Vlan specific _device_invoke_plugin needs special net_id
        """
        ports = super().get_ports(context, filters=filters, fields=fields,
                                  verbose=verbose)
        self._invoke_device_plugins(self._func_name(), [context, filters,
                                                        fields, verbose])
        return ports

    """
    Extension API implementation
    """
    def get_all_portprofiles(self, tenant_id):
        """Get all port profiles"""
        LOG.debug("get_all_portprofiles() called\n")
        pplist = cdb.get_all_portprofiles()
        new_pplist = []
        for portprofile in pplist:
            new_pp = cutil.make_portprofile_dict(tenant_id,
                                                 portprofile[const.UUID],
                                                 portprofile[const.PPNAME],
                                                 portprofile[const.PPQOS])
            new_pplist.append(new_pp)

        return new_pplist

    def get_portprofile_details(self, tenant_id, profile_id):
        """Get port profile details"""
        LOG.debug("get_portprofile_details() called\n")
        try:
            portprofile = cdb.get_portprofile(tenant_id, profile_id)
        except Exception:
            raise cexc.PortProfileNotFound(tenant_id=tenant_id,
                                           portprofile_id=profile_id)

        new_pp = cutil.make_portprofile_dict(tenant_id,
                                             portprofile[const.UUID],
                                             portprofile[const.PPNAME],
                                             portprofile[const.PPQOS])
        return new_pp

    def create_portprofile(self, tenant_id, profile_name, qos):
        """Create port profile"""
        LOG.debug("create_portprofile() called\n")
        portprofile = cdb.add_portprofile(tenant_id, profile_name,
                                          const.NO_VLAN_ID, qos)
        new_pp = cutil.make_portprofile_dict(tenant_id,
                                             portprofile[const.UUID],
                                             portprofile[const.PPNAME],
                                             portprofile[const.PPQOS])
        return new_pp

    def delete_portprofile(self, tenant_id, profile_id):
        """Delete portprofile"""
        LOG.debug("delete_portprofile() called\n")
        try:
            portprofile = cdb.get_portprofile(tenant_id, profile_id)
        except Exception:
            raise cexc.PortProfileNotFound(tenant_id=tenant_id,
                                           portprofile_id=profile_id)

        plist = cdb.get_pp_binding(tenant_id, profile_id)
        if plist:
            raise cexc.PortProfileInvalidDelete(tenant_id=tenant_id,
                                                profile_id=profile_id)
        else:
            cdb.remove_portprofile(tenant_id, profile_id)

    def rename_portprofile(self, tenant_id, profile_id, new_name):
        """Rename port profile"""
        LOG.debug("rename_portprofile() called\n")
        try:
            portprofile = cdb.get_portprofile(tenant_id, profile_id)
        except Exception:
            raise cexc.PortProfileNotFound(tenant_id=tenant_id,
                                           portprofile_id=profile_id)
        portprofile = cdb.update_portprofile(tenant_id, profile_id, new_name)
        new_pp = cutil.make_portprofile_dict(tenant_id,
                                             portprofile[const.UUID],
                                             portprofile[const.PPNAME],
                                             portprofile[const.PPQOS])
        return new_pp

    def associate_portprofile(self, tenant_id, net_id,
                              port_id, portprofile_id):
        """Associate port profile"""
        LOG.debug("associate_portprofile() called\n")
        try:
            portprofile = cdb.get_portprofile(tenant_id, portprofile_id)
        except Exception:
            raise cexc.PortProfileNotFound(tenant_id=tenant_id,
                                           portprofile_id=portprofile_id)

        cdb.add_pp_binding(tenant_id, port_id, portprofile_id, False)

    def disassociate_portprofile(self, tenant_id, net_id,
                                 port_id, portprofile_id):
        """Disassociate port profile"""
        LOG.debug("disassociate_portprofile() called\n")
        try:
            portprofile = cdb.get_portprofile(tenant_id, portprofile_id)
        except Exception:
            raise cexc.PortProfileNotFound(tenant_id=tenant_id,
                                           portprofile_id=portprofile_id)

        cdb.remove_pp_binding(tenant_id, port_id, portprofile_id)

    def get_all_qoss(self, tenant_id):
        """Get all QoS levels"""
        LOG.debug("get_all_qoss() called\n")
        qoslist = cdb.get_all_qoss(tenant_id)
        return qoslist

    def get_qos_details(self, tenant_id, qos_id):
        """Get QoS Details"""
        LOG.debug("get_qos_details() called\n")
        try:
            qos_level = cdb.get_qos(tenant_id, qos_id)
        except Exception:
            raise cexc.QosNotFound(tenant_id=tenant_id,
                                   qos_id=qos_id)
        return qos_level

    def create_qos(self, tenant_id, qos_name, qos_desc):
        """Create a QoS level"""
        LOG.debug("create_qos() called\n")
        qos = cdb.add_qos(tenant_id, qos_name, str(qos_desc))
        return qos

    def delete_qos(self, tenant_id, qos_id):
        """Delete a QoS level"""
        LOG.debug("delete_qos() called\n")
        try:
            qos_level = cdb.get_qos(tenant_id, qos_id)
        except Exception:
            raise cexc.QosNotFound(tenant_id=tenant_id,
                                   qos_id=qos_id)
        return cdb.remove_qos(tenant_id, qos_id)

    def rename_qos(self, tenant_id, qos_id, new_name):
        """Rename QoS level"""
        LOG.debug("rename_qos() called\n")
        try:
            qos_level = cdb.get_qos(tenant_id, qos_id)
        except Exception:
            raise cexc.QosNotFound(tenant_id=tenant_id,
                                   qos_id=qos_id)
        qos = cdb.update_qos(tenant_id, qos_id, new_name)
        return qos

    def get_all_credentials(self, tenant_id):
        """Get all credentials"""
        LOG.debug("get_all_credentials() called\n")
        credential_list = cdb.get_all_credentials(tenant_id)
        return credential_list

    def get_credential_details(self, tenant_id, credential_id):
        """Get a particular credential"""
        LOG.debug("get_credential_details() called\n")
        try:
            credential = cdb.get_credential(tenant_id, credential_id)
        except Exception:
            raise cexc.CredentialNotFound(tenant_id=tenant_id,
                                          credential_id=credential_id)
        return credential

    def create_credential(self, tenant_id, credential_name, user_name,
                          password):
        """Create a new credential"""
        LOG.debug("create_credential() called\n")
        credential = cdb.add_credential(tenant_id, credential_name,
                                        user_name, password)
        return credential

    def delete_credential(self, tenant_id, credential_id):
        """Delete a credential"""
        LOG.debug("delete_credential() called\n")
        try:
            credential = cdb.get_credential(tenant_id, credential_id)
        except Exception:
            raise cexc.CredentialNotFound(tenant_id=tenant_id,
                                          credential_id=credential_id)
        credential = cdb.remove_credential(tenant_id, credential_id)
        return credential

    def rename_credential(self, tenant_id, credential_id, new_name):
        """Rename the particular credential resource"""
        LOG.debug("rename_credential() called\n")
        try:
            credential = cdb.get_credential(tenant_id, credential_id)
        except Exception:
            raise cexc.CredentialNotFound(tenant_id=tenant_id,
                                          credential_id=credential_id)
        credential = cdb.update_credential(tenant_id, credential_id, new_name)
        return credential

    def schedule_host(self, tenant_id, instance_id, instance_desc):
        """Provides the hostname on which a dynamic vnic is reserved"""
        LOG.debug("schedule_host() called\n")
        host_list = self._invoke_device_plugins(self._func_name(),
                                                [tenant_id,
                                                 instance_id,
                                                 instance_desc])
        return host_list

    def associate_port(self, tenant_id, instance_id, instance_desc):
        """
        Get the portprofile name and the device name for the dynamic vnic
        """
        LOG.debug("associate_port() called\n")
        return self._invoke_device_plugins(self._func_name(), [tenant_id,
                                                               instance_id,
                                                               instance_desc])

    def detach_port(self, tenant_id, instance_id, instance_desc):
        """
        Remove the association of the VIF with the dynamic vnic
        """
        LOG.debug("detach_port() called\n")
        return self._invoke_device_plugins(self._func_name(), [tenant_id,
                                                               instance_id,
                                                               instance_desc])

    def create_multiport(self, tenant_id, net_id_list, port_state, ports_desc):
        """
        Creates multiple ports on the specified Virtual Network.
        """
        LOG.debug("create_ports() called\n")
        ports_num = len(net_id_list)
        ports_id_list = []
        ports_dict_list = []

        for net_id in net_id_list:
            db.validate_network_ownership(tenant_id, net_id)
            port = db.port_create(net_id, port_state)
            ports_id_list.append(port[const.UUID])
            port_dict = {const.PORT_ID: port[const.UUID]}
            ports_dict_list.append(port_dict)

        self._invoke_device_plugins(self._func_name(), [tenant_id,
                                                        net_id_list,
                                                        ports_num,
                                                        ports_id_list])
        return ports_dict_list

    """
    Private functions
    """
    def _invoke_device_plugins(self, function_name, args):
        """
        All device-specific calls are delegated to the model
        """
        return getattr(self._model, function_name)(args)

    def _get_vlan_for_tenant(self, tenant_id, net_name):
        """Get vlan ID"""
        return self._vlan_mgr.reserve_segmentation_id(tenant_id, net_name)

    def _release_vlan_for_tenant(self, tenant_id, net_id):
        """Relase VLAN"""
        return self._vlan_mgr.release_segmentation_id(tenant_id, net_id)

    def _get_vlan_name(self, net_id, vlan):
        """Getting the vlan name from the tenant and vlan"""
        vlan_name = conf.VLAN_NAME_PREFIX + vlan
        return vlan_name

    def _validate_port_state(self, port_state):
        """Checking the port state"""
        if port_state.upper() not in (const.PORT_UP, const.PORT_DOWN):
            raise exc.StateInvalid(port_state=port_state)
        return True

    def _func_name(self, offset=0):
        """Getting the name of the calling funciton"""
        return inspect.stack()[1 + offset][3]
