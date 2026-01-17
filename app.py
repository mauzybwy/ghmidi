from midi import MidiDrums, MidiGuitar
import threading

def guitar_task():
    with MidiGuitar(
            channel=0,
            root="C3",
            scale="minor",
            midi_bus="IAC Driver Bus 1"
    ) as guitar:
        while True:
            guitar.poll()

def drums_task():
    with MidiDrums(
            midi_bus="IAC Driver Bus 2"
    ) as drums:
        while True:
            drums.poll()
                
guitar_thread = threading.Thread(target=guitar_task)
guitar_thread.start()

drums_thread = threading.Thread(target=drums_task)
drums_thread.start()

