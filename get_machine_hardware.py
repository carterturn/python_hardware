#!/usr/bin/python3
from re import compile
from requests import post
from subprocess import check_output
from subprocess import DEVNULL

from yaml import safe_dump


def _get_pci_devices():
    lspci_lines_array = check_output(['lspci', '-nnmm']).decode().splitlines()

    devices = []

    remove_device_code_regex = compile(' \[[0-9a-fA-F]+\]')

    for lspci_line in lspci_lines_array:
        device = {}
        device['slot'] = lspci_line[0:7]
        index = 7

        first_string_properties = ['class', 'merchant', 'device']
        for string_property in first_string_properties:
            index = lspci_line.find('"', index) + 1
            end_index = lspci_line.find('"', index)
            device[string_property] = remove_device_code_regex.sub('', lspci_line[index:end_index])
            index = end_index + 1

        index = index + 2
        device['rev'] = lspci_line[index:lspci_line.find(' ', index)]

        second_string_properties = ['subsystem vendor', 'subsystem device']
        for string_property in second_string_properties:
            index = lspci_line.find('"', index) + 1
            end_index = lspci_line.find('"', index)
            device[string_property] = remove_device_code_regex.sub('', lspci_line[index:end_index])
            index = end_index + 1

        devices.append({'class': device['class'], 'merchant': device['merchant'], 'name': device['device']})

    return devices


def _get_important_pci_devices():
    important_pci_classes = ['VGA compatible controller']

    return [x for x in _get_pci_devices() if x['class'] in important_pci_classes]


def _get_cpu_devices():
    reduce_ws_re = compile('\s+')  # reduce whitespace regular expression

    lscpu_lines_array = check_output(['lscpu']).decode().splitlines()

    cpu_property_string_list = dict(map(lambda x: reduce_ws_re.sub(' ', x).split(': '), lscpu_lines_array))

    cpu_vendor = cpu_property_string_list['Vendor ID']
    cpu_device = ''

    try:
        if cpu_property_string_list['Virtualization type']:
            cpu_device = 'Virtual ' + cpu_property_string_list['Model name']
    except KeyError:
        cpu_device = cpu_property_string_list['Model name']

    return [{'class': 'CPU', 'merchant': cpu_vendor, 'name': cpu_device}]


def _get_display_devices():
    CRT_connected = False
    CRT_type = ''
    DFP_connected = 8 * [False]
    DFP_types = 8 * ['']

    monitors = []
    try:
        with open('/var/log/Xorg.0.log', 'r') as xorg_logfile:

            connection_line_re = compile('connected$')
            DFP_number_re = compile('DFP-([0-9])')
            DFP_monitor_type_re = compile('\): ([A-Za-z0-9 ]*)\(DFP-')
            CRT_monitor_type_re = compile('\): ([A-Za-z0-9 ]*)\(CRT-')

            for line in xorg_logfile:
                line = line.strip()

                if connection_line_re.search(line):
                    if 'CRT' in line:
                        CRT_connected = (line.split(' ').pop(-1) == 'connected')
                        if CRT_connected:
                            CRT_type = CRT_monitor_type_re.search(line).group(1).strip()
                        else:
                            CRT_type = ''
                    else:
                        DFP_number = int(DFP_number_re.search(line).group(1))
                        DFP_connected[DFP_number] = (line.split(' ').pop(-1) == 'connected')
                        if DFP_connected[DFP_number]:
                            DFP_types[DFP_number] = DFP_monitor_type_re.search(line).group(1).strip()
                        else:
                            DFP_types[DFP_number] = ''

    except FileNotFoundError as e:
        return monitors

    for i in range(0, 8):
        if DFP_connected[i]:
            merchant = DFP_types[i].split(' ').pop(0)
            name = DFP_types[i].split(' ').pop(1)
            monitors.append({'class': 'Monitor', 'merchant': merchant, 'name': name})
    if CRT_connected:
        merchant = CRT_type.split(' ').pop(0)
        name = CRT_type.split(' ').pop(1)
        monitors.append({'class': 'Monitor', 'merchant': merchant, 'name': name})

    return monitors


def _get_usb_devices():
    lsusb_devices_array = check_output(['lsusb', '-v'], stderr=DEVNULL).decode().split('\n\n')
    lsusb_devices_array.pop(0)  # Remove blank first line

    lsusb_gap_re = compile('\s\s+')
    lsusb_code_re = compile('^[0-9A-Fa-fx]+ *')

    usb_devices = []

    for lsusb_device in lsusb_devices_array:
        device_lines_array = [lsusb_gap_re.sub(': ', x.strip()) for x in lsusb_device.splitlines()]
        device_property_pair_list = list(map(lambda x: x.split(': '), device_lines_array))

        # Convert to dictionary. Reverse to prefer earlier (usually more verbose) descriptions
        device_property_string_list = dict([x for x in reversed(device_property_pair_list) if len(x) == 2])

        usb_class = lsusb_code_re.sub('', device_property_string_list['bInterfaceClass'])
        usb_vendor = lsusb_code_re.sub('', device_property_string_list['idVendor'])
        usb_device = lsusb_code_re.sub('', device_property_string_list['idProduct'])

        if usb_device == '':
            usb_device = lsusb_code_re.sub('', device_property_string_list['bInterfaceProtocol'])

        usb_devices.append({'class': 'USB ' + usb_class, 'merchant': usb_vendor, 'name': usb_device})

    return usb_devices


def _get_important_usb_devices():
    important_usb_classes = ['USB Human Interface Device', 'USB Mass Storage', 'USB Vendor Specific Class']

    return [x for x in _get_usb_devices() if x['class'] in important_usb_classes]


def get_devices(only_important=True):

    if only_important:
        return _get_important_pci_devices() + _get_cpu_devices()\
            + _get_display_devices() + _get_important_usb_devices()
    else:
        return _get_pci_devices() + _get_cpu_devices() + _get_display_devices() + _get_usb_devices()


def get_devices_yaml():
    devices = get_devices()
    devices_sorted = sorted(devices, key=lambda d: d['class'] + d['merchant'] + d['name'])
    hostname = check_output('hostname').decode().strip()
    return safe_dump({'hostname': hostname, 'devices': devices_sorted}, width=1000)

data = get_devices_yaml()

print(data)
print(post('https://carterturn.com/fco/hardware', data=data).text)
