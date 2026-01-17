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

# Guitar configuration
BUTTON_COUNT = 5
PAD_COUNT = 5
BASE_NOTE = 60
MAX_PITCH_BEND = 8191
STRUM_DEBOUNCE_SECS = 0.05

note_to_midi = {
    'C0': 12, 'C#0': 13, 'D0': 14, 'D#0': 15, 'E0': 16, 'F0': 17, 'F#0': 18, 'G0': 19, 'G#0': 20, 'A0': 21, 'A#0': 22, 'B0': 23,
    'C1': 24, 'C#1': 25, 'D1': 26, 'D#1': 27, 'E1': 28, 'F1': 29, 'F#1': 30, 'G1': 31, 'G#1': 32, 'A1': 33, 'A#1': 34, 'B1': 35,
    'C2': 36, 'C#2': 37, 'D2': 38, 'D#2': 39, 'E2': 40, 'F2': 41, 'F#2': 42, 'G2': 43, 'G#2': 44, 'A2': 45, 'A#2': 46, 'B2': 47,
    'C3': 48, 'C#3': 49, 'D3': 50, 'D#3': 51, 'E3': 52, 'F3': 53, 'F#3': 54, 'G3': 55, 'G#3': 56, 'A3': 57, 'A#3': 58, 'B3': 59,
    'C4': 60, 'C#4': 61, 'D4': 62, 'D#4': 63, 'E4': 64, 'F4': 65, 'F#4': 66, 'G4': 67, 'G#4': 68, 'A4': 69, 'A#4': 70, 'B4': 71,
    'C5': 72, 'C#5': 73, 'D5': 74, 'D#5': 75, 'E5': 76, 'F5': 77, 'F#5': 78, 'G5': 79, 'G#5': 80, 'A5': 81, 'A#5': 82, 'B5': 83,
    'C6': 84, 'C#6': 85, 'D6': 86, 'D#6': 87, 'E6': 88, 'F6': 89, 'F#6': 90, 'G6': 91, 'G#6': 92, 'A6': 93, 'A#6': 94, 'B6': 95,
    'C7': 96, 'C#7': 97, 'D7': 98, 'D#7': 99, 'E7': 100, 'F7': 101, 'F#7': 102, 'G7': 103, 'G#7': 104, 'A7': 105, 'A#7': 106, 'B7': 107,
    'C8': 108, 'C#8': 109, 'D8': 110, 'D#8': 111, 'E8': 112, 'F8': 113, 'F#8': 114, 'G8': 115, 'G#8': 116, 'A8': 117, 'A#8': 118, 'B8': 119,
}

pentatonic_scales = {
    'major': [0, 2, 4, 7, 9],
    'minor': [0, 3, 5, 7, 10],
    'dominant': [0, 2, 4, 7, 10],
    'minor_6': [0, 2, 3, 7, 9],
    'major_b6': [0, 2, 4, 7, 8],
    'lydian': [0, 2, 4, 6, 9],
    'phrygian': [0, 1, 5, 7, 10],
    'whole_tone_fragment': [0, 2, 4, 6, 8],
    'diminished_subset': [0, 2, 3, 6, 7],
    'hirajoshi': [0, 2, 3, 7, 8],
    'kumoi': [0, 2, 3, 7, 9],
    'iwato': [0, 1, 5, 6, 10],
    'man_gong': [0, 3, 5, 8, 10],
    'pelog': [0, 1, 3, 7, 8],
}

# Whammy bar thresholds
WHAMMY_FULL_BEND = 0xC0
WHAMMY_PARTIAL_START = 0x90
WHAMMY_RANGE = 0x30

# Strum bar neutral position
STRUM_NEUTRAL = 8

