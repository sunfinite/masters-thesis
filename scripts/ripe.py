import requests
import pyasn
import json
import socket
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
from geoip import geolite2
import requests

es = Elasticsearch(['http://dce5388e.ngrok.io:80'])
base_url = 'https://stat.ripe.net/data/'
asndb = pyasn.pyasn('/Users/skatkuri/masters-thesis/scripts/ipasn.dat')

def request(endpoint, resource):
    url = base_url + endpoint + '/data.json?resource=' + resource
    res = requests.get(url)
    return res.json()['data']

def get_asn(ip):
    # return request('network-info', ip)
    return asndb.lookup(ip)[0]

def get_asn_details(ip):
    return request('network-info', ip)

def get_geoloc(ip):
    geo = geolite2.lookup(ip)
    if geo:
        return geo.country
    else:
        print("geolite failed for ", ip)
        res = request('geoloc', ip)
        if res and res['locations']:
            return res['locations'][0]['country']
    return ''

def get_country_resource_list(country):
    return request('country-resource-list', country)

def get_asn_neighbours(asn):
    return request('asn-neighbours', str(asn))
    
def get_bgp_state(asn):
    return request('bgp-state', str(asn))

def get_dns_chain(domain):
    return request('dns-chain', domain)

def eth_nodes_to_es():
    nodes = json.load(open('eth_nodes.json'))['data']
    items = []
    for i, node in enumerate(nodes):
        print(i)
        try:
            node['asn'] = get_asn(socket.gethostbyname(node['host']))
            if not node['asn']:
                node['asn'] = 0
            items.append({'index': {'_index': 'eth-nodes', '_type': 'node', '_id': node['host'] + str(node['port'])}})
            items.append(node)
            # if (i + 1) % 500 == 0:
            #    return es.bulk(items)
        except Exception as e:
            print(node)
            print(e)

    es.bulk(items)

def nano_nodes_to_es():
    url = 'https://nano.org/en/explore/peers'
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    rows = soup.findAll('tr')
    items = []
    for row in rows[1:]:
        node = {}
        node['host'] = row.find('a').text
        node['asn'] = get_asn(node['host'])
        node['country'] = get_geoloc(node['host'])
        items.append({'index': {'_index': 'nano-nodes', '_type': 'node', '_id': node['host']}})
        items.append(node)
    es.bulk(items)

def iota_nodes_to_es():
    url = 'http://62.138.1.187:21494/'
    res = requests.get(url)
    print(len(res.json()))
    items = []
    for node in res.json():
        print(node['hostname'])
        ip = socket.gethostbyname(node['hostname'])
        print(ip)
        node['asn'] = get_asn(ip)
        node['country'] = get_geoloc(ip)
        items.append({'index': {'_index': 'iota-nodes', '_type': 'node', '_id': node['hostname']}})
        items.append(node)
    es.bulk(items)

    

def query_es_terms():
    query = {
        "size": 0,
        "aggs" : {
            "asns" : {
                "terms" : { "field" : "asn",  "size" : 50000 }
            }
        }
    }
    res = es.search(index='nano-nodes', body=query)
    print(res.keys())

if __name__ == '__main__':
    iota_nodes_to_es()
