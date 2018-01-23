#!/usr/bin/env python3

''' Database conversion tool.
    Use this tool to convert databases from the previous release into the new,
    updated release. The expectation is that your database is only one release behind, so if you've skipped a release, this tool won't work. Also, please
    be sure that no applications are reading from or writing to the database
    when you run this tool.
'''

import sys
import sqlite3 as sql
from shutil import copyfile
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


def get_query(this_url):
    # Get the query information from the url.
    this_query = urlsplit(this_url).query.split('&')
    this_result = []
    for this_item in this_query:
        item_parts = this_item.split('=')
        this_field = item_parts[0]
        this_value = '='.join(item_parts[1:])
        this_result.append([this_field, this_value])
    return this_result


def merge_titles(title1, title2):
    title1_parts = title1.split()
    title2_parts = title2.split()
    new_title_parts = extract_exact(title1_parts, title2_parts)
    return ' '.join(new_title_parts)


def merge_lists(list1, list2):
    return list(set(list1 + list2))


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))


'''---[ BEGIN CONVERSION ]---'''


print('Creating database backup.')
copyfile ('data/SpiderWeb.db', 'data/SpiderWeb.db.ORIG')
print('Database backed up as data/SpiderWeb.db.ORIG.')


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
            fault TEXT DEFAULT 'none', \
            CONSTRAINT unique_page UNIQUE(domain, url));")
db.commit()


print('Adding forms table to the database.')
cur.execute("CREATE TABLE IF NOT EXISTS forms ( \
            id INTEGER PRIMARY KEY, \
            page INTEGER, \
            field TEXT DEFAULT 'none', \
            examples TEXT DEFAULT 'none', \
            CONSTRAINT unique_field UNIQUE(page, field));")
db.commit()


print('Creating dictionary of domains.')
cur.execute('SELECT domain, id FROM onions;')
res = cur.fetchall()
domains = {}
for item in res:
    (domain, domain_id) = item
    domains[domain] = domain_id


print('Collecting urls from database.')
cur.execute('SELECT url, title, fault FROM urls;')
urls = cur.fetchall()


print('Processing urls and populating pages.')
records = 0
for item in urls:
    (url, page_title, url_fault) = item
    page_title = 'none' if page_title == 'Unknown' else page_title
    domain = get_domain(url)
    domain_id = domains[domain]
    # First, let's add the page information.
    page = get_page(url)
    cur.execute('SELECT title FROM pages \
                WHERE url = ? AND domain = ?;',
                [page, domain_id])
    res = cur.fetchall()
    if(res == []):
        page_title = 'Unknown' if page_title == '' else page_title
        cur.execute('INSERT OR IGNORE INTO pages \
                    (domain, url, title, fault) VALUES ( \
                    ?, ?, ?, ?);', (domain_id, page, page_title, url_fault))
    else:
        if(url_fault != 'none'):
            cur.execute('UPDATE pages SET fault = ? \
                        WHERE url = ? AND domain = ?;',
                        [url_fault, page, domain_id])
        try:
            old_title = res[0][0]
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
    # Now, add the query information.
    link_query = get_query(url)
    for query in link_query:
        if(query == ['']):
            continue
        try:
            [field, value] = query
        except Exception as e:
            [field] = query
            value = 'none'
        # First, make sure this field is in the forms table.
        if(field == ''):
            continue
        cur.execute('INSERT OR IGNORE INTO forms \
                    (page, field) VALUES ( \
                    (SELECT id FROM pages WHERE \
                    url IS ? AND domain IS ?), ?);',
                    [page, domain_id, field])
        db.commit()

        # Next, determine what examples already exist in the database.
        # Of course, we only want to do this if there is a value to add.
        if(value == '' or value == 'none'):
            continue
        examples = ''
        cur.execute('SELECT examples FROM forms \
                    WHERE page IS (SELECT id FROM pages \
                    WHERE url IS ? AND domain IS ?) \
                    AND field IS ?;',
                    [page, domain_id, field])
        result = cur.fetchall()
        if(result[0][0] == 'none'):
            # There are currently no examples in the database.
            examples = value
        else:
            # Merge with the returned examples.
            example_list = result[0][0].split(',')
            example_list.append(value)
            examples = ','.join(unique(example_list))

        # Finally, update the examples in the database.
        cur.execute('UPDATE forms SET examples = ? WHERE \
                    page IS (SELECT id FROM pages WHERE \
                    url IS ? AND domain IS ?) AND field IS ?;',
                    [examples, page, domain_id, field])
        db.commit()
    records += 1

print('Removing faults from 300-series pages and urls.')
cur.execute('UPDATE urls SET fault = "none", \
            date = "1900-01-01 00:00" \
            WHERE fault IN (301, 302, 303, 307);')
cur.execute('UPDATE pages SET fault = "none" \
            WHERE fault IN (301, 302, 303, 307);')
db.commit()

print('{} records processed.'.format(records))
print('Changes saved. Closing database.')
db.close()
print('Done!')
