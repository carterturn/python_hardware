from math import sqrt
import Xlib
from Xlib import X, display
from Xlib.ext import randr

INCHES_PER_MILLIMETER = 0.0394

def pnp_to_ascii(pnp):
    return chr(int(pnp, 2) + 64)

def parse_edid_manufacturer(edid_manu):
    character_one = bin(edid_manu[0])[2:].rjust(8, '0')[1:6]
    character_two = bin(edid_manu[0])[2:].rjust(8, '0')[6:8] + bin(edid_manu[1])[2:].rjust(8, '0')[0:3]
    character_three = bin(edid_manu[1])[2:].rjust(8, '0')[3:8]
    return pnp_to_ascii(character_one) + pnp_to_ascii(character_two) + pnp_to_ascii(character_three)

def merge_little_endian_array(array):
    array.reverse()
    return int(''.join(list(map(lambda x: bin(x)[2:].rjust(8, '0'), array))), 2)

def parse_edid(edid):
    edid_data = {}
    edid_data['header'] = str(edid[0:8])
    edid_data['manufacturer'] = parse_edid_manufacturer(edid[8:10])
    edid_data['product code'] = hex(merge_little_endian_array(edid[10:12]))
    edid_data['serial number'] = str(merge_little_endian_array(edid[12:16]))
    edid_data['week of manufacture'] = str(edid[16])
    edid_data['year of manufacture'] = str(1990 + edid[17])
    edid_data['edid version'] = str(edid[18]) + "." + str(edid[19])
    edid_data['display parameters'] = str(edid[20:25])
    edid_data['chromaticity coordinates'] = str(edid[25:35])
    #edid_data['Timing'] =  " + str(edid[35:54])
    #edid_data['Descriptor 1'] =  " + str(edid[54:72])
    #edid_data['Descriptor 2'] =  " + str(edid[72:90])
    #edid_data['Descriptor 3'] =  " + str(edid[90:108])
    #edid_data['Descriptor 4'] =  " + str(edid[108:126])
    return edid_data

display = display.Display()
window = display.screen().root.create_window(0, 0, 1, 1, 1,
					     display.screen().root_depth, X.InputOutput, X.CopyFromParent)

resources = window.xrandr_get_screen_resources()._data

for output in resources['outputs']:
    output_info = display.xrandr_get_output_info(output, resources['config_timestamp'])._data
    if output_info['crtc'] != 0:
        size = round(sqrt(output_info['mm_width']**2 + output_info['mm_height']**2) * INCHES_PER_MILLIMETER)
        edid_data = parse_edid(display.xrandr_get_output_property(output, 81, 0, 0, 128)._data['value'])

        print(edid_data['manufacturer'] + ' ' + edid_data['year of manufacture'] + ' ' + str(size) + '"')

