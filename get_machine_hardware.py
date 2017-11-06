#!/usr/bin/python3

from yaml import safe_dump
from math import sqrt
from collections import namedtuple
from subprocess import check_output, DEVNULL
from re import compile, sub

from Xlib import X, display
from Xlib.ext import randr, xinput
from Xlib.error import DisplayNameError

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
            index = lspci_line.find('"', index)+1
            end_index = lspci_line.find('"', index)
            device[string_property] = remove_device_code_regex.sub('', lspci_line[index:end_index])
            index = end_index+1

        index = index + 2
        device['rev'] = lspci_line[index:lspci_line.find(' ', index)]

        second_string_properties = ['subsystem vendor', 'subsystem device']
        for string_property in second_string_properties:
            index = lspci_line.find('"', index)+1
            end_index = lspci_line.find('"', index)
            device[string_property] = remove_device_code_regex.sub('', lspci_line[index:end_index])
            index = end_index+1

        devices.append({'class': device['class'], 'merchant': device['merchant'], 'name': device['device']})
    
    return devices

def _get_important_pci_devices():
    important_pci_classes = ['VGA compatible controller']

    return [x for x in _get_pci_devices() if x['class'] in important_pci_classes]
    

def _get_cpu_devices():
    reduce_ws_re = compile('\s+') # reduce whitespace regular expression

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

INCHES_PER_MILLIMETER = 0.0394

def _parse_plug_and_play(plug_and_play_name):
    return chr(int(plug_and_play_name, 2) + 64)

def _parse_edid_manufacturer(edid_manufacturer):
    char_one = bin(edid_manufacturer[0])[2:].rjust(8, '0')[1:6]
    char_two = bin(edid_manufacturer[0])[2:].rjust(8, '0')[6:8] + bin(edid_manufacturer[1])[2:].rjust(8, '0')[0:3]
    char_three = bin(edid_manufacturer[1])[2:].rjust(8, '0')[3:8]
    return _parse_plug_and_play(char_one) + _parse_plug_and_play(char_two) + _parse_plug_and_play(char_three)

def _merge_little_endian_array(array):
    array.reverse()
    return int(''.join(list(map(lambda x: bin(x)[2:].rjust(8, '0'), array))), 2)

def _get_display_devices():
    try:
        x_display = display.Display(':0')
        x_screen = x_display.screen()
        x_window = x_screen.root.create_window(0, 0, 1, 1, 1, x_screen.root_depth, X.InputOutput, X.CopyFromParent)

        x_resources = x_window.xrandr_get_screen_resources()._data

        monitors = []

        for monitor in x_resources['outputs']:
            monitor_info = x_display.xrandr_get_output_info(monitor, x_resources['config_timestamp'])._data

            if monitor_info['crtc'] != 0: # This checks if a port is connected

                monitor_width = monitor_info['mm_width'] * INCHES_PER_MILLIMETER
                monitor_height = monitor_info['mm_height'] * INCHES_PER_MILLIMETER
                monitor_diagonal = round(sqrt(monitor_width**2 + monitor_height**2))

                edid_data = x_display.xrandr_get_output_property(monitor, 81, 0, 0, 128)._data['value']

                manufacturer = _parse_edid_manufacturer(edid_data[8:10])
                year_of_manufacture = str(1990 + edid_data[17])

                monitor_name = year_of_manufacture + ' ' + str(monitor_diagonal) + '"'

                monitors.append({'class': 'Monitor', 'merchant': manufacturer, 'name': monitor_name})

        return monitors
    except DisplayNameError as e:
        return []

def _get_usb_devices():
    lsusb_devices_array = check_output(['lsusb', '-v'], stderr=DEVNULL).decode().split("\n\n")
    lsusb_devices_array.pop(0) # Remove blank first line

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

def get_devices(only_important = True):

    if only_important:
        return _get_important_pci_devices() + _get_cpu_devices()\
        + _get_display_devices() + _get_important_usb_devices()
    else:
        return _get_pci_devices() + _get_cpu_devices() + _get_display_devices() + get_usb_devices()

def get_devices_yaml():
    devices = get_devices();
    devices_sorted = sorted(devices, key=lambda d: d['class']+d['merchant']+d['name'])
    hostname = check_output('hostname').decode().strip()
    return safe_dump({'hostname': hostname, 'devices': devices_sorted}, width=1000)

print(get_devices_yaml(), end='')
