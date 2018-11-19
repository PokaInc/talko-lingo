
class AbstractDisplay:

    def __init__(self):
        pass

    def show(self, message):
        raise NotImplementedError()


class TerminalDisplay(AbstractDisplay):

    def __init__(self):
        AbstractDisplay.__init__(self)
        from art import tprint
        self.print_function = tprint

    def show(self, message):
        assert len(message) == 4
        self.print_function(message[:2] + ' ' + message[2:])


class LedDisplay(AbstractDisplay):

    def __init__(self):
        AbstractDisplay.__init__(self)
        from Adafruit_LED_Backpack import AlphaNum4
        self.alphanum_display = AlphaNum4.AlphaNum4()
        self.alphanum_display.begin()

    def show(self, message):
        message = self._format_message(message)
        assert len(message) <= 4
        self.alphanum_display.clear()
        self.alphanum_display.print_str()
        self.alphanum_display.write_display()

    @staticmethod
    def _format_message(message):
        return message.replace('-', '').upper()


try:
    from Adafruit_LED_Backpack import AlphaNum4

    Display = LedDisplay
except ImportError:
    Display = TerminalDisplay


