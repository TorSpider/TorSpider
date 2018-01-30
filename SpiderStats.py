#!/usr/bin/env python3

''' SpiderStats – Quickly check some basic metrics to see how the spiders are
    doing.
'''

import sys
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
if(cursor.fetchall()[0][0] == False):
    print('Database not yet initialized. No results to show.\n')
    sys.exit(0)

print('Gathering metrics...')

print('Url count...')
cursor.execute('SELECT count(id) FROM urls;')
url_count = cursor.fetchall()[0][0]

print('Onions...')
cursor.execute('SELECT count(id) FROM onions WHERE online = 1;')
onion_count = cursor.fetchall()[0][0]

print('Pages...')
cursor.execute('SELECT count(id) FROM pages WHERE domain IN \
               (SELECT id FROM onions WHERE online = 1);')
page_count = cursor.fetchall()[0][0]

print('Unique forms...')
cursor.execute('SELECT count(DISTINCT page) FROM forms WHERE page IN \
               (SELECT id FROM pages WHERE domain IN \
               (SELECT id FROM onions WHERE online = 1));')
form_page_count = cursor.fetchall()[0][0]

print('Form fields...')
cursor.execute('SELECT count(id) FROM forms WHERE page IN \
               (SELECT id FROM pages WHERE domain IN \
               (SELECT id FROM onions WHERE online = 1));')
form_field_count = cursor.fetchall()[0][0]

print('Links...')
cursor.execute('SELECT count(domain) FROM links WHERE domain IN \
               (SELECT id FROM onions WHERE online = 1) AND link IN \
               (SELECT id FROM onions WHERE online = 1);')
link_count = cursor.fetchall()[0][0]

print('–' * 60)
print('Results:')
messages = [
        'So far, TorSpider has found {} urls which have revealed {} active',
        'onion sites, comprising {} pages, with a total of {} forms and {}',
        'form fields. TorSpider has documented {} associations between sites.'
]
message = '\n'.join(messages)
print(message.format(url_count, onion_count, page_count, form_page_count, form_field_count, link_count))

connection.close()
