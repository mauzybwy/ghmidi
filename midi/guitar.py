from mido import Message
from .instrument import MidiInstrument
import math
import time

VID = 0x1209
PID = 0x2882
MIDI_OUTPUT = 'IAC Driver Bus 1' 

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

BUTTON_COUNT = 5
TAP_PAD_COUNT = 5
LEGATO_DEBOUNCE = 1.0
CHORD_DEBOUNCE = 0.25
STRUM_DEBOUNCE = 0.05

class MidiGuitar(MidiInstrument):
    def __init__(self, keymap):
        super().__init__(keymap, VID, PID, MIDI_OUTPUT)
        self.buttons = [None] * BUTTON_COUNT
        self.strum_tick = 0.0
    
    def _poll(self):        
        data = self.device.read(64)
        
        if not data: return 

        tick = time.time()
        buttons = [None] * BUTTON_COUNT
        strum = False

        print(list(map(hex, data)))

        for i in range(5): 
            buttons[i] = is_bit_set(data[1], i)

        strummed = False
        legato = self.is_legato(tick)
        if data[3] != 8 and self.is_strum(tick):
            self.strum_tick = tick
            strummed = True

        for i, nxt in enumerate(buttons):
            curr = self.buttons[i]
            
            if not strummed:
                continue

            note = 60 + i * 2
            channel = 0

            if strummed and nxt == curr and nxt == True:
                msg = Message(
                    'note_off',
                    channel=channel,
                    note=note
                )
                self.midiout.send(msg)

            msg = Message(
                'note_on' if nxt else 'note_off',
                channel=channel,
                note=note,
                velocity=0x7f,
            )
            self.midiout.send(msg)

        print(buttons, self.strum_tick, legato)
        self.buttons = buttons

        # for i, b in enumerate(data):
        #     key = self.keymap[i] if i < len(self.keymap) else None
        #     if not key:
        #         continue
        # 
        #     prev = self.last[i]
        #     curr = data[i]
        # 
        #     if curr < 10:
        #         curr = 0
        # 
        #     if prev == curr:
        #         continue
        # 
        #     msg = Message(
        #         'note_on' if curr else 'note_off',
        #         channel=0,
        #         note=key['note'],
        #         velocity=math.floor(curr / 2),
        #         time=0
        #     )
        #     self.midiout.send(msg)
        #     self.last[i] = curr


    def is_legato(self, tick):
        return tick - self.strum_tick < LEGATO_DEBOUNCE

    def is_chord(self, tick):
        return tick - self.strum_tick > CHORD_DEBOUNCE

    def is_strum(self, tick):
        return tick - self.strum_tick > STRUM_DEBOUNCE


def is_bit_set(n, k):
  return (n & (1 << k)) != 0
