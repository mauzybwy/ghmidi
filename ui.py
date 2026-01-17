# RAW DUMP FROM APP

dpg.create_context()
dpg.create_viewport(title="GH MIDI")

# Define unique colors for each button (RGB without alpha)
BUTTON_COLORS = [
    (0, 255, 0),      # Green
    (255, 0, 0),      # Red
    (255, 255, 0),    # Yellow
    (0, 0, 255),      # Blue
    (255, 127, 0),    # Orange
    (0, 255, 0),      # Green
    (255, 0, 0),      # Red
    (255, 255, 0),    # Yellow
    (0, 0, 255),      # Blue
    (255, 127, 0),    # Orange
]

BTN_RADIUS = 20
BTN_STROKE = 4

with dpg.window(label="MIDI Settings", tag="midi") as midi_window:
    dpg.set_item_pos(midi_window, (0, 140))
    dpg.set_item_width(midi_window, 300)
    dpg.add_combo(["Channel 0", "Channel 1"], label="MIDI Channel", default_value="Channel 0")

with dpg.value_registry(tag="guitar_value_registry"):
    for i in range(10):
        dpg.add_string_value(default_value="OFF", tag=f"btn_{i}")

with dpg.window(label="Guitar State", tag="main") as primary_window:
    dpg.set_item_height(primary_window, 140)
    dpg.set_item_width(primary_window, (BTN_RADIUS + BTN_STROKE) * 21)
    for i, tag in enumerate(dpg.get_item_children("guitar_value_registry", slot=1)):
        r, g, b = BUTTON_COLORS[i]
        dpg.draw_circle(
            (BTN_RADIUS + i * (BTN_RADIUS * 2 + BTN_STROKE), BTN_RADIUS), BTN_RADIUS,
            color=(r, g, b, 255),
            fill=(0, 0, 0, 255),
            thickness=BTN_STROKE,  # stroke width in pixels
            tag=f"circle_{i}"
        )

    with dpg.group(horizontal=True) as prog:
        dpg.set_item_pos(prog, (8, BTN_RADIUS * 4 + BTN_STROKE))
        dpg.add_text("Whammy:")
        dpg.add_progress_bar(default_value=0, overlay="0%", tag="whammy")
    

def update_display_state(state):
    for i, is_pressed in enumerate(state.buttons):
        is_active = i in state.active_buttons
        
        status = "RING" if is_active else "PRESS" if is_pressed else "OFF"
        dpg.set_value(f"btn_{i}", status)
        
        # Update circle fill based on state
        r, g, b = BUTTON_COLORS[i]
        if is_active:  # RING - full opacity
            fill = (r, g, b, 255 if state.strumming else 220)
        elif is_pressed:  # PRESS - half opacity
            fill = (r, g, b, 127)
        else:  # OFF
            fill=(0, 0, 0, 255),  # Start with no fill (OFF state)
        
        dpg.configure_item(f"circle_{i}", fill=fill)

        whammy = abs(state.pitch_position / 8191)
        dpg.set_value("whammy", whammy)
        dpg.configure_item("whammy", overlay=f"{math.floor(whammy * 100)}%")
