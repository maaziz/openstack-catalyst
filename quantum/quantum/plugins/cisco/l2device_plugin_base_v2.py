from abc import ABCMeta, abstractmethod
import inspect


class L2DevicePluginBaseV2(object):
    """
    Base class for a device specific plugin.
    An example for a device specific plugin is a Catalyst Switch.
    The network model relies on device-category-specific plugins to perform
    the configuration on each device.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_subnet(self, context, subnet):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def update_subnet(self, context, id, subnet):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_subnet(self, context, id, fields=None, verbose=None):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def delete_subnet(self, context, id):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_subnets(self, context, filters=None, fields=None, verbose=None):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def create_network(self, context, network, vlan_name, vlan_id):
        """
        :returns:
        :raises:
        """
        pass

    def update_network(self, context, id, network):
        """
        :returns:
        :raises:
        """
        pass

    def delete_network(self, context, id):
        """
        :returns:
        :raises:
        """
        pass

    def get_network(self, context, id, fields=None, verbose=None):
        """
        :returns:
        :raises:
        """
        pass

    def get_networks(self, context, filters=None, fields=None, verbose=None):
        """
        :returns:
        :raises:
        """
        pass

    def create_port(self, context, port):
        """
        :returns:
        :raises:
        """
        pass

    def update_port(self, context, id, port):
        """
        :returns:
        :raises:
        """
        pass

    def delete_port(self, context, id):
        """
        :returns:
        :raises:
        """
        pass

    def get_port(self, context, id, fields=None, verbose=None):
        pass

    def get_ports(self, context, filters=None, verbose=None):
        pass
