#!/usr/bin/python
import struct
import socket
from collections import defaultdict
import requests
import sys
import codecs
# from bitcoin import network
import asyncio
# from p2p import kademlia, discovery as d
from eth_keys import keys
from eth_utils import *
import ipaddress
import json
from elasticsearch import Elasticsearch
from datetime import datetime
import traceback

es = Elasticsearch(['http://dce5388e.ngrok.io:80'])

def pcap_to_es(file_, index='nano-pcap'):
    pcap = json.load(open(file_))
    info = {}
    items = []
    for i, packet in enumerate(pcap):
        try:
            packet = packet['_source']['layers']
            if '_ws.malformed' in packet or 'data' not in packet:
                continue
            info['dest'] = packet['ip']['ip.dst']
            info['src'] = packet['ip']['ip.src']
            info['len'] = int(packet['frame']['frame.len'])
            info['time'] = datetime.strptime(packet['frame']['frame.time'], '%b %d, %Y %H:%M:%S.%f000 %Z').isoformat()
            if 'tcp' not in packet:
                info.update(deserialize_nano_msg(packet['data']['data.data'].replace(':', '')))
            else:
                info['msg'] = packet['data']['data.data']
            items.append({'index': {'_index': index, '_type': 'packet'}})
            items.append(info)
            if i % 100 == 0:
                es.bulk(items)
                items = []
        except Exception as e:
            print(e)
            print(packet)
            print(traceback.format_exc())


def deserialize_nano_msg(msg):
    msg = bytearray.fromhex(msg)
    msg_enum = ['invalid', 'not_a_type', 'keepalive', 'publish', 'confirm_req',
                'confirm_ack', 'bulk_pull', 'bulk_push', 'frontier_req', 'bulk_pull_blocks']
    info = {}

    header = struct.unpack('<2sBBBBH', msg[:8])
    if len(header) < 5:
        info['type']= 'tcp'
        return info

    if header[0] == b'RC':
        info['type']= msg_enum[header[4]]
    else:
        info['type']= 'unknown'

    if info['type'] == 'keepalive':
        peers = []
        for i in range(8, len(msg), 18):
            if len(msg) - i < 18:
                continue
            addr, port = struct.unpack('<16sH', msg[i : i + 18])
            addr = str(ipaddress.ip_address(addr).ipv4_mapped)
            peers.append([addr, port])
        info['msg'] = peers
    else:
        info['msg'] = msg.hex()
    return info

def flood_keepalive(limit=4200000, dst='localhost'):
    import scapy.all as scapy
    import struct
    port = 4242
    magic_number = b'RC'
    v, type_, ext = 0x09, 2, 0
    src = scapy.RandIP()

    payload = b''
    payload += struct.pack('<2s', magic_number)
    payload += struct.pack('<BBBBH', v, v, v, type_, ext)
    for i in range(8):
        payload += struct.pack('<16s', b'127.0.0.1')
        payload += struct.pack('<H', 4242)

    for i in range(limit):
        ip = scapy.IP(src=str(src), dst=dst)
        udp = scapy.UDP(sport=(port + i) % 65535, dport=port)
        spoofed_packet = ip / udp / payload
        scapy.send(spoofed_packet, iface="lo0", verbose=False)

def nano():
    '''
        Keepalive: Pick a random selection of peers and include them in the keepalive message

        Header: 
            magic_number: 'RC' for the live network
            version_max: 0x07
            version_using: 0x07
            version_min: 0x01
            message_type: 2 for keepalive
            extensions: 0 (?)

            preconfigured peer: rai.raiblocks.net
    '''

    # nodes = [('rai.raiblocks.net', 7075)]
    # nodes = [('45.35.55.30', 7075)]
    # nodes = [('localhost', 7075)]
    nodes = [('localhost', 4242)]
    peers = defaultdict(list)
    port = 7075
    magic_number = b'RC'
    version_max = 0x09
    version_using = 0x09
    version_min = 0x01
    message_type = 2
    extensions = 0

    for node in nodes:
        try:
            print("Trying ", node)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(3)
            # s.connect((seed, port))
            message = b''
            message += struct.pack('<2s', magic_number)
            message += struct.pack('<BBB', version_max, version_using, version_min)
            message += struct.pack('<B', message_type)
            message += struct.pack('<H', extensions)
            for i in range(8):
                message += struct.pack('<16s', b'127.0.0.1')
                message += struct.pack('<H', 8084 + i)
            b = s.sendto(message, node)
            msg, sender = s.recvfrom(1024)
            res = deserialize_nano(msg)
            print(res)
        except Exception as e:
            print(e)
    with open('nano.peers', 'w') as fout:
        fout.write(json.dumps(peers))
    return peers



