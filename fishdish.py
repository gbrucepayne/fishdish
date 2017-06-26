"""
    Initializes the Fish Dish GPIO board
    Flashes the green LED and plays a tune on start-up
    Waits for a button press to trigger graceful shutdown after playing a tune and flashing the red LED

    Tune definition is done by parsing a RTTL ringtone file
"""

# !/usr/bin/python
import sys
import os
import time
import logging
import threading
import argparse

global _rpi
try:
    import RPi.GPIO as GPIO
    _rpi = True
except ImportError:
    print('Error importing RPi.GPIO library')
    if sys.platform.lower().startswith('win32'):
        print('Simulating GPIO/Fishdish for Windows')
        import simGPIO
        import winsound
        GPIO = simGPIO.GPIO()
        _rpi = False
    else:
        sys.exit('Unsupported Operating System')

# FishDish hardware map (BCM)
LED_GRN = 4
LED_YEL = 22
LED_RED = 9
BUZZER = 8
BUTTON = 7

global _debug
global _shutdown
global startSong
global endSong

logfileName = 'fishdish.log'
if _rpi:
    logfileName = '/home/pi/' + logfileName
logging.basicConfig(filename=logfileName, level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d,(%(threadName)-10s),[%(levelname)s],%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


chargeRingtone = "Charge:d=4,o=5,b=108:8g4,8c,8e,8g.,16e,2g"

smdRingtone = "SuperMarioDies:d=4,o=5,b=76:32c6,32c6,32c6,8p,16b,16f6,16p,16f6,16f.6,16e.6,16d6,16c6,16p,16e,16p,16c"


class Song:
    """An object with attributes for title, tempo, notes and durations."""

    # Tones source: http://www.phy.mtu.edu/~suits/notefreqs.html
    tones = {
        'P': 0,
        'C0': 16,
        'C#0': 17,
        'D0': 18,
        'D#0': 20,
        'E0': 21,
        'F0': 22,
        'F#0': 23,
        'G0': 25,
        'G#0': 26,
        'A0': 28,
        'A#0': 29,
        'B0': 31,
        'C1': 33,
        'C#1': 35,
        'D1': 37,
        'D#1': 39,
        'E1': 41,
        'F1': 44,
        'F#1': 46,
        'G1': 49,
        'G#1': 52,
        'A1': 55,
        'A#1': 58,
        'B1': 62,
        'C2': 65,
        'C#2': 69,
        'D2': 73,
        'D#2': 78,
        'E2': 82,
        'F2': 87,
        'F#2': 93,
        'G2': 98,
        'G#2': 104,
        'A2': 110,
        'A#2': 117,
        'B2': 123,
        'C3': 131,
        'C#3': 139,
        'D3': 147,
        'D#3': 156,
        'E3': 165,
        'F3': 175,
        'F#3': 185,
        'G3': 196,
        'G#3': 208,
        'A3': 220,
        'A#3': 233,
        'B3': 247,
        'C4': 262,
        'C#4': 277,
        'D4': 294,
        'D#4': 311,
        'E4': 330,
        'F4': 349,
        'F#4': 370,
        'G4': 392,
        'G#4': 415,
        'A4': 440,
        'A#4': 466,
        'B4': 494,
        'C5': 523,
        'C#5': 554,
        'D5': 587,
        'D#5': 622,
        'E5': 659,
        'F5': 698,
        'F#5': 740,
        'G5': 784,
        'G#5': 831,
        'A5': 880,
        'A#5': 932,
        'B5': 988,
        'C6': 1047,
        'C#6': 1109,
        'D6': 1175,
        'D#6': 1245,
        'E6': 1319,
        'F6': 1397,
        'F#6': 1480,
        'G6': 1568,
        'G#6': 1661,
        'A6': 1760,
        'A#6': 1865,
        'B6': 1976,
        'C7': 2093,
        'C#7': 2217,
        'D7': 2349,
        'D#7': 2489,
        'E7': 2637,
        'F7': 2794,
        'F#7': 2960,
        'G7': 3136,
        'G#7': 3322,
        'A7': 3520,
        'A#7': 3729,
        'B7': 3951,
        'C8': 4186,
        'C#8': 4435,
        'D8': 4699,
        'D#8': 4978,
        'E8': 5274,
        'F8': 5588,
        'F#8': 5920,
        'G8': 6272,
        'G#8': 6645,
        'A8': 7040,
        'A#8': 7459,
        'B8': 7902
    }

    # Tempo source: https://music.stackexchange.com/questions/4525/list-of-average-genre-tempo-bpm-levels
    tempos = {
        'largo': 40,
        'larghetto': 60,
        'adiago': 66,
        'andante': 76,
        'moderato': 108,
        'allegro': 120,
        'presto': 168,
        'prestissimo': 200
    }

    def __init__(self, title='nil', tempo=108, piezo=False):
        self.title = title
        self.tempo = tempo  # Beats Per Minute
        self.notes = []
        self.durations = []
        self.piezo = piezo

    def playsong(self):
        """Plays the tune."""
        if _debug: logging.debug('Playing song: ' + self.title)
        tempo = 108.0 / float(self.tempo)
        notes = len(self.notes)
        note = 0
        while note < notes:
            duration = tempo / float(self.durations[note])
            if _debug: logging.debug('Playing note ' + self.notes[note] + ' for ' + str(duration) + ' seconds.')
            pitch = self.tones[self.notes[note]]
            if pitch > 0:
                if self.piezo:
                    audible = GPIO.PWM(BUZZER, pitch)
                    dcVolume = 1.0
                    audible.start(dcVolume)   # volume is represented by Duty Cycle in the range 0..100
                    time.sleep(duration)
                    audible.stop()
                else:
                    winsound.Beep(pitch, int(duration * 1000))
            else:
                time.sleep(duration)
            time.sleep(duration * 0.3)
            note += 1

    def play(self):
        threading.Thread(name='song' + self.title, target=self.playsong).start()

    def parseRTTL(self, ringtone):
        """Parses the Nokia RTTL format text file to create a song made of tempo, notes and durations.

        Ringtone file format: https://en.wikipedia.org/wiki/Ring_Tone_Transfer_Language
        :param ringtone: an RTTL compliant text string/file
        :return: song dictionary with title, BPM (tempo), notes, durations (divisors)
        """
        # noteDurations = [1, 2, 4, 8, 16, 32]
        self.title = ringtone.split(':')[0].strip()
        defaults = ringtone.split(':')[1].strip()
        melody = ringtone.split(':')[2]
        defaultDuration = defaults.split(',')[0].strip().replace('d=', '')
        defaultOctave = defaults.split(',')[1].strip().replace('o=', '')
        self.tempo = int(defaults.split(',')[2].strip().replace('b=', ''))
        melodyNotes = melody.split(',')
        for melodyNote in melodyNotes:
            melodyNote = melodyNote.strip()
            strPos = 0
            noteFound = False
            isOctave = False
            duration = ''
            note = ''
            octave = ''
            while strPos < len(melodyNote) and not noteFound:
                try:
                    if int(melodyNote[strPos]) in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
                        duration += melodyNote[strPos]
                except:
                    if melodyNote[strPos].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'p']:
                        noteFound = True
                        note += melodyNote[strPos].upper()
                strPos += 1
            if duration == '':
                duration = defaultDuration
            duration = int(duration)
            while strPos < len(melodyNote) and not isOctave:
                try:
                    if int(melodyNote[strPos]) in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
                        isOctave = True
                        octave = melodyNote[strPos]
                except:
                    if melodyNote[strPos] == '#':
                        note += melodyNote[strPos]
                    elif melodyNote[strPos] == '.':
                        duration = int(1.0/(1.0/float(duration) * 1.5))
                    else:
                        logging.error('Unidentified character/order while parsing RTTL.')
                strPos += 1
            if note != 'P':
                if isOctave:
                    note += octave
                else:
                    note += defaultOctave
            self.notes.append(note)
            self.durations.append(duration)


