"""
  Simulates the Fish Dish board with a GUI interface for Windows
"""

import Tkinter as tk
import threading
import simGPIO
from PIL import ImageTk, Image

_debug = False

ON = 1
OFF = 0


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


class CircleButton(tk.Canvas):
    """A circular button widget that calls back on press and release conditions"""

    global button_state

    def __init__(self, parent, width, height, color, bg_color="darkslategray", command_press=None, command_release=None):
        tk.Canvas.__init__(self, parent, borderwidth=1,
                           relief="raised", highlightthickness=0)
        self.command_press = command_press
        self.command_release = command_release
        self.bg_color = bg_color
        padding = 4
        self.create_oval((padding, padding, width + padding, height + padding), outline=color, fill=color)
        (x0, y0, x1, y1) = self.bbox("all")
        width = (x1 - x0) + padding
        height = (y1 - y0) + padding
        self.configure(width=width, height=height, background=self.bg_color)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self.configure(relief="sunken")
        if self.command_press is not None:
            self.command_press()

    def _on_release(self, event):
        self.configure(relief="raised")
        if self.command_release is not None:
            self.command_release()


class CircleIndicator(tk.Canvas):
    """A circular indicator widget that represents on/off states with different colors"""
    def __init__(self, parent, width, height, color_on, color_off, bg_color="gold", name=None):
        if name is not None:
            self.name = name
        self.bg_color = bg_color
        self.color_on = color_on
        self.color_off = color_off
        tk.Canvas.__init__(self, parent, borderwidth=1,
                           relief="flat", highlightthickness=0)
        padding = 4
        self.indicator = self.create_oval((padding, padding, width + padding, height + padding), outline=color_off, fill=color_off)
        (x0, y0, x1, y1) = self.bbox("all")
        width = (x1 - x0) + padding
        height = (y1 - y0) + padding
        self.configure(width=width, height=height, background="gold")

    def set_state(self, state):
        if state == ON:
            if _debug:
                print("Changing color of " + self.name + " to:" + self.color_on)
            self.itemconfig(self.indicator, fill=self.color_on)
        else:
            if _debug:
                print("Changing color of " + self.name + " to:" + self.color_off)
            self.itemconfig(self.indicator, fill=self.color_off)


class FishDish(object):
    """TODO: doc"""

    active_gpio = {
        "LED_GRN": 4,
        "LED_YEL": 22,
        "LED_RED": 9,
        "BUZZER": 8,
        "BUTTON": 7
    }

    def __init__(self, GPIO, button_press_callback=None, button_release_callback=None):
        self.threads = []
        self.GPIO = GPIO
        self.button_press_callback = button_press_callback
        self.button_release_callback = button_release_callback
        self.button_state = 0
        self.root = tk.Tk()
        self.root.withdraw()
        self.GUI = self.Display(button_press_callback=self.button_press,
                                button_release_callback=self.button_release)
        # self.threads.append(self.GUI)
        self.monitor = RepeatingTimer(0.1, target=self.gpio_monitor, name="CheckGPIO")
        self.threads.append(self.monitor)
        self.monitor.start()

    class Display(threading.Thread):
        """A graphical display of the Fish Dish with widgets overlaid"""
        button_size = 15
        buzzer_size = 50
        led_size = 20

        def __init__(self, button_press_callback=None, button_release_callback=None):
            threading.Thread.__init__(self)
            self.name = "FishDishDisplay"
            self.setDaemon(True)
            if button_press_callback is not None:
                self.button_press_callback = button_press_callback
            if button_release_callback is not None:
                self.button_release_callback = button_release_callback
            self.window = tk.Toplevel()
            # assumes the target file is in the current directory
            # source: http://cpc.farnell.com/productimages/standard/en_GB/SC13407-40.jpg
            self.img = ImageTk.PhotoImage(Image.open("fishdish.jpg"))
            self.panel = tk.Label(self.window, image=self.img)
            self.panel.pack(side="bottom", fill="both", expand="yes")
            self.button = CircleButton(parent=self.window, width=self.button_size, height=self.button_size,
                                       color='black',
                                       command_press=self.button_press_callback,
                                       command_release=self.button_release_callback)
            self.button.place(x=37, y=87)
            self.buzzer = CircleIndicator(parent=self.window, width=self.buzzer_size, height=self.buzzer_size,
                                          color_on='dimgray', color_off='black', name='BUZZER')
            self.buzzer.place(x=79, y=91)
            self.redled = CircleIndicator(parent=self.window, width=self.led_size, height=self.led_size,
                                          color_on='red', color_off='darkred', name='RED_LED')
            self.redled.place(x=177, y=98)
            self.yelled = CircleIndicator(parent=self.window, width=self.led_size, height=self.led_size,
                                          color_on='yellow', color_off='olive', name='YELLOW_LED')
            self.yelled.place(x=220, y=98)
            self.grnled = CircleIndicator(parent=self.window, width=self.led_size, height=self.led_size,
                                          color_on='lime', color_off='darkgreen', name='GREEN_LED')
            self.grnled.place(x=262, y=98)
            self.start()

        def quit_callback(self):
            self.window.quit()

        def run(self):
            self.window.protocol("WM_DELETE_WINDOW", self.quit_callback)
            self.window.title('Fish Dish')
            self.window.mainloop()

        def indicator_set(self, indicator, indicator_state):
            if indicator == "LED_GRN":
                self.grnled.set_state(indicator_state)
            elif indicator == "LED_RED":
                self.redled.set_state(indicator_state)
            elif indicator == "LED_YEL":
                self.yelled.set_state(indicator_state)
            elif indicator == "BUZZER":
                self.buzzer.set_state(indicator_state)
            else:
                print("Undefined indicator.")

    def gpio_monitor(self):
        for key in self.active_gpio:
            pinname = "GPIO" + str(self.active_gpio[key])
            pin = self.GPIO.board_map[pinname]
            match = next((l for l in self.GPIO.config if l['pin'] == pin), None)
            if match is not None and match['config'] == self.GPIO.OUT and self.button_state != 1:
                self.assert_led(key, match['value'])

    def button_press(self):
        self.button_state = 1
        pinname = "GPIO" + str(self.active_gpio["BUTTON"])
        pin = self.GPIO.board_map[pinname]
        match = next((l for l in self.GPIO.config if l['pin'] == pin), None)
        if match is not None and match['config'] == self.GPIO.IN:
            match['value'] = self.GPIO.HIGH
        if _debug:
            print("Button pressed!")
            self.assert_led(led_color='GRN', led_state=ON)

    def button_release(self):
        self.button_state = 0
        pinname = "GPIO" + str(self.active_gpio["BUTTON"])
        pin = self.GPIO.board_map[pinname]
        match = next((l for l in self.GPIO.config if l['pin'] == pin), None)
        if match is not None and match['config'] == self.GPIO.IN:
            match['value'] = self.GPIO.LOW
        if _debug:
            print("Button released!")
            self.assert_led(led_color='GRN', led_state=OFF)

    def assert_led(self, led_color, led_state):
        self.GUI.indicator_set(indicator=led_color, indicator_state=led_state)

    def cleanup(self):
        self.GUI.quit_callback()
        for t in self.threads:
            print("Cancelling " + t.name)
            t.cancel()


if __name__ == "__main__":
    _debug = True
    GPIO = simGPIO.GPIO()
    fd = FishDish(GPIO)