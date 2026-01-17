import hid

print("Scanning for HID devices...")
device_list = hid.enumerate()

if not device_list:
    print("No HID devices found, or permissions are restricted.")
else:
    print(f"Found {len(device_list)} device(s).")
    for device_dict in device_list:
        print("-" * 30)
        # Sort keys for consistent output
        keys = sorted(device_dict.keys())
        for key in keys:
            print(f"{key:25} : {device_dict[key]}")
    print("-" * 30)
