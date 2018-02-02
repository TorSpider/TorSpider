#!/usr/bin/env python3

# Update the database to reflect newest changes.

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

print('Clearing offline faults.')
cursor.execute("UPDATE urls SET fault = 'none' \
               WHERE fault = 'offline';")
cursor.execute("UPDATE pages SET fault = 'none' \
               WHERE fault = 'offline';")

print('Adding column offline_scans to onions table.')
cursor.execute("ALTER TABLE onions \
               ADD COLUMN offline_scans INTEGER DEFAULT 0;")

print('Committing changes.')
connection.commit()
connection.close()
print('Database update complete.')
