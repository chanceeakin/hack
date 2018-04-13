#!/usr/bin/env python

import os
import sys
import time
import evdev
import requests
import json
from functools import partial

env = partial(os.environ.get)

class Config:
    BARCODE_INPUT_DEVICE = env("BARCODE_INPUT_DEVICE")
    SNACK_SERVICE_HOST = "http://localhost:8080" #env("SNACK_SERVICE_HOST")

class BarcodeReader():
    def __init__(self, config):
        self.barcode_reader = None
        self.config = config
        self.code = ''
        # Try to connect
        self.connect_to_reader()

    def post(self, code):
        print("Posting : {}".format(code))
        data = {"item_code": code}
        headers = {"content-type": "application/json"}
        try:
            r = requests.post(self.config.SNACK_SERVICE_HOST + "/state/item_code", data=json.dumps(data), headers=headers)
            print(r.content)
        except requests.exceptions.ConnectionError as e:
            print("Failed to connect. Please try again.")

    def connect_to_reader(self):
        self.barcode_reader = None
        try:
            self.barcode_reader = evdev.InputDevice('/dev/input/event17')
        except OSError as e:
            print("No barcode reader found: {0}".format(e))

    def _read_code(self):
        for event in self.barcode_reader.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_press_data = evdev.categorize(event)
                # print(key_press_data)
                if key_press_data.keystate == 1:  # dow press only.
                    key_code = key_press_data.keycode[4:]
                    # print(key_press_data.keycode)
                    if len(key_code) == 1:
                        self.code = self.code + key_code
                    if key_code == "ENTER":
                        print("End of input")
                        print("Code is : {0}".format(self.code))
                        self.post(self.code)
                        self.code = ''

    def read_code(self):
        try:
            if(self.barcode_reader is not None):
                self._read_code()
            else:
                self.connect_to_reader()
                time.sleep(3)
        except IOError as e:
            print("Missing input device.... is scanner plugged in? \n {0}".format(e))
            self.connect_to_reader()
            time.sleep(3)


def main():
    config = Config()
    reader = BarcodeReader(config)
    # devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    # for device in devices:
    #     print(device.fn, device.name, device.phys)
    while(1):
        reader.read_code()

if __name__ == "__main__":
    main()