def ripple():
    '''
        protocol messages use protobuf
        Handshake is via HTTP

    '''

    nodes = [('r.ripple.com', 51235)]
    peers = defaultdict(set)

    headers = {
        "User-Agent": '',
        "Upgrade": "RTXP/1.2",
        "Connection": "Upgrade",
        "Connect-As": "Peer",
        "Crawl": "public",
        "Public-Key": '',
        "Session-Signature": ''
    }
    for node in nodes:
        res = requests.get('http://%s:%d/' % node, headers=headers)
        print(res.text)

def bitcoin():
    '''
        Borrowed liberally from https://github.com/cdecker/pycoin
    '''

    params = {
        'magic': codecs.decode(b'D9B4BEF9', 'hex')[::-1],
        'port': 8333,
    }

    def checksum(payload):
        return hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]

    nodes = [
        "seed.bitcoinstats.com",
        "seed.bitcoin.sipa.be",
        "dnsseed.bluematt.me",
        "dnsseed.bitcoin.dashjr.org",
        "bitseed.xf2.org"
    ]

    peers = defaultdict(list)

    def serialize_message(message_type, payload):
        message = params['magic']
        message += message_type.ljust(12, chr(0)).encode('utf-8')
        message += struct.pack("<I", len(payload))
        message += checksum(payload)
        if type(payload) != bytes:
            payload = payload.encode('utf-8')
        message += payload
        return message


    def addr_handler(connection, addr):
        for a in addr.addresses:
            print(a.ip)

    def verack_handler(connection, verack):
        print("Got verack")
        connection.send("getaddr", '')

    client = network.GeventNetworkClient()
    client.register_handler('addr', addr_handler)
    client.register_handler('verack', verack_handler)
    network.ClientBehavior(client)
    for node in nodes:
        client.connect((node, params['port']))
    client.run_forever()

def ethereum():
    privkey_hex = '65462b0520ef7d3df61b9992ed3bea0c56ead753be7c8b3614e0ce01e4cac41b'
    listen_host = '0.0.0.0'
    listen_port = 30303
    bootstrap_uris = [
        b'enode://78de8a0916848093c73790ead81d1928bec737d565119932b98c6b100d944b7a95e94f847f689fc723399d2e31129d182f7ef3863f2b4c820abbf3ab2722344d@191.235.84.50:30303',
        b'enode://158f8aab45f6d19c6cbf4a089c2670541a8da11978a2f90dbf6a502a4a3bab80d288afdbeb7ec0ef6d92de563767f3b1ea9e8e334ca711e9f8e2df5a0385e8e6@13.75.154.138:30303',
        b'enode://1118980bf48b0a3640bdba04e0fe78b1add18e1cd99bf22d53daac1fd9972ad650df52176e7c7d89d1114cfef2bc23a2959aa54998a46afcf7d91809f0855082@52.74.57.123:30303',
    ]

    loop = asyncio.get_event_loop()
    privkey = keys.PrivateKey(decode_hex(privkey_hex))
    addr = kademlia.Address(listen_host, listen_port, listen_port)
    bootstrap_nodes = [kademlia.Node.from_uri(x) for x in bootstrap_uris]
    discovery = d.DiscoveryProtocol(privkey, addr, bootstrap_nodes)
    loop.run_until_complete(discovery.listen(loop))
    print(discovery.kademlia.routing.neighbours(discovery.this_node.id))
    
    # asyncio.ensure_future(discovery.bootstrap())
    # loop.run_until_complete(discovery.bootstrap())
    discovery.stop()
    loop.close()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Need a network name")
    elif sys.argv[1] == 'nano':
        for i in range(65535555):
            nano()
    elif sys.argv[1] == 'bitcoin':
        bitcoin()
    elif sys.argv[1] == 'ethereum':
        ethereum()
    elif sys.argv[1] == 'ripple':
        ripple()
