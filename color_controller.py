from bulb_actions import set_rgb
from ui_helpers import move_white_point, update_rgb_values

def apply_color_change(color, canvas, marker, red_input, green_input, blue_input):
                set_rgb(color) # Send the color to the bulb
                move_white_point(canvas,marker)
                update_rgb_values(red_input,green_input,blue_input,color[0], color[1], color[2])
