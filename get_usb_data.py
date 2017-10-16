from re import compile, sub
from subprocess import check_output, DEVNULL

lsusb_devices_array = check_output(['lsusb', '-v'], stderr=DEVNULL).decode().split("\n\n")
lsusb_devices_array.pop(0) # Remove blank first line

lsusb_gap_re = compile('\s\s+')
lsusb_code_re = compile('^0x[0-9A-Fa-f]+ ')

usb_devices = []

for lsusb_device in lsusb_devices_array:
    device_lines_array = [lsusb_gap_re.sub(': ', x.strip()) for x in lsusb_device.splitlines()]
    device_property_pair_list = list(map(lambda x: x.split(': '), device_lines_array))
    device_property_string_list = dict([x for x in device_property_pair_list if len(x) == 2])

    usb_device = {}
    usb_device['vendor'] = lsusb_code_re.sub('', device_property_string_list['idVendor'])
    usb_device['device'] = lsusb_code_re.sub('', device_property_string_list['idProduct'])

    usb_devices.append(usb_device)
