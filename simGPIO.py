"""
    Simulates the Raspberry Pi GPIO to some degree
    v1.0: spoofs most functions to do nothing
"""

import sys
import math
import Tkinter as tk

class GPIO(object):

    board_map = {
        '3.3V PWR1': 1,
        'I2C1 SDA': 3,
        'I2C1 SCL': 5,
        'GPIO4': 7,
        'GND1': 9,
        'GPIO17': 11,
        'GPIO27': 13,
        'GPIO22': 15,
        '3.3V PWR2': 17,
        'SPI0 MOSI': 19,
        'SPI0 MISO': 21,
        'SPI0 SCLK': 23,
        'GND2': 25,
        'RES1': 27,     # ID_SD
        'GPIO5': 29,
        'GPIO6': 31,
        'GPIO13': 33,
        'GPIO19': 35,
        'GPIO26': 37,
        'GND3': 39,
        '5V PWR1': 2,
        '5V PWR2': 4,
        'GND4': 6,
        'UART0 TX': 8,
        'UART0 RX': 10,
        'GPIO18': 12,
        'GND5': 14,
        'GPIO23': 16,
        'GPIO24': 18,
        'GND6': 20,
        'GPIO25': 22,
        'SPI0 CS0': 24,
        'SPI0 CS1': 26,
        'RES2': 28,    # ID_SC
        'GND7': 30,
        'GPIO12': 32,
        'GND8': 34,
        'GPIO16': 36,
        'GPIO20': 38,
        'GPIO21': 40
    }

    def __init__(self):
        self.mode = 'BCM'
        self.config = []

    def display(self):
        GUI = tk.Tk()
        GUI.title('RPi GPIO')
        GUI.geometry('200x450+30+30')
        for key, val in self.board_map.iteritems():
            if val % 2 == 0:
                c = 1
            else:
                c = 0
            r = int(math.ceil(float(val/2.0))) - 1
            fore = 'white'
            if 'GPIO' in key:
                back = 'orange'
            elif 'GND' in key:
                back = 'black'
            elif 'RES' in key:
                back = 'grey'
                fore = 'red'
            elif 'UART' in key:
                back = 'green'
                fore = 'black'
            elif 'SPI' in key:
                back = 'magenta'
            elif '3.3V' in key:
                back = 'yellow'
                fore = 'black'
            elif '5V' in key:
                back = 'red'
            elif 'I2C' in key:
                back = 'cyan'
                fore = 'black'
            tk.Label(GUI, text=key, width=10, bg=back, fg=fore, relief='ridge').grid(row=r, column=c)
        GUI.mainloop()

    def setmode(self, mode):
        if mode == self.BCM:
            self.mode = 'BCM'
        elif mode == self.BOARD:
            self.mode = 'BOARD'
        else:
            errMsg = 'Please use GPIO.setmode(GPIO.BCM) or GPIO.setmode(GPIO.BOARD)'
            sys.exit(errMsg)

    def setup(self, pin, config, initial=None, pull_up_down=None):
        if config in [self.IN, self.OUT]:
            if self.mode == 'BOARD':
                pass # TODO: remap pin numbering
            # TODO: stuff...
        else:
            errMsg = 'Plase use GPIO.setup(channel, GPIO.IN) or GPIO.setup(channel, GPIO.OUT)'
            sys.exit(errMsg)

    def BCM(self):
        return True

    def BOARD(self):
        return True

    def IN(self):
        return True

    def input(self, channel):
        return True

    def add_event_detect(self, pin, config, callback):
        # TODO: daemon thread that picks up the Fishdish button_press and triggers the callback function
        return True

    def RISING(self):
        return True

    def FALLING(self):
        return True

    def OUT(self):
        return True

    def LOW(self):
        return 0

    def HIGH(self):
        return 1

    def PUD_DOWN(self):
        return True

    def PUD_UP(self):
        return True

    # TODO: return an object that allows something to be modulated using start and stop functions
    def PWM(self, pin, frequency):
        return True

    def output(self, channel, state):
        return True

    def cleanup(self, channel=None):
        return True


class CircleButton(tk.Canvas):
    def __init__(self, parent, width, height, color, command=None):
        tk.Canvas.__init__(self, parent, borderwidth=1,
                           relief="raised", highlightthickness=0)
        self.command = command

        padding = 4
        self.create_oval((padding, padding, width + padding, height + padding), outline=color, fill=color)
        (x0, y0, x1, y1) = self.bbox("all")
        width = (x1 - x0) + padding
        height = (y1 - y0) + padding
        self.configure(width=width, height=height)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self.configure(relief="sunken")

    def _on_release(self, event):
        self.configure(relief="raised")
        if self.command is not None:
            self.command()


class FishDish(object):
    def __init__(self, GPIO):
        self.LED_GRN = False
        self.LED_YEL = False
        self.LED_RED = False
        self.BUZZER = False
        self.BUTTON = False
        self.GPIO = GPIO

    def display(self):
        GUI = tk.Tk()
        GUI.title('Fish Dish')
        tk.Label(GUI, width=10, bg='green', relief='ridge').pack()
        tk.Label(GUI, width=10, bg='yellow', relief='ridge').pack()
        tk.Label(GUI, width=10, bg='red', relief='ridge').pack()
        tk.Label(GUI, width=10, bg='black', relief='ridge').pack()
        CircleButton(parent=GUI, width=10, height=10, color='black').pack()
        GUI.mainloop()

    def button_press(self):
        # TODO: return an event to the add_event_detect
        pass


if __name__ == "__main__":
    simGPIO = GPIO()
    # simGPIO.display()
    fd = FishDish(simGPIO)
    fd.display()
