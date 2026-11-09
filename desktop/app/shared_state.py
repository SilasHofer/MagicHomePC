bulb = None
current_device_info = None
current_ip = None  # IP of the bulb in shared_state.bulb, so windows can show the same device
system_change = False
# Full-brightness color (R, G, B in UI order) that the brightness slider scales.
# Kept here so repeated slider moves never lose the color's ratio.
base_color = None
canvas_size = 200
point_size = 7
is_connected = True