from collections import defaultdict
import json


def read_nxos_config_file(filename="Configurations/SW-ATCA-93180-1-Configuration_0.1"):
    config_file = open(filename, "r")
    return config_file

def create_vlans_from_nxos(file,  cmd_string="vlan "):
    vlan_id = ''
    prev_line = ''
    epgs_bds = {}
    subnets_vrfs = {}
    vrf_lst = []
    vrf_found = 'n'
    for line in config_file:
        if line.startswith(cmd_string) and len(line) < 11:
            prev_line = line
            temp_line = line.split(" ")
            vlan_id = temp_line[1].strip()
            epgs_bds[vlan_id] = {}
        elif line.startswith("  name") and prev_line.startswith(cmd_string):
            vlan_name_lst = line.split("  name")
            vlan_name = vlan_name_lst[1].strip()
            epgs_bds[vlan_id]= {
                "name": vlan_name}
        elif line.startswith("interface Vlan"):
            subnet_lst = line.split('interface Vlan')
            svi_cleaned = subnet_lst[1].strip()
            subnets_vrfs[svi_cleaned] = {}
            prev_line = line
        elif line.startswith("  vrf member") and prev_line.startswith('interface Vlan'):
            vrf_lst = line.split('  vrf member ')
            subnets_vrfs[svi_cleaned] = {"vrf": vrf_lst[1].strip()}
            #epgs_bds[subnet_cleaned]['vrf'] = {}
            epgs_bds[svi_cleaned]["vrf"] = vrf_lst[1].strip()
            vrf_found = 'y'
        try:
            if line.startswith("  ip address") and prev_line.startswith('interface Vlan') and subnets_vrfs[svi_cleaned]["vrf"] == vrf_lst[1].strip():
                ip_lst = line.split('  ip address ')
                subnets_vrfs[svi_cleaned] = {
                    "vrf": vrf_lst[1].strip(),
                    "ip": ip_lst[1].strip()}
                epgs_bds[svi_cleaned]['ip'] = ip_lst[1].strip()
        except:
            if line.startswith("  ip address") and prev_line.startswith('interface Vlan'):
                ip_lst = line.split('  ip address ')
                subnets_vrfs[svi_cleaned] = {
                    "vrf": "DEFAULT",
                    "ip": ip_lst[1].strip()}
            epgs_bds[svi_cleaned]["vrf"] = "DEFAULT"
            epgs_bds[svi_cleaned]["ip"] = ip_lst[1].strip()
    return epgs_bds, subnets_vrfs

config_file = read_nxos_config_file()
epgs_bds, bd_subnets = create_vlans_from_nxos(config_file)

bdsubnet_epg = defaultdict(list)

for d in (epgs_bds, bd_subnets): # you can list as many input dicts as you want here
    for key, value in d.iteritems():
        bdsubnet_epg[key].append(value)

#print json.dumps(bdsubnet_epg, sort_keys=True, indent=4)
print json.dumps(epgs_bds, sort_keys=True, indent=4)