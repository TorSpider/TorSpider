#!/usr/bin/env python3

''' SpiderStats – Quickly check some basic metrics to see how the spiders are
    doing.
'''

import textwrap
import requests
import json
import urllib.parse
import configparser
import sys
import os


def count_field(endpoint, query):
    r = requests.get(api_url + endpoint + '?results_per_page=1&q=' + urllib.parse.quote_plus(json.dumps(query)),
                     verify=False)
    if r.status_code == 200:
        # If correct then it returns the object data
        return json.loads(r.text).get('num_results')
    else:
        return {}


if __name__ == '__main__':

    # Load the configuration file.
    try:
        config = configparser.ConfigParser()
        config.read('spider.cfg')
        api_url = config['API'].get('api_url')
    except Exception as e:
        print('Could not parse spider.cfg. Please verify its syntax.')
        sys.exit(0)

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
    date_query = {"filters": [{"op": "ne", "name": "date", "val": "1900-01-01"}]}
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

    # Get the totals
    total_onions = count_field('onions', empty_query)
    total_urls = count_field('urls', empty_query)
    total_pages = count_field('pages', empty_query)
    total_forms = count_field('forms', empty_query)
    total_links = count_field('links', empty_query)

    print('–' * 70)
    print('Results:')
    messages = [
        'So far, TorSpider has scanned {:,} ({:.2%}) of the {:,} urls it has',
        'discovered. Of the scanned sites, {:,} are known to be active.' + os.linesep,
        'Table Stats:' + os.linesep,
        'Total Onions: {:}' + os.linesep,
        'Total Urls: {:}' + os.linesep,
        'Total Pages: {:}' + os.linesep,
        'Total Forms: {:}' + os.linesep,
        'Total Links: {:}'
    ]

    message = ' '.join(messages)
    message = message.format(url_count_scanned, url_count_percentage,
                             url_count, onion_count, total_onions, total_urls, total_pages, total_forms, total_links)

    print(message)
