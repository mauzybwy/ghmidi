from dataclasses import dataclass, field
import math
import random
import time
import copy

from mido import Message

from .instrument import MidiInstrument

MAJOR_PENTATONIC = [0, 2, 4, 7, 9]
MINOR_PENTATONIC = [0, 3, 5, 7, 10]

DOMINANT_PENTATONIC = [0, 2, 4, 7, 10]
MINOR_6_PENTATONIC = [0, 2, 3, 7, 9]
MAJOR_B6_PENTATONIC = [0, 2, 4, 7, 8]
LYDIAN_PENTATONIC = [0, 2, 4, 6, 9]
PHRYGIAN_PENTATONIC = [0, 1, 5, 7, 10]
WHOLE_TONE_FRAGMENT = [0, 2, 4, 6, 8]
DIMINISHED_SUBSET = [0, 2, 3, 6, 7]

HIRAJOSHI = [0, 2, 3, 7, 8]
KUMOI = [0, 2, 3, 7, 9]
IWATO = [0, 1, 5, 6, 10]
MAN_GONG = [0, 3, 5, 8, 10]
PELOG = [0, 1, 3, 7, 8]

# Device configuration
VID = 0x1209
PID = 0x2882
MIDI_OUTPUT = "IAC Driver Bus 1"

# Guitar configuration
BUTTON_COUNT = 5
BASE_NOTE = 60
NOTE_OFFSETS = MINOR_PENTATONIC
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
    def __init__(self, keymap, channel=0, latch_notes=False):
        super().__init__(keymap, VID, PID, MIDI_OUTPUT)
        self.channel = channel
        self.latch_notes = latch_notes
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
                if not self.latch_notes and not is_pressed:
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
        note = BASE_NOTE + NOTE_OFFSETS[button]
        
        if velocity is None:
            velocity = random.randint(0x40, 0x7F)

        self.midiout.send(
            Message("note_on", channel=self.channel, note=note, velocity=velocity)
        )

    def _note_off(self, button: int):
        self.state.active_buttons.discard(button)
        note = BASE_NOTE + NOTE_OFFSETS[button]
        
        self.midiout.send(Message("note_off", channel=self.channel, note=note))

    def _pitch_bend(self, pitch: int):
        self.midiout.send(Message("pitchwheel", channel=self.channel, pitch=pitch))


def is_bit_set(value: int, bit: int) -> bool:
    return (value & (1 << bit)) != 0
