from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import ConfigReloader
from midi import MidiDrums

# Setup
reloader = ConfigReloader()
observer = Observer()
observer.schedule(reloader, '.', recursive=False)
observer.start()

try:
    with MidiDrums(reloader.keymap) as drums:
        drums.longpoll()
except KeyboardInterrupt:
    observer.stop()

observer.join()
