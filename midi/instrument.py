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
