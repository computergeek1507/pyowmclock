from datetime import datetime
import sys
import time
import requests
import json
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

from Adafruit_LED_Backpack import SevenSegment
global show_temp
show_temp=False
global update_alarm
update_alarm=False

class ClockDisplay(SevenSegment.SevenSegment):
    COLON_OFF = 0x00
    COLON_CLOCK = 0x02
    COLON_UPPER_LEFT = 0x04
    COLON_LOWER_LEFT = 0x08
    COLON_UPPER_RIGHT = 0x10

    def set_colon(self, colon):
        self.buffer[4] = colon


class TempClock(object):
    def __init__(self, display):
        self._display = display
        self._time = '1200'
        self._pm = False
        self._outside = 0
        self._alarm = False

    def _update_time(self):
        now = datetime.now()
        self._time = now.strftime('%-I%M')
        self._pm = (now.strftime('%p') == 'PM')

    def show_time(self):
        self._update_time()
        self._display.clear()
        self._display.print_number_str(self._time)
        colon = ClockDisplay.COLON_CLOCK
        if self._pm:
            colon |= ClockDisplay.COLON_UPPER_LEFT
        if self._alarm:
            colon |= ClockDisplay.COLON_UPPER_RIGHT
        self._display.set_colon(colon)
        self._display.write_display()

    def _update_outside_temperature(self):
        
       response = requests.get("http://192.168.5.148:8080/rest/items/Temperature/state")
       self._outside = response.content

    def update_temperature(self):
        self._update_outside_temperature()

    def _show_temperature(self, temperature):
        self._display.clear()
        self._display.print_number_str('{0} '.format(int(float(temperature))))
        self._display.write_display()

    def show_temperature(self):
        self.update_temperature()
        self._show_temperature(self._outside)
        

    def update_alarm(self):
       response = requests.get("http://192.168.5.148:8080/rest/items/AlarmClock/state")
       data = response.content
       if(data == "ON"):
          self._alarm = True
       else:
          self._alarm = False

def button_callback1(channel):
    response = requests.post("http://192.168.5.148:8080/rest/items/Mstr_Bedroom_Lights", data="TOGGLE" )

def button_callback2(channel):
    response = requests.post("http://192.168.5.148:8080/rest/items/Inside_Lts", data="OFF")

def button_callback3(channel):
    response = requests.post("http://192.168.5.148:8080/rest/items/AlarmClock", data="TOGGLE")
    global update_alarm
    update_alarm=True

def button_callback4(channel):
    global show_temp
    show_temp=True



GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Set pin 37 to be an input pin and set initial value to be pulled low (off)

GPIO.add_event_detect(37,GPIO.RISING,callback=button_callback1, bouncetime=500)

GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(36,GPIO.RISING,callback=button_callback2, bouncetime=500)
GPIO.setup(32, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(32,GPIO.RISING,callback=button_callback3, bouncetime=500)
GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(29,GPIO.RISING,callback=button_callback4, bouncetime=500)



def main():

    brightness = -1
    if brightness not in range(0, 16):
        brightness = 1

    print 'Initializing display ...'
    display = ClockDisplay()
    display.begin()
    display.set_brightness(brightness)

    clock = TempClock(display)

    last_temperature = 0
    global show_temp
    global update_alarm
    count = 20

    while True:
        if(show_temp):
            clock.show_temperature()
            time.sleep(5)
            show_temp=False
        if(count>10 or update_alarm):
	    clock.update_alarm()
            count=0
            update_alarm=False
	clock.show_time()
        time.sleep(1)
        count+=1

if __name__ == '__main__':
    main()
