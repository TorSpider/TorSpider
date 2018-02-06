import requests
import psycopg2 as sql
import multiprocessing as mp
from datetime import datetime

# Let's use the default Tor Browser Bundle UA:
agent = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'


def check_db():
    log('Checking the database...')
    # First, we'll set up the database connection.
    connection = sql.connect(
            "dbname='{}' user='{}' host='{}' \
            password='{}'".format(
                    postgre_dbase,
                    postgre_user,
                    postgre_host,
                    postgre_pass))
    cursor = connection.cursor()

    # Check to see if the db exists.
    cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables \
                   WHERE tablename = 'links');")
    if(cursor.fetchall()[0][0] == False):
        log('Initializing new database...')

        ''' Onions: Information about each individual onion domain.
            - id:            The numerical ID of that domain.
            - domain:        The domain itself (i.e. 'google.com').
            - online:        Whether the domain was online in the last scan.
            - last_online:   The last date the page was seen online.
            - date:          The date of the last scan.
            - offline_scans: How many times the onion has scanned offline.
        '''
        cursor.execute("CREATE TABLE IF NOT EXISTS onions ( \
                        id SERIAL PRIMARY KEY, \
                        domain TEXT, \
                        online INTEGER DEFAULT '1', \
                        last_online DATE DEFAULT '1900-01-01', \
                        date DATE DEFAULT '1900-01-01', \
                        offline_scans INTEGER DEFAULT '0', \
                        CONSTRAINT unique_domain UNIQUE(domain));")

        ''' Urls: Information about each link discovered.
            - id:            The numerical ID of that url.
            - title:         The url's title.
            - domain:        The numerical ID of the url's parent domain.
            - url:           The url itself.
            - hash:          The page's sha1 hash, for detecting changes.
            - date:          The date of the last scan.
            - fault:         If there's a fault preventing scanning, log it.
        '''
        cursor.execute("CREATE TABLE IF NOT EXISTS urls ( \
                        id SERIAL PRIMARY KEY, \
                        title TEXT DEFAULT 'none', \
                        domain INTEGER, \
                        url TEXT, \
                        hash TEXT DEFAULT 'none', \
                        date DATE DEFAULT '1900-01-01', \
                        fault TEXT DEFAULT 'none', \
                        CONSTRAINT unique_url UNIQUE(domain, url));")

        ''' Pages: Information about the various pages in each domain.
            - id:            The numerical ID of the page.
            - url:           The url of the page.
            - title:         The title of the page.
            - domain:        The numerical ID of the page's parent domain.
            - fault:         If there's a fault preventing scanning, log it.
        '''
        cursor.execute("CREATE TABLE IF NOT EXISTS pages ( \
                       id SERIAL PRIMARY KEY, \
                       url TEXT, \
                       title TEXT DEFAULT 'none', \
                       domain INTEGER, \
                       fault TEXT DEFAULT 'none', \
                       CONSTRAINT unique_page UNIQUE(domain, url));")

        ''' Forms: Information about the various form fields for each page.
            - id:            The numerical ID of the form field.
            - page:          The numerical ID of the page it links to.
            - field:         The name of the form field.
            - examples:      Some examples of found values.
        '''
        cursor.execute("CREATE TABLE IF NOT EXISTS forms ( \
                       id SERIAL PRIMARY KEY, \
                       page INTEGER, \
                       field TEXT, \
                       examples TEXT DEFAULT 'none', \
                       CONSTRAINT unique_field UNIQUE(page, field));")

        ''' Links: Information about which domains connect to each other.
            - domain:        The numerical ID of the origin domain.
            - link:          The numerical ID of the target domain.
        '''
        cursor.execute('CREATE TABLE IF NOT EXISTS links ( \
                        domain INTEGER, \
                        link INTEGER, \
                        CONSTRAINT unique_link UNIQUE(domain, link));')

        # Next, we'll populate the database with some default values. These
        # pages are darknet indexes, so they should be a good starting
        # point.

        # The Uncensored Hidden Wiki
        # http://zqktlwi4fecvo6ri.onion/wiki/Main_Page
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'zqktlwi4fecvo6ri.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '1', \
                       'http://zqktlwi4fecvo6ri.onion/wiki/Main_Page');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '1', \
                       '/wiki/Main_Page');")

        # OnionDir
        # http://auutwvpt2zktxwng.onion/index.php
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'auutwvpt2zktxwng.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '2', \
                       'http://auutwvpt2zktxwng.onion/index.php');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '2', \
                       '/index.php');")

        # Wiki links
        # http://wikilink77h7lrbi.onion/
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'wikilink77h7lrbi.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '3', \
                       'http://wikilink77h7lrbi.onion/');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '3', \
                       '/');")

        # Deep Web Links
        # http://wiki5kauuihowqi5.onion/
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'wiki5kauuihowqi5.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '4', \
                       'http://wiki5kauuihowqi5.onion/');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '4', \
                       '/');")

        # OnionDir Deep Web Directory
        # http://dirnxxdraygbifgc.onion/
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'dirnxxdraygbifgc.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '5', \
                       'http://dirnxxdraygbifgc.onion/');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '5', \
                       '/');")

        # The Onion Crate
        # http://7cbqhjnlkivmigxf.onion/
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       '7cbqhjnlkivmigxf.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '6', \
                       'http://7cbqhjnlkivmigxf.onion/');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '6', \
                       '/');")

        # Fresh Onions
        # http://zlal32teyptf4tvi.onion/
        cursor.execute("INSERT INTO onions (domain) VALUES ( \
                       'zlal32teyptf4tvi.onion');")
        cursor.execute("INSERT INTO urls (domain, url) VALUES ( \
                       '7', \
                       'http://zlal32teyptf4tvi.onion/');")
        cursor.execute("INSERT INTO pages (domain, url) VALUES ( \
                       '7', \
                       '/');")

        # Save our changes.
        connection.commit()

        log("Database initialized.")
    else:
        # The database already exists.
        log("Database loaded.")
    connection.close()


def combine(message, args=()):
    return 'Message: {}\t| Args: {}'.format(message, args)


def extract_exact(list1, list2):
    # Return the common items from both lists.
    return [item for item in list1
            if any(scan == item for scan in list2)]


def get_timestamp():
    # Get a time stamp that fits PostgreSQL's DATE format.
    return datetime.now().strftime('%Y-%m-%d')


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
    message = '{}| {}: {}'.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            mp.current_process().name,
            line)
    message = ' '.join(message.split()) # Remove unnecessary whitespace.
    if(log_to_console):
        # Print to the screen if log_to_console is enabled.
        print(message)
    # Append the message to the logfile.
    f = open('run.log', 'a')
    f.write('{}\n'.format(message))
    f.close()


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))
