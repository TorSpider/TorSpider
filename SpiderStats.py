#!/usr/bin/env python3

''' SpiderStats – Quickly check some basic metrics to see how the spiders are
    doing.
'''

import sys
import textwrap
import configparser
import psycopg2 as sql

print('Reading configuration file...')
config = configparser.ConfigParser()
config.read('spider.cfg')
postgre_user = config['PostgreSQL'].get('Username')
postgre_pass = config['PostgreSQL'].get('Password')
postgre_host = config['PostgreSQL'].get('Hostname')
postgre_dbase = config['PostgreSQL'].get('Database')

print('Connecting to database...')
connection = sql.connect(
        "dbname='{}' user='{}' host='{}' \
        password='{}'".format(
                postgre_dbase,
                postgre_user,
                postgre_host,
                postgre_pass))
cursor = connection.cursor()

cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables \
               WHERE tablename = 'links');")
if(cursor.fetchall()[0][0] is False):
    print('Database not yet initialized. No results to show.\n')
    sys.exit(0)

print('Gathering metrics...')

print('Url count...')
cursor.execute("SELECT count(id) FROM urls;")
url_count = cursor.fetchall()[0][0]
cursor.execute("SELECT count(id) FROM urls WHERE date != '1900-01-01';")
url_count_scanned = cursor.fetchall()[0][0]
url_count_percentage = (url_count_scanned / url_count)

print('Onions...')
cursor.execute("SELECT count(id) FROM onions WHERE online = 1 AND \
               last_online != '1900-01-01';")
onion_count = cursor.fetchall()[0][0]

print('Links...')
cursor.execute("SELECT count(domain) FROM links WHERE domain IN \
               (SELECT id FROM onions WHERE online = 1 AND \
               last_online != '1900-01-01') AND link IN \
               (SELECT id FROM onions WHERE online = 1 AND \
               last_online != '1900-01-01');")
link_count = cursor.fetchall()[0][0]

print('–' * 70)
print('Results:')
messages = [
        'So far, TorSpider has scanned {:,} ({:.2%}) of the {:,} urls it has',
        'discovered. Of the scanned sites, {:,} are known to be active.',
        'TorSpider has found {:,} direct links between these sites.'
]

message = ' '.join(messages)
message = message.format(url_count_scanned, url_count_percentage, url_count,
                         onion_count, link_count)
message = textwrap.fill(message)
print(message)

connection.close()
