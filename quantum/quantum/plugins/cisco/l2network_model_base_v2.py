from abc import ABCMeta, abstractmethod
import inspect


class L2NetworkModelBaseV2(object):
    """
    Base class for L2 Network Model
    It relies on a pluggable network config module to gather
    knowledge of the system,but knows which device-specific plugins
    to invoke for a corresponding core API call, and what parameters tp pass
    to that plugin.
    """

    __metaclass__ = ABCMETA

    @abstractmethod
    def create_subnet(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def update_subnet(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def delete_subnet(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_subnets(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def create_network(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def delete_network(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_network(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def update_network(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_networks(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def create_port(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def update_port(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def delete_port(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_port(self, args):
        """
        :returns:
        :raises:
        """
        pass

    @abstractmethod
    def get_ports(self, args):
        """
        :returns:
        :raises:
        """
        pass
