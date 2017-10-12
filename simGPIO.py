"""
    Simulates the Raspberry Pi GPIO to some degree
    v1.0: spoofs most functions to do nothing
"""

import sys
import math
import Tkinter as tk
import threading


class RepeatingTimer():
    """ A Timer class that does not stop, unless you want it to.
     Used to call repeating functions at defined intervals.
    """

    def __init__(self, seconds, target, args=None, name=''):
        self._should_continue = False
        self.is_running = False
        self.seconds = seconds
        self.target = target
        self.args = args
        self.thread = None
        if name != '':
            self.name = name

    def _handle_target(self):
        self.is_running = True
        if self.args is not None:
            self.target(self.args)
        else:
            self.target()
        self.is_running = False
        self._start_timer()

    def _start_timer(self):
        if self._should_continue:
            self.thread = threading.Timer(self.seconds, self._handle_target)
            # self.thread.setDaemon(True)
            if self.name != '':
                self.thread.name = self.name
            self.thread.start()

    def start(self):
        if not self._should_continue and not self.is_running:
            self._should_continue = True
            self._start_timer()
        else:
            print('Timer already started or running, process must wait')

    def cancel(self):
        if self.thread is not None:
            self._should_continue = False  # Just in case thread is running and cancel failed
            self.thread.cancel()
        else:
            print('Timer never started or failed to initialize')


