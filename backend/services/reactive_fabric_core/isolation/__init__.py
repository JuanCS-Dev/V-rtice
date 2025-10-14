"""
Network Isolation Layer for Reactive Fabric
Implements L3-L2-L1 isolation with Data Diode simulation
"""

from .data_diode import DataDiode, DiodeDirection
from .firewall import NetworkFirewall, FirewallRule
from .network_segmentation import NetworkSegmentation, VLANConfig
from .kill_switch import KillSwitch, EmergencyShutdown

__all__ = [
    'DataDiode',
    'DiodeDirection',
    'NetworkFirewall',
    'FirewallRule',
    'NetworkSegmentation',
    'VLANConfig',
    'KillSwitch',
    'EmergencyShutdown'
]