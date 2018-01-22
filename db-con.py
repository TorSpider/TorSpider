#!/usr/bin/env python3

''' Database conversion tool.
    Use this tool to convert databases from the previous release into the new,
    updated release. The expectation is that your database is only one release behind, so if you've skipped a release, this tool won't work. Also, please
    be sure that no applications are reading from or writing to the database
    when you run this tool.

    BACK UP YOUR DATABASE BEFORE USING THIS TOOL.
'''

import sqlite3 as sql
from urllib.parse import urlsplit, urlunsplit


def extract_exact(list1, list2):
    # Return the common items from both lists.
    return [item for item in list1
            if any(scan == item for scan in list2)]


def get_domain(url):
    # Get the defragmented domain of the given url.
    domain = urlsplit(url).netloc
    # Let's omit subdomains. Rather than having separate records for urls
    # like sub1.onionpage.onion and sub2.onionpage.onion, just keep them
    # all under onionpage.onion.
    domain = '.'.join(domain.split('.')[-2:])
    return domain


def get_page(url):
    # Get the page from a link.
    return urlsplit(url).path


def merge_titles(title1, title2):
    title1_parts = title1.split()
    title2_parts = title2.split()
    new_title_parts = extract_exact(title1_parts, title2_parts)
    return ' '.join(new_title_parts)


'''---[ BEGIN CONVERSION ]---'''


print('Opening database.')
db = sql.connect('data/SpiderWeb.db')
cur = db.cursor()


# Here are all the necessary adjustments to be made.


print('Adding pages table to database.')
cur.execute("ALTER TABLE pages RENAME TO urls;")
cur.execute("CREATE TABLE IF NOT EXISTS pages ( \
            id INTEGER PRIMARY KEY, \
            url TEXT, \
            title TEXT DEFAULT 'none', \
            domain INTEGER, \
            info TEXT, \
            form_fields TEXT, \
            CONSTRAINT unique_page UNIQUE(domain, url));")
db.commit()


print('Creating dictionary of domains.')
cur.execute('SELECT domain, id FROM onions;')
res = cur.fetchall()
domains = {}
for item in res:
    (domain, domain_id) = item
    domains[domain] = domain_id


print('Collecting urls from database.')
cur.execute('SELECT url, title FROM urls;')
urls = cur.fetchall()


print('Processing urls and populating pages.')
records = 0
for item in urls:
    (url, page_title) = item
    page_title = 'none' if page_title == 'Unknown' else page_title
    domain = get_domain(url)
    domain_id = domains[domain]
    page = get_page(url)
    cur.execute('SELECT url, title FROM pages \
                WHERE url = ? AND domain = ?;',
                [page, domain_id])
    res = cur.fetchall()
    if(res == []):
        page_title = 'Unknown' if page_title == '' else page_title
        cur.execute('INSERT OR IGNORE INTO pages \
                    (domain, url, title) VALUES ( \
                    ?, ?, ?);', (domain_id, page, page_title))
    else:
        try:
            (url, old_title) = res[0]
            new_title = page_title if page_title != 'none' else old_title
            if(old_title != new_title and old_title != 'none'):
                new_title = merge_titles(new_title, old_title)
            new_title = 'Unknown' if new_title == '' else new_title
            cur.execute('UPDATE pages SET title = ? \
                        WHERE url = ? AND domain = ?;',
                        [new_title, page, domain_id])
        except Exception as e:
            print('Error: {}'.format(res))
    db.commit()
    records += 1

print('{} records processed.'.format(records))
print('Saving final changes and closing database.')
db.commit()
db.close()
print('Done!')
