
class AbstractPhysicalInterface:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def is_push_to_talk_button_pressed(self):
        raise NotImplementedError()


class GPIOPhysicalInterface(AbstractPhysicalInterface):
    def __init__(self, gpio):
        AbstractPhysicalInterface.__init__(self)
        self.gpio = gpio

    def is_push_to_talk_button_pressed(self):
        return not self.gpio.input(18)


class KeyboardPhysicalInterface(AbstractPhysicalInterface):
    def __init__(self, listener, key_module):
        AbstractPhysicalInterface.__init__(self)
        self._shift_key_pressed = False
        self._listener = listener(on_press=self._on_press, on_release=self._on_release)
        self._key_module = key_module

    def __enter__(self):
        self._listener.__enter__()
        return AbstractPhysicalInterface.__enter__(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._listener.__exit__(exc_type, exc_val, exc_tb)

    def is_push_to_talk_button_pressed(self):
        return self._shift_key_pressed

    def _on_press(self, key):
        if key == self._key_module.shift:
            self._shift_key_pressed = True

    def _on_release(self, key):
        if key == self._key_module.shift:
            self._shift_key_pressed = False


try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    PhysicalInterface = GPIOPhysicalInterface(GPIO)
except ImportError:
    from pynput.keyboard import Key, Listener
    PhysicalInterface = KeyboardPhysicalInterface(Listener, Key)
