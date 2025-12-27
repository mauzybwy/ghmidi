import hid
import mido
from mido import Message
import time
import math
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_PATH = 'config.yaml'

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

class ConfigReloader(FileSystemEventHandler):
    def __init__(self):
        self.keymap = load_config()
    
    def on_modified(self, event):
        if event.src_path.endswith(CONFIG_PATH):
            try:
                self.keymap = load_config()
                print("Config reloaded!")
            except Exception as e:
                print(f"Config reload failed: {e}")

# Setup
device = hid.device()
device.open(0x1209, 0x2882)
device.set_nonblocking(False)

midiout = mido.open_output('IAC Driver Bus 1')

reloader = ConfigReloader()
observer = Observer()
observer.schedule(reloader, '.', recursive=False)
observer.start()

print("Hit different pads/buttons... (edit config.yaml to remap live)")

last = [0] * 10

try:
    while True:
        data = device.read(64)
        if not data:
            continue

        for i, b in enumerate(data):
            key = reloader.keymap[i] if i < len(reloader.keymap) else None
            if not key:
                continue
            
            prev = last[i]
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
            midiout.send(msg)
            last[i] = curr

except KeyboardInterrupt:
    observer.stop()

observer.join()