def flashled(ledpin=LED_GRN, frequency=1.0, cycles=1):
    """Toggles a LED """
    if cycles > 0:
        tick = int(cycles)
    elif cycles == 0:
        tick = 1
    LEDstate = False
    while tick > 0:
        if not LEDstate:
            GPIO.output(ledpin, GPIO.HIGH)
            LEDstate = True
        else:
            GPIO.output(ledpin, GPIO.LOW)
            LEDstate = False
            tick -= 1
        if cycles == 0:
            tick = 1
        time.sleep(frequency / 2.0)


def shutdown(channel):
    """ Callback function for a GPIO input event requesting graceful shutdown """

    global _debug
    global _shutdown
    global endSong

    SD_DEBOUNCE = 3
    SD_COUNTDOWN = 5
    SD_CMD = 'sudo shutdown -h now'

    debounce_count = 0
    while debounce_count < SD_DEBOUNCE:
        if not GPIO.input(BUTTON):
            if _debug:
                print('Input button not held high. Shutdown avoided.')
            return
        if _debug:
            print('Button debounce count: ' + str(debounce_count))
        debounce_count += 1
        time.sleep(1)

    if not _shutdown:
        if _debug: print("Halt request via GPIO input #" + str(BUTTON))
        logging.info("Halt request via GPIO input #" + str(BUTTON))
        if endSong is not None:
            endSong.play()
        _shutdown = True
        tick = SD_COUNTDOWN
        while tick > 0:
            if _debug: print("WARNING: system shutdown in " + str(tick) + " seconds")
            GPIO.output(LED_RED, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(LED_RED, GPIO.LOW)
            time.sleep(0.5)
            tick -= 1
        GPIO.output(LED_RED, GPIO.HIGH)
        if _debug:
            GPIO.output(LED_RED, GPIO.LOW)
            GPIO.cleanup()
            sys.exit('Virtual shutdown (' + SD_CMD + ')')
        else:
            os.system(SD_CMD)


def splash():
    print('\n')
    print('\\-\\    \\-------\\')
    print(' \\ -----       --\\')
    print('  \\  FISH DISH    \\')
    print('   /  HEADLESS    O -\\')
    print('  <.................../')
    print('\n')


def main():
    global _debug
    global _shutdown
    global startSong
    global endSong

    _shutdown = False

    # Derive run options from command line
    parser = argparse.ArgumentParser(description='Fishdish GPIO interface')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='run in debug mode (virtual shutdown)')
    # TODO: add some parameters to optionally customize/validate the tune played on startup and shutdown

    args = parser.parse_args()
    _debug = args.debug

    if _debug:
        splash()

    startSong = Song(piezo=_rpi)
    startSong.parseRTTL(chargeRingtone)

    endSong = Song(piezo=_rpi)
    endSong.parseRTTL(smdRingtone)

    try:
        GPIO.setmode(GPIO.BCM)

        leds = [LED_GRN, LED_YEL, LED_RED]
        GPIO.setup(leds, GPIO.OUT)
        GPIO.setup(BUZZER, GPIO.OUT)

        for led in leds:
            GPIO.output(led, GPIO.LOW)

        threading.Thread(name='init_flash', target=flashled, args=(LED_GRN, 1.0, 3)).start()

        startSong.play()

        GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(BUTTON, GPIO.RISING, callback=shutdown)
        # TODO: create virtual FishDish GUI event handler for PC testing/demo in simGPIO.py

        while True:
            pass

    except KeyboardInterrupt:
        msg = 'Fishdish program halted by keyboard interrupt.'
        print(msg)
        logging.info(msg)

    except Exception, e:
        logging.error('Error: ' + str(e))

    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    _debug = True     # uncomment for PC testing
    main()
