"""show_vrf.py

NXOS parsers for the following show commands:
    * 'show vrf'
    * 'show vrf <WORD> detail'
"""

# Python
import re
import xmltodict

# Metaparser
from metaparser import MetaParser
from metaparser.util.schemaengine import Schema, Any, Optional, Or, And,\
                                         Default, Use


# =====================
# Parser for 'show vrf'
# =====================

class ShowVrfSchema(MetaParser):
    """Schema for show vrf"""

    schema = {
        'vrfs':
            {Any():
                {'vrf_id': int,
                 'vrf_state': str,
                 'reason': str,},
            },
        }

class ShowVrf(ShowVrfSchema):
    """Parser for show vrf"""

    def cli(self):
        cmd = 'show vrf'
        out = self.device.execute(cmd)
        
        # Init vars
        vrf_dict = {}

        for line in out.splitlines():
            line = line.rstrip()

            # VRF2                                    4 Up      --
            # default                                 1 Up      --
            p1 = re.compile(r'^\s*(?P<vrf_name>(\S+)) +(?P<vrf_id>[0-9]+)'
                             ' +(?P<vrf_state>(Up|Down)) +(?P<reason>(\S+))$')
            m = p1.match(line)
            if m:
                if 'vrfs' not in vrf_dict:
                    vrf_dict['vrfs'] = {}
                vrf_name = str(m.groupdict()['vrf_name'])
                if vrf_name not in vrf_dict['vrfs']:
                    vrf_dict['vrfs'][vrf_name] = {}
                vrf_dict['vrfs'][vrf_name]['vrf_id'] = \
                    int(m.groupdict()['vrf_id'])
                vrf_dict['vrfs'][vrf_name]['vrf_state'] = \
                    str(m.groupdict()['vrf_state'])
                vrf_dict['vrfs'][vrf_name]['reason'] = \
                    str(m.groupdict()['reason'])
                continue

        return vrf_dict

class ShowVrfInterfaceSchema(MetaParser):
    """Schema for show vrf interface"""

    schema = {
            'vrf_interface':
                {Any():
                    {'vrf_name': str,
                     'vrf_id': str,
                     'site_of_origin': str},
                },
            }

class ShowVrfInterface(ShowVrfInterfaceSchema):
    """Parser for show vrf Interface"""

    def cli(self):
        cmd = 'show vrf interface'
        out = self.device.execute(cmd)
        
        # Init vars
        vrf_interface_dict = {}

        for line in out.splitlines():
            line = line.rstrip()

            p1 = re.compile(r'^\s*Interface +VRF-Name +VRF-ID +Site-of-Origin$')
            m = p1.match(line)
            if m:
                continue

            p2 = re.compile(r'^\s*(?P<intf_name>[a-zA-Z0-9\/]+)'
                ' +(?P<vrf_name>[a-zA-Z0-9\-]+) +(?P<vrf_id>[0-9]+)'
                ' +(?P<site_of_origin>[a-zA-Z0-9\-]+)?$')
            m = p2.match(line)
            if m:
                interface = m.groupdict()['intf_name']
                if 'vrf_interface' not in vrf_interface_dict:
                    vrf_interface_dict['vrf_interface'] = {}
                if interface not in vrf_interface_dict['vrf_interface']:
                    vrf_interface_dict['vrf_interface'][interface] = {}
                vrf_interface_dict['vrf_interface'][interface]['vrf_name'] = \
                    m.groupdict()['vrf_name']
                vrf_interface_dict['vrf_interface'][interface]['vrf_id'] = \
                    m.groupdict()['vrf_id']
                vrf_interface_dict['vrf_interface'][interface]['site_of_origin'] = \
                    m.groupdict()['site_of_origin']
                continue

        return vrf_interface_dict


class ShowVrfDetailSchema(MetaParser):
    """Schema for show vrf <vrf> detail"""

    schema = {Any():
                {
                 'vrf_id':  int,
                 Optional('route_distinguisher'): str,
                 Optional('vpn_id'): str,
                 'max_routes':  int,
                 'mid_threshold':  int,
                 'state': str,
                 'address_family': {
                    Any(): {
                        'table_id': str,
                         'fwd_id':  str,
                         'state':  str,
                    },                        
                }
            },
        }

class ShowVrfDetail(ShowVrfDetailSchema):
    """Parser for show vrf <vrf> detail"""

    def cli(self, vrf='all'):
        cmd = 'show vrf {} detail'.format(vrf)
        out = self.device.execute(cmd)
        
        # Init vars
        vrf_dict = {}

        for line in out.splitlines():
            line = line.strip()

            # VRF-Name: VRF1, VRF-ID: 3, State: Up
            p1 = re.compile(r'^VRF\-Name: +(?P<vrf>[\w\-]+), +'
                             'VRF-ID: +(?P<vrf_id>\d+), +'
                             'State: +(?P<state>\w+)$')
            m = p1.match(line)
            if m:
                vrf = m.groupdict()['vrf']
                if vrf not in vrf_dict:
                    vrf_dict[vrf] = {}
                vrf_dict[vrf]['vrf_id'] = int(m.groupdict()['vrf_id'])
                vrf_dict[vrf]['state'] = m.groupdict()['state'].lower()
                continue

            # VPNID: unknown
            p2 = re.compile(r'^VPNID: +(?P<vpn_id>\w+)$')
            m = p2.match(line)
            if m:
                vpn_id = m.groupdict()['vpn_id']
                if vpn_id != 'unknown':
                    vrf_dict[vrf]['vpn_id'] = vpn_id
                continue

            # RD: 300:1
            p3 = re.compile(r'^RD: +(?P<rd>[\w\:]+)$')
            m = p3.match(line)
            if m:
                vrf_dict[vrf]['route_distinguisher'] = m.groupdict()['rd']
                continue

            # Max Routes: 20000  Mid-Threshold: 17000
            p4 = re.compile(r'^Max +Routes: +(?P<max_routes>\d+) +'
                             'Mid\-Threshold: +(?P<mid_threshold>\d+)$')
            m = p4.match(line)
            if m:
                vrf_dict[vrf]['max_routes'] = int(m.groupdict()['max_routes'])
                vrf_dict[vrf]['mid_threshold'] = int(m.groupdict()['mid_threshold'])
                continue

            # Table-ID: 0x80000003, AF: IPv6, Fwd-ID: 0x80000003, State: Up
            p5 = re.compile(r'^Table\-ID: +(?P<table_id>\w+), +'
                             'AF: +(?P<af>\w+), +'
                             'Fwd\-ID: (?P<fwd_id>\w+), +'
                             'State: +(?P<state>\w+)$')
            m = p5.match(line)
            if m:
                af = m.groupdict()['af'].lower()
                if 'address_family' not in vrf_dict[vrf]:
                    vrf_dict[vrf]['address_family'] = {}
                if af not in vrf_dict[vrf]['address_family']:
                    vrf_dict[vrf]['address_family'][af] = {}

                vrf_dict[vrf]['address_family'][af]['table_id'] = m.groupdict()['table_id']
                vrf_dict[vrf]['address_family'][af]['fwd_id'] = m.groupdict()['fwd_id']
                vrf_dict[vrf]['address_family'][af]['state'] = m.groupdict()['state'].lower()
                continue

        return vrf_dict


# vim: ft=python et sw=4
