
LANGUAGES = {
    0: 'XXXX',
    5: 'en-AU',
    6: 'en-US',
    12: 'en-GB',
    13: 'es-US',
    16: 'fr-CA',
    20: 'XXXX',
    24: 'XXXX',
    25: 'XXXX',
}

DEV_LANGUAGES = {
    0: 'en-AU',
    1: 'en-US',
    2: 'en-GB',
    3: 'es-US',
    4: 'fr-CA',
}

PUSH_TO_TALK_PIN_NUMBER = 17
PUSH_TO_TALK_LED = 4


class AbstractPhysicalInterface:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def tick(self):
        pass

    @property
    def is_push_to_talk_button_pressed(self):
        raise NotImplementedError()

    @property
    def language_code(self):
        raise NotImplementedError


class GPIOPhysicalInterface(AbstractPhysicalInterface):
    def __init__(self, gpio, talk_button_pin_number, languages):
        AbstractPhysicalInterface.__init__(self)
        self.gpio = gpio
        self.talk_button_pin_number = talk_button_pin_number
        self.on_language_change = lambda *args: None
        self.selected_pin = 0

    def tick(self):
        selected_pin = next((pin for pin in LANGUAGES.keys() if self.gpio.input(pin) == 0), self.selected_pin)
        if self.selected_pin != selected_pin:
            self.selected_pin = selected_pin
            new_language = LANGUAGES.get(self.selected_pin, LANGUAGES[0])
            self.on_language_change(new_language)

    @property
    def is_push_to_talk_button_pressed(self):
        return not self.gpio.input(self.talk_button_pin_number)

    @property
    def language_code(self):
        return LANGUAGES.get(self.selected_pin, "XX")


class KeyboardPhysicalInterface(AbstractPhysicalInterface):
    def __init__(self, listener, key_module, languages_dev):
        AbstractPhysicalInterface.__init__(self)
        self.languages = languages_dev
        self._shift_key_pressed = False
        self._current_language_code = 0
        self._current_language = DEV_LANGUAGES[0]
        self._listener = listener(on_press=self._on_press, on_release=self._on_release)
        self._key_module = key_module
        self.on_language_change = lambda *args : None

    def __enter__(self):
        self._listener.__enter__()
        return AbstractPhysicalInterface.__enter__(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._listener.__exit__(exc_type, exc_val, exc_tb)

    @property
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


try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    # Button LED
    GPIO.setup(PUSH_TO_TALK_LED, GPIO.OUT)
    GPIO.output(PUSH_TO_TALK_LED, GPIO.HIGH)
    # Button
    GPIO.setup(PUSH_TO_TALK_PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Rotary Switch
    for switch_pin in LANGUAGES.keys():
        GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    PhysicalInterface = GPIOPhysicalInterface(GPIO, PUSH_TO_TALK_PIN_NUMBER, LANGUAGES)
except ImportError:
    from pynput.keyboard import Key, Listener
    PhysicalInterface = KeyboardPhysicalInterface(Listener, Key, DEV_LANGUAGES)
