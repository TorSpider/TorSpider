#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' TorSpider – A script to explore the darkweb.
    -------------------by Christopher Steffen---

    TorSpider will explore the darkweb to discover as many onion sites as
    possible, storing them all in a database along with whatever additional
    information can be found. It will also store data regarding which sites
    connected to which other sites, allowing for some relational mapping.

    The database generated by TorSpider will be accessible via a secondary
    script which will create a web interface for exploring the saved data.
'''

import os
import sys
import time
import random
import requests
import sqlite3 as sql
from hashlib import sha1
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit
from multiprocessing import Process, cpu_count, current_process


'''---GLOBAL VARIABLES---'''


# Should we log to the console?
log_to_console = True

# Let's use the default Tor Browser Bundle UA:
agent = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'

# Just to prevent some SSL errors.
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += \
                                              ':ECDHE-ECDSA-AES128-GCM-SHA256'


'''---CLASS DEFINITIONS---'''


class parse_links(HTMLParser):
    # Parse given HTML for all a.href links.
    def __init__(self):
        HTMLParser.__init__(self)
        self.output_list = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.output_list.append(dict(attrs).get('href'))


class parse_title(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.match = False
        self.title = ''

    def handle_starttag(self, tag, attributes):
        self.match = True if tag == 'title' else False

    def handle_data(self, data):
        if self.match:
            self.title = data
            self.match = False


'''---FUNCTION DEFINITIONS---'''


def crawl():
    ''' This function is the meat of the program, doing all the heavy lifting
        of crawling the website and scraping up all the juicy data therein.
    '''
    log("{}: I'm awake! Good morning!".format(current_process().name))
    while(True):
        if(os.path.exists('sleep')):
            # The kill-switch is creating a file called 'sleep'.
            log("{}: I'm sleepy. Good night!".format(current_process().name))
            return
        try:
            # Query the database for a random link that hasn't been scanned in
            # 7 days or whose domain was marked offline more than a day ago.
            query = db_cmd("SELECT `domain`, `url` FROM `pages` \
                          WHERE `date` < DATETIME('now', '-7 day') \
                          OR `domain` IN (\
                                SELECT `id` FROM `onions` \
                                WHERE `online` IS '0' \
                                AND `date` < DATETIME('now', '-1 day')\
                          ) ORDER BY RANDOM() LIMIT 1;")
            try:
                (domain_id, url) = query[0]
            except Exception as e:
                # No links to process.
                time.sleep(1)
                continue

            # Grab that link's root domain.
            query = db_cmd("SELECT `domain` FROM `onions` \
                           WHERE `id` IS ?;", (domain_id, ))
            domain = query[0][0]

            # Update the scan date for this page and domain.
            db_cmd("UPDATE `pages` SET `date` = ? \
                   WHERE `url` IS ? AND `domain` \
                   IS ?;", (get_timestamp(), url, domain_id))
            db_cmd("UPDATE `onions` SET `date` = ? \
                   WHERE `id` IS ?;", (get_timestamp(), domain_id))

            # Retrieve the page.
            req = session.get(url)

            # Did we get the page successfully?
            if(req.status_code == 404):
                # This page doesn't exist. Delete it from the database.
                db_cmd("DELETE FROM `pages` WHERE `url` IS ?;", (url, ))
                log("404 - {}".format(url))
                continue
            elif(req.status_code != 200):
                # Some other status.
                # I'll add more status_code options as they arise.
                log("{} - {}".format(req.status_code, url))
                continue

            # We've got the site's data. Let's see if it's changed...
            try:
                # Get the page's sha1 hash.
                page_hash = get_hash(req.content)

                # Retrieve the page's last hash.
                query = db_cmd("SELECT `hash` FROM `pages` WHERE \
                               `domain` IS ? AND `url` IS ?;",
                               (domain_id, url))
                last_hash = query[0][0]

                # If the hash hasn't changed, don't bother processing it.
                if(last_hash == page_hash):
                    continue

            except Exception as e:
                log("Couldn't retrieve previous hash: {}".format(url))
                continue

            # The page's HTML changed since our last scan; let's process it.
            page_text = req.text

            # Get the title of the page.
            page_title = get_title(page_text)

            # Get the page's links.
            page_links = get_links(page_text, url)

            ''' To add a page to the database:

                Add the domain to the `onions` table.
                INSERT OR IGNORE INTO `onions` (`domain`)
                    VALUES ('link_domain');

                Add the page to the `pages` table.
                INSERT OR IGNORE INTO `pages` (`domain`, `url`)
                    VALUES (
                        (SELECT `id` FROM `onions`
                            WHERE `domain` = 'link_domain'),
                        'link_page'
                    );

                Link the two domains in the `links` table.
                INSERT OR IGNORE INTO `links` (`domain`, `link`)
                    VALUES (
                        'domain_id',
                        (SELECT `id` FROM `onions`
                            WHERE `domain` = 'link_domain')
                    );
            '''

            # Add the links to the database.
            for l in page_links:
                # Get the link domain.
                link_domain = urlsplit(l)[1]
                # Get the link page.
                link_page = l[l.find(link_domain) + len(link_domain):]
                try:
                    # Insert the new domain into the onions table.
                    db_cmd("INSERT OR IGNORE INTO `onions` (`domain`) \
                           VALUES (?);", (link_domain, ))
                    # Insert the new link into the pages table.
                    db_cmd("INSERT OR IGNORE INTO `pages` (`domain`, `url`) \
                           VALUES ((SELECT `id` FROM `onions` WHERE \
                           `domain` = ?), ?);", (link_domain, link_page))
                    # Insert the new connection between domains.
                    db_cmd("INSERT OR IGNORE INTO `links` (`domain`, `link`) \
                           VALUES (?, (SELECT `id` FROM `onions` WHERE \
                           `domain` = ?));", (domain_id, link_domain))
                except Exception as e:
                    # There was an error saving the link to the database.
                    log('Failed to save to database: {} -> {}'.format(url, l))
                    continue
            # Parsing is complete for this page!

        except IndexError as e:
            # Something went wrong with SQL.
            log("IndexError: {}".format(e))

        except requests.InvalidURL:
            # The url provided was invalid.
            log("Invalid url: {}".format(url))
            db_cmd("DELETE FROM `pages` WHERE `url` IS ?;", (url, ))

        except requests.ConnectionError:
            # We had trouble connecting to the url.
            log("Site offline: {}".format(url))
            # Set the domain to offline.
            db_cmd("UPDATE `onions` SET `online` = '0' \
                   WHERE `id` IS ?", (domain_id, ))
            # Make sure we don't keep scanning the pages.
            db_cmd("UPDATE `pages` SET `date` = ? \
                   WHERE `domain` = ?;", (get_timestamp, domain_id))


def db_cmd(command, args=()):
    # This function executes commands in the database.
    output = None
    connection = sql.connect('SpiderWeb.db')
    cursor = connection.cursor()
    try:
        command = command.strip()
        cursor.execute(command, args)
        if(command.upper().startswith("SELECT")):
            output = cursor.fetchall()
        connection.commit()
        connection.close()
        return output
    except sql.Error as e:
        log("SQL Error: {}".format(e))
        connection.close()
        return None


def extract_exact(items, scan_list):
    # Return all items from items list that match items in scan_list.
    return [item for item in items
            if any(scan == item for scan in scan_list)]


def extract_fuzzy(items, scan_list):
    # Return all items from items list that match items in scan_list.
    return [item for item in items
            if any(scan in item for scan in scan_list)]


def get_hash(data):
    # Get the sha1 hash of the provided data. Data must be binary-encoded.
    return sha1(data).hexdigest()


def get_links(data, url):
    # Given HTML input, return a list of all unique links.
    parse = parse_links()
    parse.feed(data)
    links = []
    domain = urlsplit(url)[1]
    for link in parse.output_list:
        if(link is None):
            # Skip empty links.
            continue
        # Remove any references to the current directory. ('./')
        link = link.replace('./', '')
        # Split the link into its component parts.
        (scheme, netloc, path, query, fragment) = urlsplit(link)
        # Fill in empty schemes.
        scheme = 'http' if scheme is '' else scheme
        # Fill in empty paths.
        path = '/' if path is '' else path
        if(netloc is '' and '.onion' in path.split('/')[0]):
            # The urlparser mistook the domain as part of the path.
            netloc = path.split('/')[0]
            try:
                path = '/'.join(path.split('/')[1:])
            except Exception as e:
                path = '/'
        # Fill in empty domains.
        netloc = domain if netloc is '' else netloc
        fragment = ''
        if('onion' not in netloc):
            # We are only interested in links to other .onion domains.
            continue
        if('http' in scheme):
            # We only want http or https links, not irc or others.
            links.append(urlunsplit((scheme, netloc, path, query, fragment)))
    # Make sure we don't return any duplicates!
    return unique(links)


def get_timestamp():
    # Get a time stamp that fits Sqlite3's DATETIME format.
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_title(data):
    # Given HTML input, return the title of the page.
    parse = parse_title()
    parse.feed(data)
    return parse.title.strip()


def get_tor_session():
    # Create a session that's routed through Tor.
    session = requests.session()
    session.headers.update({'User-Agent': agent})
    session.proxies = {
            'http':  'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
    return session


def log(line):
    if(log_to_console):
        print('{} - {}'.format(get_timestamp(), line))
    f = open('spider.log', 'a')
    f.write("{}\n".format(line))
    f.close()


def prune_exact(items, scan_list):
    # Return all items from items list that match no items in scan_list.
    return [item for item in items
            if not any(scan == item for scan in scan_list)]


def prune_fuzzy(items, scan_list):
    # Return all items from items list that match no items in scan_list.
    return [item for item in items
            if not any(scan in item for scan in scan_list)]


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))


'''---MAIN---'''


if __name__ == '__main__':
    log('TorSpider initializing...')

    # Create a Tor session and check if it's working.
    log("Establishing Tor connection...")
    session = get_tor_session()
    try:
        local_ip = requests.get('http://api.ipify.org/').text
        tor_ip = session.get('http://api.ipify.org/').text
        if(local_ip == tor_ip):
            log("Tor connection failed: IPs match.")
            sys.exit(0)
        else:
            log("Tor connection established.")
    except Exception as e:
        log("Tor connection failed: {}".format(e))
        sys.exit(0)

    # If the database doesn't exist, create a new one.
    if(not os.path.exists('SpiderWeb.db')):
        log("Initializing new database...")

        # First, we'll set up the database structure.

        ''' Onions: Information about each individual onion domain.
                - id:       The numerical ID of that domain.
                - domain:   The domain itself (i.e. 'google.com').
                - online:   Whether the domain was online as of the last scan.
                - date:     The date of the last scan.
                - info:     Any additional information known about the domain.
        '''
        db_cmd("CREATE TABLE IF NOT EXISTS `onions` ( \
                        `id` INTEGER PRIMARY KEY, \
                        `domain` TEXT, \
                        `online` INTEGER DEFAULT '1', \
                        `date` DATETIME DEFAULT '1986-02-02 00:00:01', \
                        `info` TEXT DEFAULT 'none', \
                        CONSTRAINT unique_domain UNIQUE(`domain`));")

        ''' Pages: Information about each link discovered.
                - id:       The numerical ID of that page.
                - title:    The page's title.
                - domain:   The numerical ID of the page's parent domain.
                - url:      The URL for the page.
                - hash:     The page's sha1 hash, for detecting changes.
                - date:     The date of the last scan.
        '''
        db_cmd("CREATE TABLE IF NOT EXISTS `pages` ( \
                        `id` INTEGER PRIMARY KEY, \
                        `title` TEXT DEFAULT 'none', \
                        `domain` INTEGER, \
                        `url` TEXT, \
                        `hash` TEXT DEFAULT 'none', \
                        `date` DATETIME DEFAULT '1986-02-02 00:00:01', \
                        CONSTRAINT unique_page UNIQUE(`domain`, `url`));")

        ''' Links: Information about which domains are connected to each other.
                - domain:   The numerical ID of the origin domain.
                - link:     The numerical ID of the target domain.
        '''
        db_cmd('CREATE TABLE IF NOT EXISTS `links` ( \
                        `domain` INTEGER, \
                        `link` INTEGER, \
                        CONSTRAINT unique_link UNIQUE(`domain`, `link`));')

        # Next, we'll populate the database with some default values. These
        # pages are darknet indexes, so they should be a good starting point.

        # The Uncensored Hidden Wiki
        # http://zqktlwi4fecvo6ri.onion/wiki/Main_Page
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'zqktlwi4fecvo6ri.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '1', \
                    'http://zqktlwi4fecvo6ri.onion/wiki/Main_Page' \
               );")

        # OnionDir
        # http://auutwvpt2zktxwng.onion/index.php
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'auutwvpt2zktxwng.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '2', \
                    'http://auutwvpt2zktxwng.onion/index.php' \
               );")

        # Wiki links
        # http://wikilink77h7lrbi.onion/
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'wikilink77h7lrbi.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '3', \
                    'http://wikilink77h7lrbi.onion/' \
               );")

        # Deep Web Links
        # http://wiki5kauuihowqi5.onion/
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'wiki5kauuihowqi5.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '4', \
                    'http://wiki5kauuihowqi5.onion/' \
               );")

        # OnionDir Deep Web Directory
        # http://dirnxxdraygbifgc.onion/
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'dirnxxdraygbifgc.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '5', \
                    'http://dirnxxdraygbifgc.onion/' \
               );")

        # The Onion Crate
        # http://7cbqhjnlkivmigxf.onion/
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    '7cbqhjnlkivmigxf.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '6', \
                    'http://7cbqhjnlkivmigxf.onion/' \
               );")

        # Fresh Onions
        # http://zlal32teyptf4tvi.onion/
        db_cmd("INSERT INTO `onions` (`domain`) VALUES ( \
                    'zlal32teyptf4tvi.onion' \
                );")
        db_cmd("INSERT INTO `pages` (`domain`, `url`) VALUES ( \
                    '7', \
                    'http://zlal32teyptf4tvi.onion/' \
               );")

        log("Database initialized.")
    else:
        # The database already exists.
        log("Existing database initialized.")

    # Now we're ready to start crawling.
    log("Awaken the spiders!!!")
    # Sixteen names for processors with up to 8 cores.
    names = ['Webster', 'Spinette', 'Crowley', 'Leggy',
             'Harry', 'Terry', 'Aunt Tula', 'Cheryl',
             'Bubbles', 'Jumpy', 'Gunther', 'Vinny',
             'Squatch', 'Wolf', 'Trudy', 'Nancy',
             'Lester', 'Ginny', 'Bitsy', 'Itsy',
             'Ronald', 'Gardenia', 'Frank', 'Casper',
             'Chester', 'Maude', 'Denny', 'Hank',
             'Bruce', 'Uma', 'Lizzy', 'Dizzy']
    procs = []
    for _ in range(cpu_count() * 2):  # We'll release 2 spiders per processor.
        random.shuffle(names)
        proc = Process(target=crawl)
        proc.name = names.pop()
        procs.append(proc)
        proc.start()
        # Delay each spider so that it doesn't step on the others' feet.
        time.sleep(1)

    for proc in procs:
        proc.join()

    # The spiders are all 'asleep' now.
    try:
        os.unlink('sleep')
    except Exception as e:
        pass
    log("The spiders are all sleeping now. ZzZzz...")
