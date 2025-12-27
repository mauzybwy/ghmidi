import hid
import mido
from mido import Message
import math
import time

VID = 0x1209
PID = 0x2882
MIDI_OUTPUT = 'IAC Driver Bus 1' 

class MidiDrums:
    def __init__(self, keymap):
        self.keymap = keymap
        self.device = None
        self.midiout = None
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

        self.midiout = mido.open_output(MIDI_OUTPUT)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.device:
            self.device.close()
        if self.midiout:
            self.midiout.close()

    def longpoll(self):
        while True:
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
        self.device.open(VID, PID)
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
