from mido import Message
from .instrument import MidiInstrument
import math

VID = 0x1209
PID = 0x2882
MIDI_OUTPUT = 'IAC Driver Bus 1' 

class MidiDrums(MidiInstrument):
    def __init__(self, keymap):
        super().__init__(keymap, VID, PID, MIDI_OUTPUT)
    
    def _poll(self):
        data = self.device.read(64)

        if not data:
            return

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
                channel=0,
                note=key['note'],
                velocity=math.floor(curr / 2),
                time=0
            )
            self.midiout.send(msg)
            self.last[i] = curr
