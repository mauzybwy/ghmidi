from dataclasses import dataclass, field
import math
import random
import time
import copy

from mido import Message

from .instrument import MidiInstrument

# Device configuration
VID = 0x1209
PID = 0x2882
MIDI_OUTPUT = "IAC Driver Bus 1"

# Guitar configuration
BUTTON_COUNT = 5
BASE_NOTE = 60
NOTE_INTERVAL = 2
MAX_PITCH_BEND = 8191
STRUM_DEBOUNCE_SECS = 0.05

# Whammy bar thresholds
WHAMMY_FULL_BEND = 0xC0
WHAMMY_PARTIAL_START = 0x90
WHAMMY_RANGE = 0x30

# Strum bar neutral position
STRUM_NEUTRAL = 8

@dataclass
class GuitarState:
    buttons: list[bool] = field(default_factory=lambda: [False] * BUTTON_COUNT)
    strum_tick: float = 0.0
    strumming: bool = False
    pitch_position: int = 0

class MidiGuitar(MidiInstrument):
    def __init__(self, keymap):
        super().__init__(keymap, VID, PID, MIDI_OUTPUT)
        self.channel = 0
        self.latch_notes = False
        self.state = GuitarState()

    def _poll(self):
        data = self.device.read(64)
        if not data:
            return

        prev_state = copy.deepcopy(self.state) 
        tick = time.time()
        buttons = self._read_buttons(data)
        strummed = self._update_strum_state(data, tick)

        self._process_notes(buttons, strummed)
        self._process_whammy(data)

        self.state.buttons = buttons

        if self.state != prev_state:
            print(self.state)

    def _read_buttons(self, data: bytes) -> list[bool]:
        return [is_bit_set(data[1], i) for i in range(BUTTON_COUNT)]

    def _update_strum_state(self, data: bytes, tick: float) -> bool:
        strum_value = data[3]
        was_strumming = self.state.strumming

        if strum_value == STRUM_NEUTRAL:
            if self._is_strum_debounced(tick):
                self.state.strumming = False
            return False

        if not was_strumming:
            self.state.strum_tick = tick
            return True

        return False

    def _process_notes(self, buttons: list[bool], strummed: bool):
        for i, is_pressed in enumerate(buttons):
            note = BASE_NOTE + i * NOTE_INTERVAL
            was_pressed = self.state.buttons[i]

            if strummed:
                if was_pressed and is_pressed:
                    self._note_off(note)
                if is_pressed:
                    self._note_on(note)
                else:
                    self._note_off(note)
            elif not self.latch_notes and not is_pressed:
                self._note_off(note)

    def _process_whammy(self, data: bytes):
        whammy = data[4]
        pitch = self._whammy_to_pitch(whammy)

        if pitch != self.state.pitch_position:
            self._pitch_bend(pitch)
            self.state.pitch_position = pitch

    def _whammy_to_pitch(self, whammy: int) -> int:
        if whammy > WHAMMY_FULL_BEND:
            return -MAX_PITCH_BEND

        if whammy > WHAMMY_PARTIAL_START:
            ratio = (whammy - WHAMMY_PARTIAL_START) / WHAMMY_RANGE
            return math.floor(ratio * -MAX_PITCH_BEND)

        return 0

    def _is_strum_debounced(self, tick: float) -> bool:
        return tick - self.state.strum_tick > STRUM_DEBOUNCE_SECS

    def _note_on(self, note: int, velocity: int | None = None):
        if velocity is None:
            velocity = random.randint(0x40, 0x7F)

        self.midiout.send(
            Message("note_on", channel=self.channel, note=note, velocity=velocity)
        )

    def _note_off(self, note: int):
        self.midiout.send(Message("note_off", channel=self.channel, note=note))

    def _pitch_bend(self, pitch: int):
        self.midiout.send(Message("pitchwheel", channel=self.channel, pitch=pitch))


def is_bit_set(value: int, bit: int) -> bool:
    return (value & (1 << bit)) != 0
