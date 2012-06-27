# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011, Cisco Systems, Inc.
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
# @author: Harsh Prasad, Cisco Systems, Inc.

import logging as LOG

from sqlalchemy.orm import exc

import quantum.plugins.cisco.db.api as db

from quantum.plugins.cisco.common import cisco_exceptions as c_exc
from quantum.plugins.cisco.db import catalyst_models


def get_all_catalystport_bindings():
    """Lists all the catalystport bindings"""
    LOG.debug("get_all_catalystport_bindings() called")
    session = db.get_session()
    try:
        bindings = session.query
        (catalyst_models.CatalystPortBinding).all()
        return bindings
    except exc.NoResultFound:
        return []


def get_catalystport_binding(vland_id):
    """Lists catalyst port binding for particular vlan"""
    LOG.debug("get_catlystport_binding() called")
    session = db.get_session()
    try:
        binding = (session.query(catalyst_models.CatalystPortBinding). \
                                filter_by(vland_id).all())
        return binding
    except exc.NoresultFound:
        raise c_exc.CatalystPortBindingNotFound(vlan_id=vlan_id)


def add_catalystport_binding(port_id, vlan_id):
    """Adds a catalystport binding"""
    LOG.debug("add_catalystport_binding() called")
    session = db.get_session()
    binding = catalyst_models.CatalystPortBinding(port_id, vlan_id)
    session.add(binding)
    session.flush()
    return binding


def remove_catalystport_binding(vlan_id):
    """Removes a catalystport binding"""
    LOG.debug("remove_catalystport_binding() called")
    session = db.get_session()
    try:
        binding = (session.query(catalyst_models.CatalystPortBinding).
                        filter_by(vlan_id=vlan_id).all())
        for bind in binding:
            session.delete(bind)
            session.flush()
            return binding
    except exc.NoResultFound:
        pass


def update_catalystport_binding(port_id, new_vlan_id):
    """Updates catalystport binding"""
    LOG.debug("update_catalystport_binding called")
    session = db.get_session()
    try:
        binding = (session.query(catalyst_models.CatalystPortBinding).
                        filter_by(port_id=port_id).one())
        if new_vlan_id:
            binding["vlan_id"] = new_vlan_id
            session.merge(binding)
            session.flush()
            return binding
    except exc.NoResultFound:
        raise c_exc.CatalystPortBindingNotFound()
