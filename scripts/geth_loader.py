from elasticsearch import Elasticsearch
import web3
from web3 import Web3, IPCProvider
import rlp
import time
import subprocess
import os
import random
import sys
import traceback

es = Elasticsearch(['http://hungry-turkey-96.localtunnel.me:80'])
txpool_diff = 0.2

BASE = '/Users/skatkuri/go/src/github.com/ethereum/go-ethereum/build/bin/'
# GETH = BASE + 'geth-vanilla'
GETH = BASE + 'geth'
GENESIS = BASE + 'genesis.json'
DATADIR1 = BASE + 'n1'
DATADIR2 = BASE + 'n2'

for d in [DATADIR1, DATADIR2]:
    if not os.path.exists(d):
        raise Exception("%s does not exist" % d)
    keydir = d + '/keystore'
    if not os.path.exists(keydir):
        raise Exception("%s not found" % keydir)
    os.system('rm -r %s' % d + '/geth')
    os.system('%s --datadir %s init %s' % (GETH, d, GENESIS))
        
CMD1 = GETH + ' --datadir ' + DATADIR1 + ' --nodiscover --port 4242' # --rpc --verbosity 6'
CMD2 = GETH + ' --datadir ' + DATADIR2 + ' --nodiscover --port 4343' # --verbosity 6'
LOG1 = 'p1.log'
LOG2 = 'p2.log'
IPC1  = DATADIR1 + '/geth.ipc'
IPC2  = DATADIR2 + '/geth.ipc'

def get_block_details(block_number):
    query = {'query': {                              
         "term" : {                                                                                                                                                                                     
             "number" : block_number
        }
    }} 
    res = es.search(index='eth-headers', body=query)
    res =res['hits']['hits'][0]['_source']
    return res['size'], res['tx_count']

def get_txs(block_number, count):
    query = {'query': {                              
         "term" : {                                                                                                                                                                                     
             "blockNumber" : block_number
        }
    }}
    res = es.search(index='eth-txs', body=query, size=count)
    return [tx['_source'] for tx in res['hits']['hits']]

def get_enode(rpc):
    return rpc.admin.nodeInfo.enode

def add_peer(rpc, peer):
    return rpc.admin.addPeer(peer)

def unlock_coinbase_account(rpc):
    return rpc.personal.unlockAccount(rpc.eth.coinbase, '')

def send_txs(rpc, txs, skip=0):
    ret_txs = [None] * len(txs)
    for tx in sorted(txs, key=lambda x: x['transactionIndex']):
        from_ = to = rpc.eth.coinbase
        if random.random() >= skip:
            mod_tx = rpc.eth.sendTransaction({'from': from_, 'to': to,
                'value': tx['value'], 'input': tx['input'], 'gasPrice': tx['gasPrice']})
            ret_txs.append(mod_tx)
    return ret_txs

def mine(rpc, duration=60):
    rpc.miner.start(1)
    time.sleep(duration)
    rpc.miner.stop()

def run(block):
    with open(LOG1, 'w') as f1, open(LOG2, 'w') as f2:
        try:
            p1 = subprocess.Popen(CMD1, shell=True, stderr=f1)
            p2 = subprocess.Popen(CMD2, shell=True, stderr=f2)

            size, count = get_block_details(block)
            txs = get_txs(block, count)
            print("Block: ", block)
            print("Fetched size: %d and tx_count: %d" % (size, count))

            
            rpc1 = Web3(IPCProvider(IPC1))
            rpc2 = Web3(IPCProvider(IPC2))

            node1 = get_enode(rpc1)
            node2 = get_enode(rpc2)
            print("Fetched enodes")

            add_peer(rpc1, node2)
            add_peer(rpc2, node1)
            print("Added peers")

            unlock_coinbase_account(rpc1)
            unlock_coinbase_account(rpc2)
            print("Accounts unlocked")

            send_txs(rpc1, txs)
            # send_txs(rpc2, txs, skip=txpool_diff)
            print("Txs sent")
            
            print("Mining")
            mine(rpc1, 120)
            print("Stopped")

        except Exception as e:
            print(traceback.format_exc())
        finally:
            p1.terminate()
            p2.terminate()

if __name__ == '__main__':
    run(sys.argv[1])
