# Useful functions.

import random
import requests
from hashlib import sha1
from libs.logging import logger
from urllib.parse import urlsplit, urlunsplit

# Let's use the default Tor Browser Bundle UA:
agent = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'

# Just to prevent some SSL errors.
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += \
    ':ECDHE-ECDSA-AES128-GCM-SHA256'


def merge_titles(title1, title2):
    logger.log('Merging titles: {} and {}'.format(title1, title2), 'debug')
    title1_parts = title1.split()
    title2_parts = title2.split()
    new_title_parts = extract_exact(title1_parts, title2_parts)
    new_title = ' '.join(new_title_parts)
    logger.log('New title: {}'.format(new_title), 'debug')
    return new_title


def merge_urls(url1, url2):
    url1 = '' if url1 is None else url1
    # Split up url1 and url into their component parts.
    (ascheme, anetloc, apath, aquery, afragment) = urlsplit(url1)
    (uscheme, unetloc, upath, uquery, ufragment) = urlsplit(url2)
    scheme = ascheme if ascheme is not '' else uscheme
    netloc = anetloc if anetloc is not '' else unetloc
    try:
        if apath[0] == '/':
            # The path starts at root.
            newpath = apath
        elif apath[0] == '.':
            # The path starts in either the current directory or a
            # higher directory.
            short = upath[:upath.rindex('/') + 1]
            split_apath = apath.split('/')
            apath = '/'.join(split_apath[1:])
            if split_apath[0] == '.':
                # Targeting the current directory.
                short = '/'.join(short.split('/')[:-1])
            elif split_apath[0] == '..':
                # Targeting the previous directory.
                traverse = -2
                while apath[0:3] == '../':
                    split_apath = apath.split('/')
                    apath = '/'.join(split_apath[1:])
                    traverse -= 1
                try:
                    short = '/'.join(short.split('/')[:traverse])
                except Exception as e:
                    short = '/'
            newpath = '/'.join([short, apath])
        else:
            # The path is just a page name.
            short = upath[:upath.rindex('/')]
            newpath = '/'.join([short, apath])
    except Exception as e:
        newpath = upath
    query = aquery
    fragment = ''
    link = urlunsplit((scheme, netloc, newpath, query, fragment))
    return link


def get_hash(data):
    # Get the sha1 hash of the provided data. Data must be binary-encoded.
    return sha1(data).hexdigest()


def get_tor_session():
    # Create a session that's routed through Tor.
    session = requests.session()
    session.headers.update({'User-Agent': agent})
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return session


def get_type(headers):
    # What's the content type of the page we're checking?
    try:
        return headers['Content-Type'].split('/')[0]
    except Exception as e:
        return None


def get_my_ip(sess, max_tries=5):
    # If a session is passed, it will be tor and we'll use that.
    sites = [
        'https://api.ipify.org',
        'https://ipapi.co/ip',
        'https://icanhazip.com/',
        'https://wtfismyip.com/text'
    ]
    while max_tries > 0:
        try:
            if sess:
                r = sess.get(random.choice(sites), timeout=5)
                if r.status_code == 200:
                    return r.text
            else:
                r = requests.get(random.choice(sites), timeout=5)
                if r.status_code == 200:
                    return r.text
        except requests.Timeout:
            max_tries -= 1
            continue
    # if we are here, this failed!
    return False


def extract_exact(list1, list2):
    # Return the common items from both lists.
    return [item for item in list1 if any(scan == item for scan in list2)]


def prune_exact(items, scan_list):
    # Return all items from items list that match no items in scan_list.
    return [item for item in items
            if not any(scan == item for scan in scan_list)]


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))
