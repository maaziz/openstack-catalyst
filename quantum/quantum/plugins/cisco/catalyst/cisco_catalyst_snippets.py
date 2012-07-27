# Subinterface created on vlan 40 with ip address 192.0.2.1
# and netmask 255.255.255.0
# - Chinmay
SUBINTERFACE_CREATE = """
ios_config "int g1/4.1" "encapsulation dot1q 40" " ip address 192.0.2.1
255.255.255.0" "no shut"
"""
