import logging

from ncclient import manager

from quantum.plugins.cisco.catalyst import cisco_catalyst_snippets as snipp

LOG = logging.getLogger(__name__)


class CiscoCATALYSTDriver():
    """
    Catalyst driver main class
    """
    def __init__(self):
        pass

    def ssh_connect(self, catalyst_host, catalyst_ssh_port, catalyst_user,
                    catalyst_password):
        """
        Makes the SSH connection to the switch
        """
        man = manager.connect(host=catalyst_host, port=catalyst_ssh_port,
                              username=catalyst_user,
                              password=catalyst_password)
        return man

    def create_subinterface(self, catalyst_host, catalyst_ssh_port,
                            catalyst_user, catalyst_password):
        """
        Create a sub interface with an ip on the give vlan
        on the switch
        """
        with self.ssh_connect(catalyst_host, int(catalyst_ssh_port)
                              catalyst_user, catalyst_password) as m:
            confstr = snipp.SUBINTERFACE_CREATE
            m.edit_config(target='running', config=confstr)
            m.close_session()
