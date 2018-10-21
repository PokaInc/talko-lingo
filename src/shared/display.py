
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


try:
    from Adafruit_LED_Backpack import AlphaNum4

    Display = None
except ImportError:
    Display = TerminalDisplay



#
# from Adafruit_LED_Backpack import AlphaNum4
#
# # Create display instance on default I2C address (0x70) and bus number.
# from Adafruit_LED_Backpack import AlphaNum4
# display = AlphaNum4.AlphaNum4()
#
# # Initialize the display. Must be called once before using the display.
# display.begin()
#
# # Scroll a message across the display
# message = 'This is an example of the 4 character alpha-numeric display. THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG? ' \
#           'the quick brown fox jumps over the lazy dog!'
# pos = 0
# print('Press Ctrl-C to quit.')
# while True:
#     # Clear the display buffer.
#     display.clear()
#     # Print a 4 character string to the display buffer.
#     display.print_str(message[pos:pos + 4])
#     # Write the display buffer to the hardware.  This must be called to
#     # update the actual display LEDs.
#     display.write_display()
#     # Increment position. Wrap back to 0 when the end is reached.
#     pos += 1
#     if pos > len(message) - 4:
#         pos = 0
#     # Delay for half a second.
#     time.sleep(0.5)
