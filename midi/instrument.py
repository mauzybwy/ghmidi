import hid
import mido
from mido import Message
import math
import time

class MidiInstrument:
    def __init__(self, keymap, vid, pid, midi_bus):
        self.keymap = keymap
        self.device = None
        self.midiout = None
        self.vid = vid
        self.pid = pid
        self.midi_bus = midi_bus
        self.last = [0] * 10

    def __enter__(self):
        try:
            self._connect()
        except OSError as e:
            if e.args[0] == "open failed":
                print("⚠️ Please try disconnecting/re-connecting the USB device ⚠️")
                self._reconnect()
            else:
                raise

        self.midiout = mido.open_output(self.midi_bus)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.device:
            self.device.close()
        if self.midiout:
            self.midiout.close()

    def poll(self):
        try:
            self._poll()
        except (ValueError, OSError) as e:
            if e.args[0] in ["not open", "read error"]:
                print("⚠️ Please connect the USB device :( ⚠️")
                self._reconnect()
            else:
                raise

    def _connect(self):
        self.device = hid.device()
        # print(list_hid_devices())
        self.device.open(self.vid, self.pid)
        self.device.set_nonblocking(False)
        self.last = [0] * 10  # reset state on reconnect
            

    def _reconnect(self):
        if self.device:
            try:
                self.device.close()
            except:
                pass
            
        while True:
            time.sleep(1)
            try:
                self._connect()
                print("Connected :D")
                break
            except OSError:
                pass  # still not available

    def _poll(self):
        raise NotImplementedError("Please implement this method")

def list_hid_devices():
    """
    Enumerates and prints details of all connected HID devices.
    """
    print("Searching for HID devices...")
    try:
        devices = hid.enumerate()
        if not devices:
            print("No HID devices found.")
            return

        print(f"Found {len(devices)} device(s):")
        for dev in devices:
            print("-" * 20)
            print(f"  Path: {dev['path']}")
            print(f"  Vendor ID (VID): 0x{dev['vendor_id']:04x}")
            print(f"  Product ID (PID): 0x{dev['product_id']:04x}")
            print(f"  Serial Number: {dev['serial_number']}")
            print(f"  Manufacturer: {dev['manufacturer_string']}")
            print(f"  Product: {dev['product_string']}")
            print(f"  Usage Page: 0x{dev['usage_page']:04x}")
            print(f"  Usage: 0x{dev['usage']:04x}")
            # Other fields like interface_number, etc., may also be available
    except Exception as e:
        print(f"An error occurred: {e}")
