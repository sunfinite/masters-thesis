import web3
from web3 import Web3, HTTPProvider
import time

w3 = Web3(HTTPProvider('https://2d3f9ba3.ngrok.io'))
print(w3.eth.syncing)