@dataclass
class GuitarState:
    buttons: list[bool] = field(default_factory=lambda: [False] * (BUTTON_COUNT * PAD_COUNT))
    active_buttons: set[int] = field(default_factory=set)
    strum_tick: float = 0.0
    strumming: bool = False
    pitch_position: int = 0

    @property
    def max_active_button(self) -> int:
        if not self.active_buttons:
            return 0xffff
        return max(self.active_buttons)

    @property
    def has_active_buttons(self) -> int:
        return len(self.active_buttons) > 0

class MidiGuitar(MidiInstrument):
    def __init__(
            self,
            channel=0,
            latch_notes=False,
            scale='major',
            root='C3',
            midi_bus="IAC Driver Bus 1"
    ):
        super().__init__(VID, PID, midi_bus)
        self.channel = channel
        self.latch_notes = latch_notes
        self.state = GuitarState()
        self.note_offsets = pentatonic_scales[scale] 

    def _poll(self):
        data = self.device.read(64)
        if not data:
            return

        tick = time.time()
        buttons = self._read_buttons(data)
        strummed = self._update_strum_state(data, tick)

        self._process_notes(buttons, strummed)
        self._process_whammy(data)

        self.state.buttons = buttons

    def _read_buttons(self, data: bytes) -> list[bool]:
        return [is_bit_set(data[1], i) for i in range(BUTTON_COUNT)] + [is_pad_set(data[5], i) for i in range(PAD_COUNT)]

    def _update_strum_state(self, data: bytes, tick: float) -> bool:
        strum_value = data[3]
        was_strumming = self.state.strumming

        if strum_value == STRUM_NEUTRAL:
            if self._is_strum_debounced(tick):
                self.state.strumming = False
            return False

        if not was_strumming:
            self.state.strum_tick = tick
            self.state.strumming = True
            return True

        return False

    def _process_notes(self, buttons: list[bool], strummed: bool):
        for i, is_pressed in enumerate(buttons):
            was_pressed = self.state.buttons[i]
            was_active = i in self.state.active_buttons

            if strummed:
                if was_pressed and is_pressed:
                    self._note_off(i)

                if is_pressed:
                    self._note_on(i)
                else:
                    self._note_off(i) 
            else:
                if not is_pressed:
                    self._note_off(i)
                if is_pressed and self.state.has_active_buttons:
                    self._try_hammer_on(i)
                if not is_pressed and was_active:
                    self._try_pull_off(i)
                

    def _try_hammer_on(self, button: int):
        if button > self.state.max_active_button:
            self._note_off(self.state.max_active_button)
            self._note_on(button)

    def _try_pull_off(self, button: int):
        for i in range(button -1, -1, -1):
            if self.state.buttons[i] and  i not in self.state.active_buttons:
                self._note_on(i)
                break

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

    def _note_on(self, button: int, velocity: int | None = None):
        self.state.active_buttons.add(button)
        note = self._calc_note(button)
        
        if velocity is None:
            velocity = random.randint(0x60, 0x7F)

        self.midiout.send(
            Message("note_on", channel=self.channel, note=note, velocity=velocity)
        )

    def _note_off(self, button: int):
        self.state.active_buttons.discard(button)

        if not self.latch_notes:
            note = self._calc_note(button)
            self.midiout.send(Message("note_off", channel=self.channel, note=note))

    def _pitch_bend(self, pitch: int):
        self.midiout.send(Message("pitchwheel", channel=self.channel, pitch=pitch))

    def _calc_note(self, button: int):
        return BASE_NOTE + self.note_offsets[button % BUTTON_COUNT] + (math.floor(button / BUTTON_COUNT) * 12)


def is_bit_set(value: int, bit: int) -> bool:
    return (value & (1 << bit)) != 0

def is_pad_set(value: int, pad: int) -> bool:
    match (pad, value):
        case (0, 0x15 | 0x30): return True
        case (1, 0x30 | 0x4d | 0x66): return True
        case (2, 0x66 | 0x9a | 0xaf): return True
        case (3, 0xaf | 0xc9 | 0xe6): return True
        case (4, 0xe6 | 0xff): return True
        case _: return False
