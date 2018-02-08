#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' ______________________________________________________________________
   |                         |                  |                         |
   |                   +-----^--TorSpider-v0.5--^-----+                   |
   |                   |  Crawling the Invisible Web  |                   |
   |                   +----------------by CMSteffen--+                   |
   |                                                                      |
   | TorSpider employs an army of spiders to explore Tor hidden services, |
   | seeking to uncover and catalogue the deepest reaches of the darknet. |
    ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
'''

import os                    # +----------------------------------------+ #
import sys                   # |       Beware, ye who enter here:       | #
import time                  # |     The Invisible Web is rife with     | #
import random                # | wondrous and terrible things. It is no | #
import requests              # |  place for the squeamish or the faint  | #
import configparser          # |    of heart. Here there be dragons!    | #
import psycopg2 as sql       # +----------------------------------------+ #
from hashlib import sha1
from libs.parsers import *
import multiprocessing as mp
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

'''---[ GLOBAL VARIABLES ]---'''

# The current release version.
version = '0.5'

# Let's use the default Tor Browser Bundle UA:
agent = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'

# Just to prevent some SSL errors.
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += \
                                              ':ECDHE-ECDSA-AES128-GCM-SHA256'

'''---[ CLASS DEFINITIONS ]---'''


class Spider():
    def __init__(self):
        self.session = get_tor_session()

    def add_url(self, link_url, domain_id):
        link_url = self.fix_url(link_url)
        link_page = self.get_page(link_url)
        link_query = self.get_query(link_url)
        link_domain = self.get_domain(link_url)
        if('.onion' not in link_domain
           or '.onion.' in link_domain):
            # We don't want to add a link to a non-onion domain.
            return
        try:
            # Insert the new domain.
            self.db("INSERT INTO onions (domain) VALUES (%s) \
                    ON CONFLICT DO NOTHING;", (link_domain, ))
            # We'll need the domain id of the new link.
            link_domain_id = self.db(
                    "SELECT id FROM onions WHERE domain = %s;",
                    (link_domain, ))[0][0]
            # Insert the url into its various tables.
            self.db("INSERT INTO urls (domain, url) VALUES \
                    (%s, %s) ON CONFLICT DO NOTHING; \
                    INSERT INTO pages (domain, url) VALUES \
                    (%s, %s) ON CONFLICT DO NOTHING; \
                    INSERT INTO links (domain, link) VALUES \
                    (%s, %s) ON CONFLICT DO NOTHING;",
                    (link_domain_id, link_url, link_domain_id,
                     link_page, domain_id, link_domain_id))
            # Process and add any discovered form data.
            for item in link_query:
                if(item == ['']):
                    # Ignore empty form data.
                    continue
                try:
                    [field, value] = item
                except Exception as e:
                    # Sometimes they have a field without a query.
                    # e.g. /index.php?do=
                    [field] = item
                    value = 'none'
                # We don't need to process it if the field is empty.
                if(field == ''):
                    continue
                # First, make sure this field is in the forms table.
                self.db('INSERT INTO forms \
                        (page, field) VALUES ( \
                        (SELECT id FROM pages WHERE \
                        url = %s AND domain = %s), %s) \
                        ON CONFLICT DO NOTHING;',
                        (link_page, link_domain_id, field))

                # Next, determine what examples already exist in the database.
                # Only do this if we have a value to add.
                if(value == '' or value == 'none'):
                    continue
                examples = ''
                result = self.db('SELECT examples FROM forms \
                                 WHERE page = (SELECT id FROM pages \
                                 WHERE url = %s AND domain = %s) \
                                 AND field = %s;',
                                 (link_page, link_domain_id, field))
                if(result == [] or result[0][0] == 'none'):
                    # We don't have any current values.
                    examples = value
                else:
                    # Merge with the returned examples.
                    example_list = result[0][0].split(',')
                    example_list.append(value)
                    examples = ','.join(unique(example_list))

                # Finally, update the examples in the database.
                self.db('UPDATE forms SET examples = %s WHERE \
                        page = (SELECT id FROM pages WHERE \
                        url = %s AND domain = %s) AND field = %s;',
                        (examples, link_page, link_domain_id, field))

        except Exception as e:
            # There was an error saving the link to the
            # database.
            log("Couldn't add link to database: {}".format(
                    e))
            raise

    def crawl(self):
        log("Ready to explore!")
        time_to_sleep = False
        while(not time_to_sleep):
            if(os.path.exists('sleep')):
                time_to_sleep = True
            else:
                # Query the database for a random link that hasn't been
                # scanned in 7 days, or whose domain was last scanned more
                # than a day ago, or whose domain was found offline by a
                # different node but hasn't been marked offline yet.
                query = self.db("SELECT domain, url FROM urls WHERE \
                                fault = 'none' AND (date < \
                                (CURRENT_DATE - INTERVAL '7 days') OR \
                                domain IN (SELECT id FROM onions \
                                WHERE (online = '0' AND date < \
                                (CURRENT_DATE - INTERVAL '1 day')) OR \
                                (online = '1' AND tries != '0'))) \
                                ORDER BY RANDOM() LIMIT 1;")
                try:
                    (domain_id, url) = query[0]
                    url = self.fix_url(url)
                except Exception as e:
                    # No links to process. This should be rare...
                    time.sleep(5)
                    continue

                # See if this onion has been scanned offline by another node.
                query = self.db("SELECT tries, last_node FROM onions \
                                WHERE id = %s;", [domain_id])
                try:
                    (tries, last_node) = query[0]
                except Exception as e:
                    tries = 0
                    last_node = 'none'

                if(last_node == node_name and tries > 0):
                    # This was scanned by this node last. Let's avoid this.
                    continue

                # Update the scan date for this domain.
                self.db("UPDATE onions SET date = CURRENT_DATE, \
                        last_node = %s WHERE id = %s;", (
                                node_name, domain_id, ))

                # Check to see if it's an http/https link.
                if(not self.is_http(url)):
                    # It's not.
                    self.set_fault(url, 'non-http')
                    continue

                url_offline = False
                try:
                    # Retrieve the page's headers.
                    head = self.session.head(url, timeout=30)

                    # Redirect codes: These status codes redirect to other
                    # pages, so grab those other pages and scan them
                    # instead.
                    redirect_codes = [301, 302, 303, 307, 308]

                    # Fault codes: These status codes imply that there was
                    # something wrong with the page being requested, such as
                    # being non-existent. Don't rescan pages with these
                    # codes.
                    fault_codes = [400, 401, 403, 404, 405, 406, 410,
                                   413, 414, 444, 451, 495, 496,
                                   500, 501, 502, 505, 508, 511]

                    # No-Fault codes: These imply that something temporarily
                    # went wrong, but it's possible that it might work in
                    # the future. Just skip to the next url.
                    no_fault_codes = [408, 421, 423, 429, 503, 504]

                    # Good codes: These are the codes we want to see when we
                    # are accessing a web service.
                    good_codes = [200, 201]

                    # Did we get the page successfully?
                    if(head.status_code in redirect_codes):
                        # The url results in a redirection.
                        self.set_fault(url, str(head.status_code))
                        try:
                            # Let's grab the redirected url and add it to
                            # the database.
                            location = head.headers['location']
                            new_url = self.merge_urls(location, url)
                            # Add the new url to the database.
                            self.add_url(new_url, domain_id)
                            continue
                        except Exception as e:
                            log("{}: couldn't find redirect. ({})".format(
                                    str(head.status_code), url))
                            continue
                    elif(head.status_code in fault_codes):
                        # The url results in a fault.
                        self.set_fault(url, str(head.status_code))
                        continue
                    elif(head.status_code in no_fault_codes):
                        # The url results in a problem, but not a fault.
                        continue
                    elif(head.status_code not in good_codes):
                        # Unknown status. I'll add more status_code options
                        # as they arise.
                        self.set_fault(url, str(head.status_code))
                        log("Unknown status code {}: {}".format(
                                head.status_code, url))
                        continue

                    # Update the database to show that we've scanned this url
                    # today, to set the last_online date, and to reset the
                    # offline_scans to zero.
                    self.db("UPDATE urls SET date = CURRENT_DATE \
                            WHERE url = %s AND domain = %s; \
                            UPDATE onions SET last_online = CURRENT_DATE, \
                            tries = 0 WHERE id = %s; \
                            UPDATE onions SET offline_scans = '0' \
                            WHERE id = %s;",
                            (url, domain_id, domain_id, domain_id))

                    content_type = self.get_type(head.headers)
                    # We only want to scan text for links. But if we don't
                    # know what the content type is, that might result
                    # from a redirection, so we'll scan it just in case.
                    if(content_type != 'text' and content_type is not None):
                        # Otherwise, if we know what it is, and it's not
                        # text, don't scan it.
                        self.set_fault(url, 'type: {}'.format(
                                content_type))
                        continue

                    request = self.session.get(url, timeout=30)
                    if(content_type is None):
                        # We're going to process the request in the same
                        # way, because we couldn't get a content type from
                        # the head.
                        content_type = self.get_type(request.headers)
                        if(content_type != 'text'
                           and content_type is not None):
                            self.set_fault(url, 'type: {}'.format(
                                    content_type))
                            continue

                    # We've got the site's data. Let's see if it's
                    # changed...
                    try:
                        # Get the page's sha1 hash.
                        page_hash = self.get_hash(request.content)

                        # Retrieve the page's last hash.
                        query = self.db("SELECT hash FROM urls WHERE \
                                        domain = %s AND url = %s;",
                                        (domain_id, url))
                        last_hash = query[0][0]

                        # If the hash hasn't changed, don't process the
                        # page.
                        if(last_hash == page_hash):
                            continue

                        # Update the page's hash in the database.
                        self.db('UPDATE urls SET hash = %s \
                                WHERE domain = %s AND url = %s;',
                                (page_hash, domain_id, url))

                    except Exception as e:
                        log("Couldn't retrieve previous hash: {}".format(
                                url))
                        continue

                    # The page's HTML changed since our last scan; let's
                    # process it.
                    page_text = request.text

                    # Get the title of the page.
                    try:
                        page_title = self.get_title(page_text)
                    except Exception as e:
                        log('Bad title: {}'.format(url))
                        self.set_fault(url, 'bad title')
                        continue
                    # Set the title of the url.
                    self.db('UPDATE urls SET title = %s \
                            WHERE url = %s;', (page_title, url))

                    # Update the title of the page.
                    new_title = str(page_title)
                    # First, get the old title.
                    curr_title = self.db('SELECT title FROM pages WHERE \
                                         url = %s AND domain = %s;',
                                         (self.get_page(url),
                                          domain_id))[0][0]
                    if(curr_title == 'Unknown'):
                        curr_title = 'none'

                    # Now, if the title is 'none' then just save
                    # page_title. But if it's something else, we'll need to
                    # make a hybrid title based on the current title and
                    # the title of the newly-scraped page.
                    if(curr_title != 'none'):
                        new_title = self.merge_titles(curr_title,
                                                      page_title)
                    new_title = ' '.join(new_title.split())
                    # If the title is now empty, just set it to Unknown.
                    new_title = 'Unknown' if new_title == '' else new_title
                    # Now, save the new title to the database, but only if
                    # the title has changed.
                    if(new_title != curr_title):
                        self.db('UPDATE pages SET title = %s \
                                WHERE url = %s AND domain = %s;',
                                (new_title, self.get_page(url), domain_id))

                    # Get the page's links.
                    page_links = self.get_links(page_text, url)

                    # Add the links to the database.
                    for link_url in page_links:
                        # Get the link domain.
                        self.add_url(link_url, domain_id)

                    # Parse any forms on the page.
                    page_forms = self.get_forms(page_text)

                    # Add the forms to the database.
                    for form in page_forms:
                        # Process the form's information.
                        form_dict = dict(form)

                        # Make sure the necessary fields exist.
                        if('action' not in form_dict.keys()):
                            form_dict['action'] = ''
                        if('method' not in form_dict.keys()):
                            form_dict['method'] = ''
                        if('target' not in form_dict.keys()):
                            form_dict['target'] = ''

                        # Get the form's action, and add it to the database.
                        action = self.merge_action(form_dict['action'], url)
                        if('.onion' not in action or '.onion.' in action):
                            # Ignore any non-onion domain.
                            continue
                        self.add_url(action, domain_id)
                        link_domain_id = self.db(
                                "SELECT id FROM onions WHERE \
                                domain = %s;",
                                (self.get_domain(action), ))[0][0]

                        # Get the action's page.
                        form_page = self.get_page(action)

                        # Now we'll need to add each input field and its
                        # possible default values.
                        fields = {}

                        # Process text fields.
                        text_fields = form_dict['text_fields']
                        for key in text_fields.keys():
                            fields[key] = text_fields[key]

                        # Process radio buttons.
                        radio_buttons = form_dict['radio_buttons']
                        for key in radio_buttons.keys():
                            rb_values = radio_buttons[key]
                            rb_values = prune_exact(rb_values, ['', None])
                            fields[key] = ','.join(rb_values)

                        # Process checkboxes.
                        checkboxes = form_dict['checkboxes']
                        for key in checkboxes.keys():
                            cb_values = checkboxes[key]
                            cb_values = prune_exact(cb_values, ['', None])
                            fields[key] = ','.join(cb_values)

                        # Process dropdowns.
                        dropdowns = form_dict['dropdowns']
                        for key in dropdowns.keys():
                            dd_values = dropdowns[key]
                            dd_values = prune_exact(dd_values, ['', None])
                            fields[key] = ','.join(dd_values)

                        # Process text areas.
                        text_areas = form_dict['text_areas']
                        for key in text_areas.keys():
                            fields[key] = text_areas[key]

                        # Process dates.
                        for d in form_dict['dates']:
                            fields[d] = ''

                        # Process datetimes.
                        for dt in form_dict['datetimes']:
                            fields[dt] = ''

                        # Process months.
                        for month in form_dict['months']:
                            fields[month] = ''

                        # Process numbers.
                        for number in form_dict['numbers']:
                            fields[number] = ''

                        # Process ranges.
                        for r in form_dict['ranges']:
                            fields[r] = ''

                        # Process times.
                        for t in form_dict['times']:
                            fields[t] = ''

                        # Process weeks.
                        for week in form_dict['weeks']:
                            fields[week] = ''

                        # Process the retrieved fields and add them to the
                        # database.
                        for key in fields.keys():
                            value = fields[key]
                            if(key is None or key == ''):
                                key = 'None'
                            if(value is None or value == ''):
                                value = 'None'
                            # Add the key to the database if it isn't there.
                            self.db('INSERT INTO forms \
                                    (page, field) VALUES ( \
                                    (SELECT id FROM pages WHERE \
                                    url = %s AND domain = %s), %s) \
                                    ON CONFLICT DO NOTHING;',
                                    (form_page, link_domain_id, key))
                            if(value == 'None'):
                                continue

                            # Retrieve the current list of examples for this
                            # particular form field.
                            examples = ''
                            result = self.db('SELECT examples FROM forms \
                                             WHERE page = (SELECT id FROM \
                                             pages WHERE url = %s AND \
                                             domain = %s) AND field = %s;',
                                             (form_page, link_domain_id, key))
                            if(result == [] or result[0][0] == 'none'):
                                # We have no current values.
                                examples = value
                            else:
                                # Merge with the returned examples.
                                example_list = result[0][0].split(',')
                                example_list.append(value)
                                examples = ','.join(unique(example_list))

                            # Update the examples in the database.
                            self.db('UPDATE forms SET examples = %s WHERE \
                                    page = (SELECT id FROM pages WHERE \
                                    url = %s AND domain = %s) AND field = %s;',
                                    (examples, form_page, link_domain_id, key))

                    # Parsing is complete for this page!
                except requests.exceptions.InvalidURL:
                    # The url provided was invalid.
                    log("Invalid url: {}".format(url))
                    self.set_fault(url, 'invalid url')

                except requests.exceptions.InvalidSchema:
                    # We got an invalid schema.
                    (s, n, p, q, f) = urlsplit(url)
                    if('http' in s):
                        # The scheme was likely misspelled. Add it with http
                        # and https, just in case.
                        for scheme in ['http', 'https']:
                            s = scheme
                            new_url = urlunsplit((s, n, p, q, f))
                            self.add_url(new_url, domain_id)
                    self.set_fault(url, 'invalid schema')

                except requests.exceptions.ConnectionError:
                    # We had trouble connecting to the url.
                    # First let's make sure we're still online.
                    try:
                        tor_ip = self.session.get(
                                'http://api.ipify.org/').text
                        # If we've reached this point, Tor is working.
                        tries += 1
                        if(tries == 3):
                            # We've failed three times. Time to quit.
                            url_offline = True
                        else:
                            self.db('UPDATE onions SET tries = %s \
                                    WHERE id = %s;', (tries, domain_id, ))
                    except Exception as e:
                        # We aren't connected to Tor for some reason.
                        # It might be a temporary outage, so let's wait
                        # for a little while and see if it fixes itself.
                        time.sleep(5)
                        continue

                except requests.exceptions.Timeout:
                    # It took too long to load this page.
                    tries += 1
                    if(tries == 3):
                        # We've failed three times. Time to quit.
                        url_offline = True
                    else:
                        self.db('UPDATE onions SET tries = %s \
                                WHERE id = %s;', (tries, domain_id, ))

                except requests.exceptions.TooManyRedirects as e:
                    # Redirected too many times. Let's not keep trying.
                    self.set_fault(url, 'redirect')

                except requests.exceptions.ChunkedEncodingError as e:
                    # Server gave bad chunk. This might not be a permanent
                    # problem, so let's just roll with it.
                    continue

                except requests.exceptions.SSLError as e:
                    # There was a problem with the site's SSL certificate.
                    log("SSL Error at {}: {}".format(url, e))
                    self.set_fault(url, 'Bad SSL')

                except MemoryError as e:
                    # Whatever it is, it's way too big.
                    log('Ran out of memory: {}'.format(url))
                    self.set_fault(url, 'memory error')

                except NotImplementedError as e:
                    log("I don't know what this means: {} - {}".format(
                            e, url))

                except Exception as e:
                    log('Unknown exception: {}'.format(e))
                    raise

                if(url_offline is True):
                    # Set the domain to offline.
                    self.db("UPDATE onions SET online = '0', \
                            tries = 0 WHERE id = %s;", (
                                    domain_id, ))
                    # In order to reduce the frequency of scans for
                    # offline pages, set the scan date ahead by the
                    # number of times the page has been scanned
                    # offline. To do this, first retrieve the
                    # number of times the page has been scanned
                    # offline.
                    offline_scans = self.db(
                            'SELECT offline_scans FROM onions \
                            WHERE id = %s;', (domain_id, )
                    )[0][0]
                    # Next, increment the scans by one.
                    offline_scans += 1
                    # Save the new value to the database.
                    self.db("UPDATE onions SET offline_scans = %s \
                            WHERE id = %s;", (
                                    offline_scans, domain_id))
                    # Now, set the interval we'll be using for the
                    # date.
                    interval = ('1 day' if offline_scans == 1
                                else '{} days'.format(
                                        offline_scans))
                    # Then update the urls and onions scan dates.
                    self.db("UPDATE urls SET date = \
                            (CURRENT_DATE + INTERVAL %s) \
                            WHERE domain = %s; UPDATE onions \
                            SET date = (CURRENT_DATE + INTERVAL %s) \
                            WHERE id = %s;",
                            (interval, domain_id, interval, domain_id))
        log("Going to sleep!")

    def db(self, query, args=[]):
        # Request information from the database.
        connection = sql.connect(
                "dbname='{}' user='{}' host='{}' \
                password='{}'".format(
                        postgre_dbase,
                        postgre_user,
                        postgre_host,
                        postgre_pass))
        cursor = connection.cursor()
        while(True):
            try:
                cursor.execute(query, args)
                try:
                    output = cursor.fetchall()
                except Exception as e:
                    output = None
                connection.commit()
                connection.close()
                return output
            except sql.extensions.TransactionRollbackError:
                time.sleep(0.1)
            except sql.OperationalError:
                # The connection to the database failed. Wait a while
                # and try again.
                connection.close()
                time.sleep(0.1)
                connection = sql.connect(
                        "dbname='{}' user='{}' host='{}' \
                        password='{}'".format(
                                postgre_dbase,
                                postgre_user,
                                postgre_host,
                                postgre_pass))
                cursor = connection.cursor()
            except Exception as e:
                if(e != 'database is locked'
                   and e != 'deadlock detected'):
                    connection.close()
                    log("SQL Error: {}".format(
                            combine(query, args)))
                    raise
                    return None
                else:
                    # Let's see if the database frees up.
                    time.sleep(0.1)

    def defrag_domain(self, domain):
        # Defragment the given domain.
        domain_parts = domain.split('.')
        # Onion domains don't have strange symbols or numbers in them, so be
        # sure to remove any of those just in case someone's obfuscating
        # domains for whatever reason.
        domain_parts[-2] = ''.join(
                ch for ch in domain_parts[-2] if ch.isalnum())
        domain = '.'.join(domain_parts)
        return domain

    def fix_url(self, url):
        # Fix obfuscated urls.
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        netloc = self.defrag_domain(netloc)
        url = urlunsplit((scheme, netloc, path, query, fragment))
        return url.replace('\x00', '')

    def get_domain(self, url):
        # Get the defragmented domain of the given url.
        # Omit subdomains. Rather than having separate records for urls
        # like sub1.onionpage.onion and sub2.onionpage.onion, just keep them
        # all under onionpage.onion.
        return '.'.join(
                self.defrag_domain(
                        urlsplit(url).netloc
                ).split('.')[-2:]
        )

    def get_forms(self, data):
        # Get the data from all forms on the page.
        parse = FormParser()
        parse.feed(data)
        return parse.forms

    def get_hash(self, data):
        # Get the sha1 hash of the provided data. Data must be binary-encoded.
        return sha1(data).hexdigest()

    def get_links(self, data, url):
        # Given HTML input, return a list of all unique links.
        parse = ParseLinks()
        parse.feed(data)
        links = []
        domain = urlsplit(url)[1]
        for link in parse.output_list:
            try:
                if(link is None):
                    # Skip empty links.
                    continue
                # Remove any references to the current directory. ('./')
                while('./' in link):
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
                if('.onion' not in netloc or '.onion.' in netloc):
                    # We are only interested in links to other .onion domains,
                    # and we don't want to include links to onion redirectors.
                    continue
                links.append(urlunsplit(
                        (scheme, netloc, path, query, fragment)))
            except Exception as e:
                log('Link exception: {} -- {}'.format(e, link))
        # Make sure we don't return any duplicates!
        return unique(links)

    def get_page(self, url):
        # Get the page from a link.
        return urlsplit(url).path

    def get_query(self, url):
        # Get the query information from the url.
        # Queries look like: /page.php?field=value&field2=value2
        # Splitting along the & we get field=value, field2=value2
        query = urlsplit(url).query.split('&')
        result = []
        for item in query:
            # Splitting each query along the '=' we get
            # [[field1, value], [field2, value2]]
            item_parts = item.split('=')
            field = item_parts[0]
            value = '='.join(item_parts[1:])
            result.append([field, value])
        return result

    def get_title(self, data):
        # Given HTML input, return the title of the page.
        parse = ParseTitle()
        parse.feed(data)
        return parse.title.strip()

    def get_type(self, headers):
        # What's the content type of the page we're checking?
        try:
            return headers['Content-Type'].split('/')[0]
        except Exception as e:
            return None

    def is_http(self, url):
        # Determine whether the link is an http/https scheme or not.
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        return True if 'http' in scheme else False

    def merge_action(self, action, url):
        action = '' if action is None else action
        # Split up the action and url into their component parts.
        (ascheme, anetloc, apath, aquery, afragment) = urlsplit(action)
        (uscheme, unetloc, upath, uquery, ufragment) = urlsplit(url)
        scheme = ascheme if ascheme is not '' else uscheme
        netloc = anetloc if anetloc is not '' else unetloc
        newpath = ''
        try:
            if(apath[0] == '/'):
                # The path starts at root.
                newpath = apath
            elif(apath[0] == '.'):
                # The path starts in either the current directory or a
                # higher directory.
                short = upath[:upath.rindex('/') + 1]
                split_apath = apath.split('/')
                apath = '/'.join(split_apath[1:])
                if(split_apath[0] == '.'):
                    # Targeting the current directory.
                    short = '/'.join(short.split('/')[:-1])
                elif(split_apath[0] == '..'):
                    # Targeting the previous directory.
                    traverse = -2
                    while(apath[0:3] == '../'):
                        split_apath = apath.split('/')
                        apath = '/'.join(split_apath[1:])
                        traverse -= 1
                    try:
                        short = '/'.join(short.split('/')[:traverse])
                    except:
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
        return(link)

    def merge_titles(self, title1, title2):
        title1_parts = title1.split()
        title2_parts = title2.split()
        new_title_parts = extract_exact(title1_parts, title2_parts)
        return ' '.join(new_title_parts)

    def merge_lists(list1, list2):
        # Merge two lists together without duplicates.
        return list(set(list1 + list2))

    def merge_urls(self, url1, url2):
        # Merge the new url (url1) into the original url (url2).
        (ns, nn, np, nq, nf) = urlsplit(url1)  # Split first url into parts.
        (us, un, up, uq, uf) = urlsplit(url2)  # Split second url into parts.
        us = us if ns == '' else ns  # Try to use the new url's scheme.
        un = un if nn == '' else nn  # Try to use the new url's netloc.
        return urlunsplit((us, un, np, nq, nf))  # Join them and return.

    def set_fault(self, url, fault):
        # Update the url and page faults.
        page = self.get_page(url)
        domain = self.get_domain(url)
        self.db('UPDATE urls SET fault = %s WHERE url = %s; \
                UPDATE pages SET fault = %s WHERE url = %s AND domain = \
                (SELECT id FROM onions WHERE domain = %s);',
                (fault, url, fault, page, domain))


'''---[ FUNCTIONS ]---'''


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
    if(cursor.fetchall()[0][0] is False):
        log('Initializing new database...')

        ''' Onions: Information about each individual onion domain.
            - id:            The numerical ID of that domain.
            - domain:        The domain itself (i.e. 'google.com').
            - online:        Whether the domain was online in the last scan.
            - last_online:   The last date the page was seen online.
            - date:          The date of the last scan.
            - last_node:     The last node to scan this domain.
            - tries:         How many attempts have been made to connect?
            - offline_scans: How many times the onion has scanned offline.
        '''
        cursor.execute("CREATE TABLE IF NOT EXISTS onions ( \
                        id SERIAL PRIMARY KEY, \
                        domain TEXT, \
                        online INTEGER DEFAULT '1', \
                        last_online DATE DEFAULT '1900-01-01', \
                        date DATE DEFAULT '1900-01-01', \
                        last_node TEXT DEFAULT 'none', \
                        tries INTEGER DEFAULT '0', \
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
    message = ' '.join(message.split())  # Remove unnecessary whitespace.
    if(log_to_console):
        # Print to the screen if log_to_console is enabled.
        print(message)
    # Append the message to the logfile.
    f = open('run.log', 'a')
    f.write('{}\n'.format(message))
    f.close()


def prune_exact(items, scan_list):
    # Return all items from items list that match no items in scan_list.
    return [item for item in items
            if not any(scan == item for scan in scan_list)]


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))


'''---[ SCRIPT ]---'''

if __name__ == '__main__':
    if(not os.path.exists('spider.cfg')):
        # If we don't yet have a configuration file, make one and tell the
        # user to set it up before continuing.
        default_config = configparser.RawConfigParser()
        default_config.optionxform = lambda option: option
        default_config['TorSpider'] = {
                'LogToConsole': 'True',
                'Daemonize': 'False',
                'NodeName': 'REPLACE_ME'
        }
        default_config['PostgreSQL'] = {
                'Username': 'username',
                'Password': 'password',
                'Hostname': '127.0.0.1',
                'Database': 'TorSpider'
        }
        with open('spider.cfg', 'w') as config_file:
            default_config.write(config_file)
        print('Default configuration stored in spider.cfg.')
        print('Please edit spider.cfg before running TorSpider again.')
        sys.exit(0)

    # Load the configuration file.
    try:
        config = configparser.ConfigParser()
        config.read('spider.cfg')
        log_to_console = config['TorSpider'].getboolean('LogToConsole')
        daemonize = config['TorSpider'].getboolean('Daemonize')
        node_name = config['TorSpider'].get('NodeName')
        postgre_user = config['PostgreSQL'].get('Username')
        postgre_pass = config['PostgreSQL'].get('Password')
        postgre_host = config['PostgreSQL'].get('Hostname')
        postgre_dbase = config['PostgreSQL'].get('Database')
    except Exception as e:
        print('Could not parse spider.cfg. Please verify its syntax.')
        sys.exit(0)

    log('-' * 40)
    log('TorSpider v{} Initializing...'.format(version))

    # Create a Tor session and check if it's working.
    log("Establishing Tor connection...")
    session = get_tor_session()
    try:
        local_ip = requests.get('http://api.ipify.org/').text
        tor_ip = session.get('http://api.ipify.org/').text
        if(local_ip == tor_ip):
            log("Tor connection failed: IPs match.")
            log('-' * 40)
            sys.exit(0)
        else:
            log("Tor connection established.")
    except Exception as e:
        log("Tor connection failed: {}".format(e))
        log('-' * 40)
        sys.exit(0)

    # Make sure the database is set up.
    check_db()

    # Awaken the spiders!
    Spiders = []
    Spider_Procs = []

    log('Waking the Spiders...')
    # There are enough names here for a 32-core processor.
    names = ['Webster', 'Spinette', 'Crowley', 'Leggy',
             'Harry', 'Terry', 'Aunt Tula', 'Jumpy',
             'Wolf', 'Bubbles', 'Bitsy', 'Itsy',
             'Squatch', 'Cheryl', 'Trudy', 'Nancy',
             'Lester', 'Ginny', 'Gunther', 'Vinny',
             'Ronald', 'Gardenia', 'Frank', 'Casper',
             'Chester', 'Maude', 'Denny', 'Hank',
             'Bruce', 'Uma', 'Lizzy', 'Dizzy']

    # We'll start two processes for every processor, less one to account for
    # the scribe process.
    count = (mp.cpu_count() * 2)
    for x in range(count):
        spider = Spider()
        spider_proc = mp.Process(target=spider.crawl)
        random.shuffle(names)
        spider_proc.name = names.pop()
        Spider_Procs.append(spider_proc)
        Spiders.append(spider)
        spider_proc.start()
        # We make them sleep a second so they don't all go skittering after
        # the same url at the same time.
        time.sleep(1)

    for spider_proc in Spider_Procs:
        spider_proc.join()

    try:
        os.unlink('sleep')
    except Exception as e:
        pass
    log('The Spiders have gone to sleep. ZzZzz...')
    log('-' * 40)
