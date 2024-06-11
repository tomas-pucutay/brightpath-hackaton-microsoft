from pynput import keyboard

def on_press(key, player, text_handler, *args):
    try:
        if key == keyboard.Key.space:
            player.set_pause(True, text_handler, *args)
        elif key == keyboard.Key.ctrl_l:
            player.set_pause(False, text_handler, *args)
    except AttributeError:
        pass