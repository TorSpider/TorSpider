#!/usr/bin/env python3

''' SpiderStats – Quickly check some basic metrics to see how the spiders are
    doing.
'''

import textwrap
import requests
import json
import urllib.parse

api_url = 'http://192.168.163.133/api/'


def count_field(endpoint, query):
    r = requests.get(api_url + endpoint + '?results_per_page=1&q=' + urllib.parse.quote_plus(json.dumps(query)), verify=False)
    if r.status_code == 200:
        # If correct then it returns the object data
        return json.loads(r.text).get('num_results')
    else:
        return {}


print('Gathering metrics...')

print('Url count...')
empty_query = {"filters": []}
url_count = count_field('urls', empty_query)
date_query = {
    "filters": [
        {
            "op": "ne",
            "name": "date",
            "val": "1900-01-01"
        }
    ]}
date_query = {"filters": [{"op": "ne","name": "date","val": "1900-01-01"}]}
url_count_scanned = count_field('urls', date_query)
url_count_percentage = (url_count_scanned / url_count)

print('Onions...')
onion_query = {
    "filters": [
        {
            "op": "ne",
            "name": "last_online",
            "val": "1900-01-01"
        },
        {
            "op": "eq",
            "name": "online",
            "val": "true"
        }
    ]}
onion_count = count_field('onions', onion_query)

print('–' * 70)
print('Results:')
messages = [
    'So far, TorSpider has scanned {:,} ({:.2%}) of the {:,} urls it has',
    'discovered. Of the scanned sites, {:,} are known to be active.'
]

message = ' '.join(messages)
message = message.format(url_count_scanned, url_count_percentage,
                         url_count, onion_count)
message = textwrap.fill(message)
print(message)
