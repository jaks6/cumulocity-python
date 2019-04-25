import json
import os
import sys
from uuid import getnode as get_mac

import errno

__author__ = 'Jakob'


def int_to_bytes(n, minlen=0):  # helper function
    """ Int/long to byte string. """
    nbits = n.bit_length() + (1 if n < 0 else 0)  # plus one for any sign bit
    nbytes = (nbits + 7) // 8  # number of whole bytes
    b = bytearray()
    for _ in range(nbytes):
        b.append(n & 0xff)
        n >>= 8
    if minlen and len(b) < minlen:  # zero pad?
        b.extend([0] * (minlen - len(b)))
    return bytearray(reversed(b))  # high bytes first


def test_bit(int_type, offset):
    mask = 1 << offset
    return (int_type & mask)


def printbits(bits):
    size = sys.getsizeof(bits) * 8  # bits
    result = ""
    for i in range(size, -1, -1):
        if test_bit(bits, i):
            result += '1'
        else:
            result += '0'
    print(result)


def mantissa(float32):
    # rightmost 23 bits make up the fraction (mantissa)
    mantissa = 1.0
    x = 1
    for i in range(22, -1, -1):
        x = x / 2.0
        if test_bit(float32, i):
            mantissa += x
    return mantissa


def write_to_file(jsondata, filename):
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'w') as outfile:
        json.dump(jsondata, outfile)

def load_json_file(file):
    with open(file) as f:
        result = json.load(f)
    return result


def get_mac_string():
    mac = get_mac()
    return hex(mac)
    # return ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
