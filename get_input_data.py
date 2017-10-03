from Xlib.display import Display
from Xlib.ext import xinput

display = Display()

devices = display.xinput_query_device(0)._data['devices']

for device in devices:
    print(device['name'])
