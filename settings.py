import yaml
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.yml')

with open(config_path, 'r') as file:
    data = yaml.safe_load(file)

MULTICAST_GROUP = data['multicast_group']
INTERFACE_IP = data['interface_ip']
SD_PORT = data['sd_port']
NEXT_PORT = data['next_port']