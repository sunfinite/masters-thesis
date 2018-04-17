import web3
from web3 import Web3, IPCProvider
import time

PATH = '/home/sunfinite/go-ethereum/build/bin/n1/geth.ipc'
PEER = 'enode://d22cf10a1b9fbd7da15665b4f04b6ec07d99674ba0ed2f1e9992a3ccc4fbeca534112d75d5941227aec1461f5e03f7b2105923630b861194a319e1a37029ee94@127.0.0.1:4343'
w3 = Web3(IPCProvider(PATH))
print("Add peer")
print(w3.admin.addPeer(PEER))
print("Unlock account")
print(w3.personal.unlockAccount(w3.eth.coinbase, ''))
print("Send transaction")
print(w3.eth.sendTransaction({'from': w3.eth.coinbase, 'to': w3.eth.coinbase,
    'value': 100}))
print("Start mining")
print(w3.miner.start(1))
time.sleep(5)
print("Stop mining")
print(w3.miner.stop())
