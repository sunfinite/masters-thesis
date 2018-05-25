import struct
import socket
import json
from collections import OrderedDict
import time
import os

def get_header():
    magic_number = b'RC'
    version_max = 0x14
    version_using = 0x14
    version_min = 0x01
    message_type = 8
    extensions = 0

    message = b''
    message += struct.pack('<2s', magic_number)
    message += struct.pack('<BBB', version_max, version_using, version_min)
    message += struct.pack('<B', message_type)
    message += struct.pack('<H', extensions)
    
    return message


def get_frontier_req():
    int_max = 4294967295
    message = b''
    message += struct.pack('<32s', (b'\x00' * 32))
    message += struct.pack('<I', int_max)
    message += struct.pack('<I', int_max)
    return message

def send_frontier_req():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #s.connect(('::1', 7075, 0, 0))
    start = int(time.time())
    s.connect(('localhost', 7075))
    message = get_header() + get_frontier_req()
    s.send(message)
    frontiers = OrderedDict()
    i = 0
    while True:
        msg = s.recv(64)
        address, hash_ = struct.unpack('<32s32s', msg)
        if address == b'\x00' * 32:
            break
        frontiers[address.hex()]  = hash_.hex()
        i += 1
    end = int(time.time())
    print(len(frontiers))
    f = '%d_%d.out' % (start, end)
    with open(f, 'w') as fout:
        fout.write(json.dumps(frontiers))
        os.system('gzip %s' % f)

if __name__ == '__main__':
    while True:
        send_frontier_req()
        time.sleep(600)




