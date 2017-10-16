from subprocess import check_output

pci_string_array = check_output(['lspci', '-nnmm']).decode().splitlines()

devices = []

for pci_string in pci_string_array:

    device = {}
    device['slot'] = pci_string[0:7]
    index = 7

    first_string_properties = ['class', 'vendor', 'device']
    for string_property in first_string_properties:
        index = pci_string.find('"', index)+1
        end_index = pci_string.find('"', index)
        device[string_property] = pci_string[index:end_index]
        index = end_index+1

    index = index + 2
    device['rev'] = pci_string[index:pci_string.find(' ', index)]

    second_string_properties = ['subsystem vendor', 'subsystem device']
    for string_property in second_string_properties:
        index = pci_string.find('"', index)+1
        end_index = pci_string.find('"', index)
        device[string_property] = pci_string[index:end_index]
        index = end_index+1

    devices.append(device)
