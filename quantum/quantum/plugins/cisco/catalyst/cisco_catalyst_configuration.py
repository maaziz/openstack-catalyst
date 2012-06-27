from quantum.common.config import find_config_file
from quantum.plugins.cisco.common import cisco_confiparser as confp

CP = confp.CiscoConfigParser(find_config_file({'plugin':'cisco'},[],'CATALYST.ini'))

SECTION = CP['SWITCH']
CATALYST_IP_ADDRESS = CP['CATALYST_ip_address']
CATALYST_FIRST_INTERFACE = CP['CATALYST_first_interface']
CATALYST_SECOND_INTERFACE = CP['CATALYST_second_interface']
CATALYST_SSH_PORT = CP['CATALYST_ssh_port']

SECTION = CP['DRIVER']
NAME = CP['name']
