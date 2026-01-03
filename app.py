from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import ConfigReloader
from midi import MidiDrums, MidiGuitar
import dearpygui.dearpygui as dpg

# Setup
reloader = ConfigReloader()
observer = Observer()
observer.schedule(reloader, '.', recursive=False)
observer.start()

# dpg.create_context()
# dpg.create_viewport(title="GH MIDI")
# 
# with dpg.window(label="Controls", tag="main"):
#     dpg.add_text("Button States:")
#     for i in range(8):
#         dpg.add_text(f"Button {i}: OFF", tag=f"btn_{i}")
# 
#     dpg.add_separator()
#     dpg.add_text("Settings")
#     dpg.add_combo(["Channel 1", "Channel 2"], label="MIDI Channel", default_value="Channel 1")
# 
# def update_button(index, pressed):
#     state = "ON" if pressed else "OFF"
#     dpg.set_value(f"btn_{index}", f"Button {index}: {state}")
# 
# dpg.setup_dearpygui()
# dpg.show_viewport()

try:
    with MidiGuitar(reloader.keymap) as guitar:
        # while dpg.is_dearpygui_running():
        #     dpg.render_dearpygui_frame()
        while True:
            # drums.poll()
           guitar.poll() 
            
except KeyboardInterrupt:
    observer.stop()
    # dpg.destroy_context()

observer.join()
