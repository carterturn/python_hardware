import Xlib
from Xlib import X, display
from Xlib.ext import randr

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
    print("Header: " + str(edid[0:8]) + " "
	  + ("OK" if edid[0:8] == [0,255,255,255,255,255,255,0] else "Not OK"))
    print("Manufacturer: " + parse_edid_manufacturer(edid[8:10]))
    print("Product Code: " + hex(merge_little_endian_array(edid[10:12])))
    print("Serial Number: " + str(merge_little_endian_array(edid[12:16])))
    print("Week of Manufacture: " + str(edid[16]))
    print("Year of Manufacture: " + str(1990 + edid[17]))
    print("EDID Version: " + str(edid[18]) + "." + str(edid[19]))
    print("Display parameters: " + str(edid[20:25]))
    print("Chromaticity coordinates: " + str(edid[25:35]))
    print("Timing: " + str(edid[35:54]))
    print("Descriptor 1: " + str(edid[54:72]))
    print("Descriptor 2: " + str(edid[72:90]))
    print("Descriptor 3: " + str(edid[90:108]))
    print("Descriptor 4: " + str(edid[108:126]))

display = display.Display()
window = display.screen().root.create_window(0, 0, 1, 1, 1,
					     display.screen().root_depth, X.InputOutput, X.CopyFromParent)

resources = window.xrandr_get_screen_resources()._data

for output in resources['outputs']:
    output_info = display.xrandr_get_output_info(output, resources['config_timestamp'])._data
    if output_info['crtc'] != 0:
        print(output_info['name'] + ' WxH(mm):' + str(output_info['mm_width']) + 'x' + str(output_info['mm_height']))
        properties = display.xrandr_list_output_properties(output)._data['atoms']

        parse_edid(display.xrandr_get_output_property(output, 81, 0, 0, 128)._data['value'])
	
        # for property in properties:
        #     print(property)
        #     print(display.xrandr_get_output_property(output, property, 0, 0, 128)._data)