class GPIO(object):

    board_map = {
        '3.3V PWR1': 1,
        '5V PWR1': 2,
        'I2C1 SDA': 3,
        '5V PWR2': 4,
        'I2C1 SCL': 5,
        'GPIO3': 5,
        'GND4': 6,
        'GPIO4': 7,
        'UART0 TX': 8,
        'GPIO14': 8,
        'GND1': 9,
        'UART0 RX': 10,
        'GPIO15': 10,
        'GPIO17': 11,
        'GPIO18': 12,
        'GPIO27': 13,
        'GND5': 14,
        'GPIO22': 15,
        'GPIO23': 16,
        '3.3V PWR2': 17,
        'GPIO24': 18,
        'SPI0 MOSI': 19,
        'GPIO10': 19,
        'GND6': 20,
        'SPI0 MISO': 21,
        'GPIO9': 21,
        'GPIO25': 22,
        'SPI0 SCLK': 23,
        'GPIO11': 23,
        'SPI0 CS0': 24,
        'GPIO8': 24,
        'GND2': 25,
        'SPI0 CS1': 26,
        'GPIO7': 26,
        'ID_SD': 27,
        'GPIO0': 27,
        'ID_SC': 28,
        'GPIO1': 28,
        'GPIO5': 29,
        'GND7': 30,
        'GPIO6': 31,
        'GPIO12': 32,
        'GPIO13': 33,
        'GND8': 34,
        'GPIO19': 35,
        'GPIO16': 36,
        'GPIO26': 37,
        'GPIO20': 38,
        'GND3': 39,
        'GPIO21': 40
    }

    BCM = 1
    BOARD = 0
    # setup config types
    IN = 0
    OUT = 1
    # states
    HIGH = 1
    LOW = 0
    FALLING = 0
    RISING = 1
    BOTH = 2
    PUD_DOWN = 0
    PUD_UP = 1

    class Display(threading.Thread):

        def __init__(self, labels):
            threading.Thread.__init__(self)
            self.setDaemon(True)
            self.labels = labels
            self.window = tk.Toplevel()
            self.start()

        def quit(self):
            self.window.quit()

        def run(self):
            self.window.protocol("WM_DELETE_WINDOW", self.quit)
            self.window.title('RPi GPIO')
            self.window.geometry('200x450+30+30')
            for key, val in self.labels.iteritems():
                if val % 2 == 0:
                    c = 1
                else:
                    c = 0
                r = int(math.ceil(float(val / 2.0))) - 1
                fore = 'white'
                back = 'black'
                if 'GPIO' in key:
                    fore = 'white'
                    back = 'orange'
                elif 'GND' in key:
                    fore = 'white'
                    back = 'black'
                elif 'RES' in key:
                    fore = 'red'
                    back = 'grey'
                elif 'UART' in key:
                    fore = 'black'
                    back = 'green'
                elif 'SPI' in key:
                    fore = 'white'
                    back = 'magenta'
                elif '3.3V' in key:
                    fore = 'black'
                    back = 'yellow'
                elif '5V' in key:
                    fore = 'white'
                    back = 'red'
                elif 'I2C' in key:
                    fore = 'black'
                    back = 'cyan'
                tk.Label(self.window, text=key, width=10, bg=back, fg=fore, relief='ridge').grid(row=r, column=c)
            self.window.mainloop()

    def __init__(self):
        self.mode = 'BCM'
        self.config = []
        self.events = []
        self.threads = []
        self.root = tk.Tk()
        self.root.withdraw()

    def display(self):
        self.Display(self.board_map)

    def setmode(self, mode):
        if mode == self.BCM:
            self.mode = 'BCM'
        elif mode == self.BOARD:
            self.mode = 'BOARD'
        else:
            errMsg = 'Please use GPIO.setmode(GPIO.BCM) or GPIO.setmode(GPIO.BOARD)'
            sys.exit(errMsg)

    def setup(self, pins, config, initial=None, pull_up_down=None):
        if config == self.OUT:
            if isinstance(pins, list):
                for item in pins:
                    pin = self.getpin(item)
                    self.config.append({"pin": pin, "config": self.OUT, "value": initial})
            else:
                pin = self.getpin(pins)
                self.config.append({"pin": pin, "config": self.OUT, "value": initial})
        elif config == self.IN:
            if isinstance(pins, list):
                for item in pins:
                    pin = self.getpin(item)
                    self.config.append({"pin": pin, "config": self.IN, "value": pull_up_down})
            else:
                pin = self.getpin(pins)
                self.config.append({"pin": pin, "config": self.IN, "value": pull_up_down})
        else:
            errMsg = 'Invalid setup. Please use GPIO.setup(channel, GPIO.IN) or GPIO.setup(channel, GPIO.OUT)'
            sys.exit(errMsg)

    def getpin(self, pinref):
        pin = pinref
        if self.mode == 'BCM':
            pinname = 'GPIO' + str(pinref)
            pin = self.board_map[pinname]
        return pin

    def getchannel(self, pinref):
        channel = 99  # unknown
        for key, val in self.board_map.iteritems():
            if val == pinref and key.startswith("GPIO"):
                channel = key.strip("GPIO")
        return channel

    def input(self, channel):
        pin = self.getpin(channel)
        match = next((l for l in self.config if l['pin'] == pin), None)
        if match is not None and match['config'] == self.IN:
            return match['value']

    def add_event_detect(self, channel, config, callback):
        pin = self.getpin(channel)
        match = next((l for l in self.config if l['pin'] == pin), None)
        if match is not None and match['config'] == self.IN:
            if config == self.RISING or config == self.FALLING or config == BOTH:
                mon = RepeatingTimer(0.1, target=self.check_event, args=pin, name="monitor_"+str(pin))
                self.threads.append(mon)
                mon.start()
                self.events.append({'pin': pin, 'config': config, 'value': match['value'], 'callback': callback})

    def check_event(self, pin):
        match_old = next((l for l in self.events if l['pin'] == pin), None)
        oldValue = match_old['value']
        condition = match_old['config']
        callback = match_old['callback']
        match_new = next((l for l in self.config if l['pin'] == pin), None)
        newValue = match_new['value']
        if (condition == self.RISING and oldValue == self.LOW and newValue == self.HIGH) or \
                (condition == self.FALLING and oldValue == self.HIGH and newValue == self.LOW) or \
                (condition == self.BOTH and oldValue != newValue):
            callback(self.getchannel(pin))
        match_old['value'] = newValue

    # TODO: return an object that allows something to be modulated using start and stop functions
    def PWM(self, pin, frequency):
        print("PWM is an unsupported simulation function")

    def output(self, channel, state):
        pin = self.getpin(channel)
        match = next((l for l in self.config if l['pin'] == pin), None)
        if match is not None and match['config'] == self.OUT:
            match['value'] = state

    def cleanup(self, channel=None):
        for t in self.threads:
            print("Cancelling " + t.name)
            t.cancel()


if __name__ == "__main__":
    simGPIO = GPIO()
    simGPIO.display()