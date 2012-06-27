from quantum.common.config import find_config_file
from quantum.plugins.cisco.common import cisco_configparser as confp

CP = confp.CiscoConfigParser(find_config_file({'plugin':'cisco'}, None,
                                               "catalyst.ini"))
SECTION = CP['SWITCH']

CATALYST_IP_ADDRESS = CP['catalyst_ip_address']
CATALYST_SSH_PORT = CP['catayst_ssh_port']

SECTION = CP['DRIVER']
CATALYST_DRIVER = CP['name']
