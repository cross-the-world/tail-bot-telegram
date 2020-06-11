import time
import os
import random
import re
import json

import numpy as np

# load config
config = None
with open('config/config.json') as f:
    config = json.load(f)
assert config is not None


folder = "images"
def getStorageFolder():
    if not os.path.exists(folder):
        os.mkdir(folder)
    return folder

def getStoragePath(filename):
    return os.path.join(getStorageFolder(), filename)

def rm(p):
    if p:
        os.remove(p)
    pass

def parse_message(u):
    return u.message if u.message else u.edited_message

seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 604800*30}
def convert_to_seconds(s):
    return int(s[:-1]) * seconds_per_unit[s[-1]]

def sleep(s):
    time.sleep(convert_to_seconds(s))

def roundQty(v, decimals=4):
    return round(v, decimals)

def roundPrice(v, decimals=8):
    return round(v, decimals)

def random_color():
    return "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])

def random_int(start, stop):
    return random.randint(start, stop)

def split(text, pattern="\s+"):
    return None if not text else re.split(pattern, text)
