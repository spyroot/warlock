pci_class_codes = {
    0x00: "Device was built before Class Code definitions were finalized",
    0x01: "Mass Storage Controller",
    0x02: "Network Controller",
    0x03: "Display Controller",
    0x04: "Multimedia Device",
    0x05: "Memory Controller",
    0x06: "Bridge Device",
    0x07: "Simple Communication Controllers",
    0x08: "Base System Peripherals",
    0x09: "Input Devices",
    0x0A: "Docking Stations",
    0x0B: "Processors",
    0x0C: "Serial Bus Controllers",
    0x0D: "Wireless Controller",
    0x0E: "Intelligent I/O Controllers",
    0x0F: "Satellite Communication Controllers",
    0x10: "Encryption/Decryption Controllers",
    0x11: "Data Acquisition and Signal Processing Controllers",
    0x12: "Processing Accelerators",
    0x13: "Non-Essential Instrumentation",
    # 0x14 - 0xFE are Reserved
    0xFF: "Device does not fit in any defined classes"
}


def decode_class_id(pci_class_id):
    base_class = (pci_class_id >> 8) & 0xFF
    return pci_class_codes.get(base_class, f"Reserved or Unknown Device Type (0x{base_class:02X})")


class_id = 512
device_type = decode_class_id(class_id)
print(f"Class ID {class_id} (0x{class_id:04X}) corresponds to a {device_type}.")


