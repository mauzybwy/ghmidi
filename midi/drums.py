from mido import Message
from .instrument import MidiInstrument
import math
import yaml

VID = 0x1209
PID = 0x2882

"""
  Path: b'DevSrvsID:4295599843'
  Vendor ID (VID): 0x1209
  Product ID (PID): 0x2882
  Serial Number: E6653811DB1F1E213031
  Manufacturer: RetroCultMods
  Product: V3 Adapter - GH Guitar (Default)
  Usage Page: 0x0001
  Usage: 0x0005
"""

CONFIG_PATH = 'midi/drums_config.yaml'

def load_config():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    
    midimap = config['midimap']
    keymap_config = config['keymap']
    
    keymap = [None] * 10
    for color, data in keymap_config.items():
        keymap[data['index']] = {
            'id': color,
            'note': midimap[data['pad']]
        }
    
    print(f"Loaded config: {[k['id'] if k else None for k in keymap]}")
    return keymap

class MidiDrums(MidiInstrument):
    def __init__(
            self,
            channel = 0,
            midi_bus = "IAC Driver Bus 1",
    ):
        self.channel = channel
        self.keymap = load_config()
        # super().__init__(VID, PID, midi_bus)
        super().__init__("V3 Adapter - GH Drums", midi_bus)
    
    def _poll(self):
        data = self.device.read(64)

        if not data:
            return

        print(data)

        for i, b in enumerate(data):
            key = self.keymap[i] if i < len(self.keymap) else None
            if not key:
                continue

            prev = self.last[i]
            curr = data[i]

            if curr < 10:
                curr = 0

            if prev == curr:
                continue

            msg = Message(
                'note_on' if curr else 'note_off',
                channel=self.channel,
                note=key['note'],
                velocity=clamp(curr, 90, 127),
                time=0
            )
            self.midiout.send(msg)
            self.last[i] = curr

def clamp(n, min, max):
    if n < min:
        return min
    elif n > max:
        return max
    else:
        return n
