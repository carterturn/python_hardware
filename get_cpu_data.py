from subprocess import check_output
import re

cpu_property_string_list = dict(map(lambda x: re.sub('[ \t]+', ' ', x).split(': '),
                                                     check_output('lscpu').decode().splitlines()))

cpu_properties = {}
cpu_properties['vendor'] = cpu_property_string_list['Vendor ID']
try:
    if cpu_property_string_list['Virtualization type']:
        cpu_properties['device'] = 'Virtual ' + cpu_property_string_list['Model Name']
except KeyError:
    cpu_properties['device'] = cpu_property_string_list['Model name']

cpu_properties['rev'] = cpu_property_string_list['Model']
cpu_properties['vendor'] = cpu_property_string_list['Vendor ID']
