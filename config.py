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
