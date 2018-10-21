
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
    def __init__(self, gpio, talk_button_pin_number, languages):
        AbstractPhysicalInterface.__init__(self)
        self.gpio = gpio
        self.languages = languages
        self.talk_button_pin_number = talk_button_pin_number
        self.on_language_change = lambda *args : None

    def is_push_to_talk_button_pressed(self):
        return not self.gpio.input(self.talk_button_pin_number)

    @property
    def language_code(self):
        selected_pin = 0
        for switch_pin in self.languages.keys():
            input_state = GPIO.input(switch_pin)
            selected_pin = selected_pin if input_state else switch_pin

        new_language = self.languages.get(selected_pin, "XX")
        self.on_language_change(new_language)
        return new_language


class KeyboardPhysicalInterface(AbstractPhysicalInterface):
    def __init__(self, listener, key_module, languages_dev):
        AbstractPhysicalInterface.__init__(self)
        self.languages = languages_dev
        self._shift_key_pressed = False
        self._current_language_code = 0
        self._current_language = "EN"
        self._listener = listener(on_press=self._on_press, on_release=self._on_release)
        self._key_module = key_module
        self.on_language_change = lambda *args : None

    def __enter__(self):
        self._listener.__enter__()
        return AbstractPhysicalInterface.__enter__(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._listener.__exit__(exc_type, exc_val, exc_tb)

    def is_push_to_talk_button_pressed(self):
        return self._shift_key_pressed

    @property
    def language_code(self):
        return self._current_language_code

    def _on_press(self, key):
        if key == self._key_module.shift:
            self._shift_key_pressed = True
        elif key == self._key_module.ctrl:
            new_language_code = (self._current_language_code + 1) % 8
            new_language = self.languages.get(new_language_code, "XX")
            self.on_language_change(new_language)
            self._current_language_code = new_language_code
            self._current_language = new_language

    def _on_release(self, key):
        if key == self._key_module.shift:
            self._shift_key_pressed = False


languages = {
    0:"XX",
    5:"FR",
    6:"EN",
    12:"ES",
    13:"DE",
    16:"RU",
    19:"CN",
    20:"TR",
    21:"AR",
}

languages_dev = {
    0:"FR",
    1:"EN",
    2:"ES",
    3:"DE",
    4:"RU",
    5:"CN",
    6:"TR",
    7:"AR",
}

talk_switch_pin_number = 18

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(talk_switch_pin_number, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for switch_pin in switch_languages.keys():
        GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    PhysicalInterface = GPIOPhysicalInterface(GPIO, talk_switch_pin_number, languages)
except ImportError:
    from pynput.keyboard import Key, Listener
    PhysicalInterface = KeyboardPhysicalInterface(Listener, Key, languages_dev)
