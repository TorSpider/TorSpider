#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    ______________________________________________________________________
   |                         |                  |                         |
   |                   +-----^--TorSpider-v0.7--^-----+                   |
   |                   |  Crawling the Invisible Web  |                   |
   |                   +------------------------------+                   |
   |                                                                      |
   | TorSpider employs an army of spiders to explore Tor hidden services, |
   | seeking to uncover and catalogue the deepest reaches of the darknet. |
    ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
    # +----------------------------------------+ #
    # |       Beware, ye who enter here:       | #
    # |     The Invisible Web is rife with     | #
    # | wondrous and terrible things. It is no | #
    # |  place for the squeamish or the faint  | #
    # |    of heart. Here there be dragons!    | #
    # +----------------------------------------+ #

"""

import configparser
import json
import logging
import multiprocessing as mp
import os
import random
import sys
import time
import urllib.parse
from datetime import date, timedelta
from hashlib import sha1
from logging.handlers import TimedRotatingFileHandler
from urllib.parse import urlsplit, urlunsplit

import names
import requests

from libs.parsers import *

'''---[ GLOBAL VARIABLES ]---'''

# The current release version.
version = '0.7'

# Let's use the default Tor Browser Bundle UA:
agent = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'

# Just to prevent some SSL errors.
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += \
    ':ECDHE-ECDSA-AES128-GCM-SHA256'

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

'''---[ CLASS DEFINITIONS ]---'''


class Spider:
    def __init__(self):
        self.api_url = api_url
        self.headers = self.__gen_api_header()
        self.session = get_tor_session()

    @staticmethod
    def __gen_api_header():
        # Create a header for the API connection.
        myhead = dict()
        myhead['Content-Type'] = 'application/json'
        myhead['Authorization'] = 'Token {}'.format(api_key)
        myhead['Authorization-Node'] = api_node
        return myhead

    def __add_onion(self, domain):
        # Add an onion to the backend DB.
        log('Adding onion: {}'.format(domain), 'debug')
        # Add the domain and the name of the node that found it.
        data = {
            "domain": domain,
            "last_node": node_name
        }
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'onions',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 201:
            # If created then it returns the object data.
            log('Added successfully: {}'.format(domain), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_url(self, domain, url):
        # Add a url to the backend DB.
        log('Adding url: {}'.format(url), 'debug')
        # Add the url as well as the domain to which it is attached.
        data = {
            "domain": domain,
            "url": url
        }
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'urls',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 201:
            # If created then it returns the object data.
            log('Added successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_page(self, domain, url):
        # Add a page to the backend DB.
        log('Adding page: {}'.format(url), 'debug')
        # Add the page as well as the domain to which it belongs.
        data = {
            "domain": domain,
            "url": url
        }
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'pages',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 201:
            # If created then it returns the object data.
            log('Added successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_link(self, domain_from, domain_to):
        # Add a link to the backend DB.
        log('Adding link: {}->{}'.format(domain_from, domain_to), 'debug')
        # Add both the origin (domain_from) and destination (domain_to)
        # of the link.
        data = {
            "domain_from": domain_from,
            "domain_to": domain_to
        }
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'links',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 201:
            # If created then it returns the object data.
            log('Added successfully: {}->{}'.format(domain_from, domain_to),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_form(self, url, field):
        # Add a form field to the backend DB.
        log('Adding Form Field: {} Url: {}'.format(field, url), 'debug')
        # Add the field as well as the page ID to which it belongs.
        data = {
            "page": url,
            "field": field
        }
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'forms',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 201:
            # If created then it returns the object data.
            log('Added successfully: Field: {}, Url: {}'.format(field, url),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __update_onions(self, domain, data):
        # Update some information about a domain.
        log("Updating onion: {} data: {}".format(
            domain, json.dumps(data)), 'debug')
        # Filter which onion to update based on its domain.
        query = {"filters": [
            {
                "op": "eq",
                "name": "domain",
                "val": domain
            }]}
        data['q'] = query
        # Send the requested patch to the database API.
        r = requests.patch(
            self.api_url + 'onions',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 200:
            # if updated it returns the object data.
            log('Updated successfully: {}'.format(domain), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            log('Update failed: {}'.format(domain), 'debug')
            return {}

    def __update_urls(self, url, data):
        # Update some information about a URL.
        log("Updating url: {} data: {}".format(url, json.dumps(data)), 'debug')
        # Filter which url to update.
        query = {"filters": [
            {
                "op": "eq",
                "name": "url",
                "val": url
            }]}
        data['q'] = query
        # Send the requested patch to the database API.
        r = requests.patch(
            self.api_url + 'urls',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 200:
            # if updated it returns the object data.
            log('Updated successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            log('Update failed: {}'.format(url), 'debug')
            return {}

    def __update_pages(self, url, data):
        # Update some information about a page.
        log("Updating page: {} data: {}".format(url, json.dumps(data)),
            'debug')
        # Filter which page to update.
        query = {"filters": [
            {
                "op": "eq",
                "name": "url",
                "val": url
            }]}
        data['q'] = query
        # Send the requested patch to the database API.
        r = requests.patch(
            self.api_url + 'pages',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 200:
            # if updated it returns the object data.
            log('Updated successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            log('Update failed: {}'.format(url), 'debug')
            return {}

    def __update_forms(self, url, field, data):
        # Update some information about a form field.
        log("Updating form: Field: {} Url: {} data: {}".format(
            field, url, json.dumps(data)), 'debug')
        # Filter which form field to update.
        query = {"filters": [
            {
                "op": "eq",
                "name": "page",
                "val": url
            }, {
                "op": "eq",
                "name": "field",
                "val": field
            }]}
        data['q'] = query
        # Send the requested patch to the database API.
        r = requests.patch(
            self.api_url + 'forms',
            headers=self.headers,
            data=json.dumps(data),
            verify=False)
        if r.status_code == 200:
            # if updated it returns the object data.
            log('Updated successfully: Field: {} Url: {}'.format(field, url),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            log('Updated failed: Field: {} Url: {}'.format(field, url),
                'debug')
            return {}

    def __get_query(self, endpoint, query):
        # Request data from the backend API.
        log("Running GET Query on endpoint: {}".format(endpoint), 'debug')
        # Send the request for information from the API.
        r = requests.get(
            self.api_url + endpoint + '?q=' + urllib.parse.quote_plus(
                json.dumps(query)),
            headers=self.headers,
            verify=False)
        if r.status_code == 200:
            # If successful then it returns the object data.
            log('GET Query successful for endpoint: {}'.format(endpoint),
                'debug')
            return json.loads(r.text).get('objects')
        elif r.status_code == 401:
            # Unauthorized.
            log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def add_to_queue(self, link_url, origin_domain):
        # Add a URL to the database to be scanned.
        log("Attempting to add a onion url to the queue: {}".format(link_url),
            'debug')

        # First, fix any potential issues with the url (fragmentation, etc.).
        link_url = self.fix_url(link_url)
        log("Fixed url is: {}".format(link_url), 'debug')

        # Next, get the url's domain.
        link_domain = self.get_domain(link_url)
        log("Link domain is: {}".format(link_domain), 'debug')

        # Ensure that the domain is a legitimate .onion domain.
        if '.onion' not in link_domain or '.onion.' in link_domain:
            log("Link domain: {} is not an onion site, ignoring.".format(
                link_domain), 'debug')
            return

        # Add the url, domain and link to the database.
        # TODO: Check if onion/url/link already exist before adding them.
        self.__add_onion(link_domain)
        self.__add_url(link_domain, link_url)
        self.__add_link(origin_domain, link_domain)

    def crawl(self):
        # TODO: Optimize to remove redundant updates to API.
        log("Ready to explore!", 'info')
        time_to_sleep = False
        while not time_to_sleep:
            # To stop the script, simply create an empty file called 'sleep'
            # in the directory where TorSpider.py resides.
            if os.path.exists('sleep'):
                # If the 'sleep' file is detected, TorSpider knows that it
                # is time to sleep.
                time_to_sleep = True
            else:
                # Ask the API for a url to scan.
                next_url_info = self.__get_query(
                        'next', {"node_name": node_name})
                if not next_url_info:
                    # There are currently no urls to scan.
                    log('We found no urls to check, sleeping for 5 seconds.',
                        'debug')
                    # Wait thirty seconds before trying again.
                    time.sleep(30)
                    continue
                if 'domain' in next_url_info.keys() \
                        and 'url' in next_url_info.keys() \
                        and 'domain_info' in next_url_info.keys():
                    log('Found next url: {}'.format(
                        next_url_info.get('domain')), 'debug')
                    domain = next_url_info['domain']
                    domain_info = next_url_info['domain_info']
                    url = self.fix_url(next_url_info['url'])
                else:
                    # No links to process. This should be rare...
                    log('We found no urls to check, sleeping for 5 seconds.',
                        'debug')
                    time.sleep(5)
                    continue
                tries = domain_info.get('tries', 0)
                last_node = domain_info.get('last_node', 'none')

                if last_node == node_name and tries > 0:
                    log('I was the last node to scan this url, skipping.',
                        'debug')
                    # This was scanned by this node last. Let's avoid this.
                    continue

                # Update the scan date for this domain.
                update_data = {
                    "scan_date": date.today().strftime('%Y-%m-%d'),
                    "last_node": node_name
                }
                self.__update_onions(domain, update_data)

                # Check to see if it's an http/https link.
                if not self.is_http(url):
                    # It's not. Skip it.
                    log('Skipping non-http site.', 'debug')
                    self.set_fault(url, 'non-http')
                    continue

                url_offline = False
                try:
                    # Retrieve the page's headers.
                    log('Getting head of url: {}'.format(url), 'debug')
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
                    if head.status_code in redirect_codes:
                        # The url results in a redirection.
                        log('Found a redirection url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        self.set_fault(url, str(head.status_code))
                        try:
                            # Let's grab the redirected url and add it to
                            # the database.
                            location = head.headers['location']
                            log('Found redirection url: {}'.format(location),
                                'debug')
                            new_url = self.merge_urls(location, url)
                            # Add the new url to the database.
                            self.add_to_queue(new_url, domain)
                            continue
                        except Exception as e:
                            log("{}: couldn't find redirect. ({})".format(
                                str(head.status_code), url), 'error')
                            continue
                    elif head.status_code in fault_codes:
                        # The url results in a fault.
                        log('Found a fault url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        self.set_fault(url, str(head.status_code))
                        continue
                    elif head.status_code in no_fault_codes:
                        log('Found a problem url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        # The url results in a problem, but not a fault.
                        continue
                    elif head.status_code not in good_codes:
                        log('Found a unknown status url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        # Unknown status. I'll add more status_code options
                        # as they arise.
                        self.set_fault(url, str(head.status_code))
                        log("Unknown status code {}: {}".format(
                            head.status_code, url), 'error')
                        continue

                    # Update the database to show that we've scanned this url
                    # today, to set the last_online date, and to reset the
                    # offline_scans to zero.
                    data = {
                        "date": date.today().strftime('%Y-%m-%d'),
                    }
                    self.__update_urls(url, data)
                    data = {
                        "last_online": date.today().strftime('%Y-%m-%d'),
                        "tries": 0,
                        "offline_scans": 0
                    }
                    self.__update_onions(domain, data)

                    content_type = self.get_type(head.headers)
                    # We only want to scan text for links. But if we don't
                    # know what the content type is, that might result
                    # from a redirection, so we'll scan it just in case.
                    log("Found content type of url: {} as: {}".format(
                        url, content_type), 'debug')
                    if content_type != 'text' and content_type is not None:
                        # Otherwise, if we know what it is, and it's not
                        # text, don't scan it.
                        self.set_fault(url, 'type: {0}'.format(content_type))
                        continue

                    request = self.session.get(url, timeout=30)
                    if content_type is None:
                        # We're going to process the request in the same
                        # way, because we couldn't get a content type from
                        # the head.
                        content_type = self.get_type(request.headers)
                        log("Found content type of url: {} as: {}".format(
                            url, content_type), 'debug')
                        if content_type != 'text' and content_type is not None:
                            self.set_fault(url, 'type: {}'.format(
                                content_type))
                            continue

                    # We've got the site's data. This page is live, so let's
                    # process the url's data.
                    self.process_url(url, domain)

                    # Let's see if the page has changed...
                    try:
                        # Get the page's sha1 hash.
                        page_hash = self.get_hash(request.content)
                        log('Page hash of url: {} is: {}'.format(
                            url, page_hash), 'debug')

                        # Retrieve the page's last hash.
                        hash_query = {
                            "filters": [
                                {
                                    "op": "eq",
                                    "name": "url",
                                    "val": url
                                }
                            ]}
                        url_info = self.__get_query('urls', hash_query)
                        if url_info:
                            last_hash = url_info[0].get('hash')
                        else:
                            last_hash = ''
                        log('Last page hash of url: {} is: {}'.format(
                            url, last_hash), 'debug')
                        # If the hash hasn't changed, don't process the
                        # page.
                        if last_hash == page_hash:
                            log('The hashes matched, nothing has changed.',
                                'debug')
                            continue

                        # Update the page's hash in the database.
                        data = {
                            "hash": page_hash
                        }
                        log('Update hash for url: {} to: {}'.format(
                            url, page_hash), 'debug')
                        self.__update_urls(url, data)

                    except Exception as e:
                        log("Couldn't retrieve previous hash: {0}".format(url),
                            'error')
                        continue

                    # The page's HTML changed since our last scan; let's
                    # process it.
                    page_text = request.text

                    # Get the title of the page.
                    try:
                        page_title = self.get_title(page_text)
                    except Exception as e:
                        page_title = 'Unknown'
                    log('Page title for url: {} is: {}'.format(
                        url, page_title), 'debug')
                    # Set the title of the url.
                    data = {
                        "title": page_title
                    }
                    self.__update_urls(url, data)

                    # Update the page's title. First, get the old title.
                    title_query = {
                        "filters": [
                            {
                                "op": "eq",
                                "name": "url",
                                "val": url
                            }
                        ]}
                    page_info = self.__get_query('pages', title_query)
                    if page_info:
                        curr_title = page_info[0].get('title')
                    else:
                        curr_title = ''
                    if curr_title == 'Unknown':
                        curr_title = 'none'
                    log('Previous page title for url: {} was: {}'.format(
                        url, curr_title), 'debug')
                    # Now, if the title is 'none' then just save
                    # page_title. But if it's something else, we'll need to
                    # make a hybrid title based on the current title and
                    # the title of the newly-scraped page.
                    if curr_title != 'none' and curr_title:
                        page_title = self.merge_titles(curr_title, page_title)
                    page_title = ' '.join(page_title.split())
                    # If the title is now empty, just set it to Unknown.
                    page_title = 'Unknown' if page_title == '' else page_title
                    # Now, save the new title to the database, but only if
                    # the title has changed.
                    if page_title != curr_title:
                        log('Page title has changed to: {}'.format(
                            page_title), 'debug')
                        data = {
                            "title": page_title
                        }
                        self.__update_pages(url, data)

                    # Get the page's links.
                    page_links = self.get_links(page_text, url)

                    # Add the links to the database.
                    for link_url in page_links:
                        # Get the link domain.
                        self.add_to_queue(link_url, domain)

                    # Parse any forms on the page.
                    log('Parsing forms on url: {}'.format(url), 'debug')
                    page_forms = self.get_forms(page_text)

                    # Add the forms to the database.
                    for form in page_forms:
                        # Process the form's information.
                        form_dict = dict(form)

                        # Make sure the necessary fields exist.
                        # TODO: Validate that this makes sense.
                        # A lot of forms can use JavaScript and don't
                        # need these methods
                        if 'action' not in form_dict.keys():
                            form_dict['action'] = ''
                        if 'method' not in form_dict.keys():
                            form_dict['method'] = ''
                        if 'target' not in form_dict.keys():
                            form_dict['target'] = ''

                        # Get the form's action, and add it to the database.
                        action_url = self.merge_action(
                            form_dict['action'], url)
                        if '.onion' not in action_url \
                                or '.onion.' in action_url:
                            # Ignore any non-onion domain.
                            continue
                        self.add_to_queue(action_url, domain)
                        # link_domain = self.get_domain(action_url)

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
                            if key is None or key == '':
                                key = 'None'
                            if value is None or value == '':
                                value = 'None'
                            # Add the key to the database if it isn't there.
                            self.__add_form(action_url, key)
                            if value == 'None':
                                continue

                            # Retrieve the current list of examples for this
                            # particular form field.
                            example_query = {
                                "filters": [
                                    {
                                        "op": "eq",
                                        "name": "page",
                                        "val": action_url
                                    }, {
                                        "op": "eq",
                                        "name": "field",
                                        "val": key
                                    }
                                ]}
                            result = self.__get_query('forms', example_query)
                            if len(result):
                                result_examples = result[0].get('examples')
                            else:
                                result_examples = None
                            if not result_examples:
                                # We have no current values.
                                examples = value
                            else:
                                # Merge with the returned examples.
                                example_list = result_examples.split(',')
                                example_list.append(value)
                                examples = ','.join(unique(example_list))

                            # Update the examples in the database.
                            data = {
                                "examples": examples
                            }
                            self.__update_forms(action_url, key, data)

                # Parsing is complete for this page!
                except requests.exceptions.InvalidURL:
                    # The url provided was invalid.
                    log("Invalid url: {}".format(url), 'error')
                    self.set_fault(url, 'invalid url')

                except requests.exceptions.InvalidSchema:
                    # We got an invalid schema.
                    (s, n, p, q, f) = urlsplit(url)
                    for scheme in ['http', 'https']:
                        s = scheme
                        new_url = urlunsplit((s, n, p, q, f))
                        self.add_to_queue(new_url, domain)
                    self.set_fault(url, 'invalid schema')

                except requests.exceptions.SSLError as e:
                    # There was a problem with the site's SSL certificate.
                    log("SSL Error at {}: {}".format(url, e), 'error')
                    self.set_fault(url, 'Bad SSL')

                except requests.exceptions.ConnectionError:
                    # We had trouble connecting to the url.
                    # First let's make sure we're still online.
                    log("Connection error to url: {}".format(url), 'debug')
                    try:
                        tor_ip = get_my_ip(self.session)
                        if tor_ip:
                            # If we've reached this point, Tor is working.
                            tries += 1
                            if tries == 3:
                                # We've failed three times. Time to quit.
                                log('Url is offline: {}'.format(url), 'debug')
                                url_offline = True
                            else:
                                data = {
                                    "tries": tries
                                }
                                self.__update_onions(domain, data)
                    except Exception as e:
                        # We aren't connected to Tor for some reason.
                        # It might be a temporary outage, so let's wait
                        # for a little while and see if it fixes itself.
                        log('We seem to not be connected to Tor', 'debug')
                        time.sleep(5)
                        continue

                except requests.exceptions.Timeout:
                    # It took too long to load this page.
                    log('Request timed out: {}'.format(url), 'debug')
                    tries += 1
                    if tries == 3:
                        # We've failed three times. Time to quit.
                        log('Url is offline: {}'.format(url), 'debug')
                        url_offline = True
                    else:
                        data = {
                            "tries": tries
                        }
                        self.__update_onions(domain, data)

                except requests.exceptions.TooManyRedirects as e:
                    # Redirected too many times. Let's not keep trying.
                    self.set_fault(url, 'redirect')

                except requests.exceptions.ChunkedEncodingError as e:
                    # Server gave bad chunk. This might not be a permanent
                    # problem, so let's just roll with it.
                    continue

                except MemoryError as e:
                    # Whatever it is, it's way too big.
                    log('Ran out of memory: {}'.format(url), 'error')
                    self.set_fault(url, 'memory error')

                except NotImplementedError as e:
                    log("I don't know what this means: {} - {}".format(e, url),
                        'error')

                except Exception as e:
                    log('Unknown exception: {}'.format(e), 'error')
                    raise

                if url_offline:
                    # Set the domain to offline.
                    log('Setting url as offline: {}'.format(url), 'debug')
                    data = {
                        "online": False,
                        "tries": 0
                    }
                    self.__update_onions(domain, data)
                    # In order to reduce the frequency of scans for
                    # offline pages, set the scan date ahead by the
                    # number of times the page has been scanned
                    # offline. To do this, first retrieve the
                    # number of times the page has been scanned
                    # offline.
                    offline_query = {
                        "filters": [
                            {
                                "op": "eq",
                                "name": "domain",
                                "val": domain
                            }
                        ]}
                    result = self.__get_query('onions', offline_query)
                    if result:
                        offline_scans = result[0].get('offline_scans', 0)
                    else:
                        offline_scans = 0
                    # Next, increment the scans by one.
                    offline_scans += 1
                    # Now, set the interval we'll be using for the date.
                    interval = offline_scans
                    new_date = (date.today() +
                                timedelta(days=interval)).strftime('%Y-%m-%d')
                    # Save the new value to the database.
                    data = {
                        "offline_scans": offline_scans,
                        "scan_date": new_date
                    }
                    self.__update_onions(domain, data)
        log("Going to sleep!", 'info')

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
        return '.'.join(self.defrag_domain(
            urlsplit(url).netloc).split('.')[-2:])

    @staticmethod
    def get_forms(data):
        # Get the data from all forms on the page.
        parse = FormParser()
        parse.feed(data)
        return parse.forms

    @staticmethod
    def get_hash(data):
        # Get the sha1 hash of the provided data. Data must be binary-encoded.
        return sha1(data).hexdigest()

    @staticmethod
    def get_links(data, url):
        log("Getting links for url: {}".format(url), 'debug')
        # Given HTML input, return a list of all unique links.
        parse = ParseLinks()
        parse.feed(data)
        links = []
        domain = urlsplit(url)[1]
        for link in parse.output_list:
            try:
                if link is None:
                    # Skip empty links.
                    continue
                # Remove any references to the current directory. ('./')
                while './' in link:
                    link = link.replace('./', '')
                # Split the link into its component parts.
                (scheme, netloc, path, query, fragment) = urlsplit(link)
                # Fill in empty schemes.
                scheme = 'http' if scheme is '' else scheme
                # Fill in empty paths.
                path = '/' if path is '' else path
                if netloc is '' and '.onion' in path.split('/')[0]:
                    # The urlparser mistook the domain as part of the path.
                    netloc = path.split('/')[0]
                    try:
                        path = '/'.join(path.split('/')[1:])
                    except Exception as e:
                        path = '/'
                # Fill in empty domains.
                netloc = domain if netloc is '' else netloc
                fragment = ''
                if '.onion' not in netloc or '.onion.' in netloc:
                    # We are only interested in links to other .onion domains,
                    # and we don't want to include links to onion redirectors.
                    continue
                links.append(urlunsplit(
                    (scheme, netloc, path, query, fragment)))
            except Exception as e:
                log('Link exception: {} -- {}'.format(e, link), 'error')
        # Make sure we don't return any duplicates!
        unique_links = unique(links)
        log("Found {} links in url: {}".format(
            len(unique_links), url), 'debug')
        return unique_links

    @staticmethod
    def get_query(url):
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

    @staticmethod
    def get_title(data):
        # Given HTML input, return the title of the page.
        parse = ParseTitle()
        parse.feed(data)
        return parse.title.strip()

    @staticmethod
    def get_type(headers):
        # What's the content type of the page we're checking?
        try:
            return headers['Content-Type'].split('/')[0]
        except Exception as e:
            return None

    @staticmethod
    def is_http(url):
        # Determine whether the link is an http/https scheme or not.
        (scheme, netloc, path, query, fragment) = urlsplit(url)
        return True if 'http' in scheme else False

    @staticmethod
    def merge_action(action, url):
        action = '' if action is None else action
        # Split up the action and url into their component parts.
        (ascheme, anetloc, apath, aquery, afragment) = urlsplit(action)
        (uscheme, unetloc, upath, uquery, ufragment) = urlsplit(url)
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

    @staticmethod
    def merge_titles(title1, title2):
        log('Merging titles: {} and {}'.format(title1, title2), 'debug')
        title1_parts = title1.split()
        title2_parts = title2.split()
        new_title_parts = extract_exact(title1_parts, title2_parts)
        new_title = ' '.join(new_title_parts)
        log('New title: {}'.format(new_title), 'debug')
        return new_title

    @staticmethod
    def merge_lists(list1, list2):
        # Merge two lists together without duplicates.
        return list(set(list1 + list2))

    @staticmethod
    def merge_urls(url1, url2):
        log('Merging url: {} and url: {}'.format(url1, url2), 'debug')
        # Merge the new url (url1) into the original url (url2).
        (ns, nn, np, nq, nf) = urlsplit(url1)  # Split first url into parts.
        (us, un, up, uq, uf) = urlsplit(url2)  # Split second url into parts.
        us = us if ns == '' else ns  # Try to use the new url's scheme.
        un = un if nn == '' else nn  # Try to use the new url's netloc.
        final_url = urlunsplit((us, un, np, nq, nf))  # Join them and return.
        log('Merged url: {}'.format(final_url), 'debug')
        return final_url

    def process_url(self, link_url, link_domain):
        # When a URL shows up valid, add its information to the database.
        log('Processing url: {}'.format(link_url), 'debug')
        link_url = self.fix_url(link_url)
        log('Fixed link url: {}'.format(link_url), 'debug')
        link_query = self.get_query(link_url)
        log('Link query: {}'.format(link_query), 'debug')
        try:
            # Insert the url into its various tables.
            log('Add url: {} domain: {} into page table.'.format(
                link_domain, link_url), 'debug')
            self.__add_page(link_domain, link_url)
            # Process and add any discovered form data.
            for item in link_query:
                if item == ['']:
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
                if field == '':
                    continue
                # First, make sure this field is in the forms table.
                self.__add_form(link_url, field)

                # Next, determine what examples already exist in the database.
                # Only do this if we have a value to add.
                if value == '' or value == 'none':
                    continue
                example_query = {
                    "filters": [
                        {
                            "op": "eq",
                            "name": "page",
                            "val": link_url
                        }, {
                            "op": "eq",
                            "name": "field",
                            "val": field
                        }
                    ]}
                result = self.__get_query('forms', example_query)
                if len(result):
                    result_examples = result[0].get('examples')
                else:
                    result_examples = None
                if not result_examples:
                    # We don't have any current values.
                    examples = value
                else:
                    # Merge with the returned examples.
                    example_list = result_examples.split(',')
                    example_list.append(value)
                    examples = ','.join(unique(example_list))

                # Finally, update the examples in the database.
                data = {
                    "examples": examples
                }
                self.__update_forms(link_url, field, data)

        except Exception as e:
            # There was an error saving the link to the database.
            log("Couldn't add link to database: {0}".format(e), 'error')
            raise

    def set_fault(self, url, fault):
        log('Setting fault status for url: {} fault: {}'.format(url, fault),
            'debug')
        # Update the url and page faults.
        data = {
            "fault": fault
        }
        self.__update_urls(url, data)
        self.__update_pages(url, data)


'''---[ FUNCTIONS ]---'''


def extract_exact(list1, list2):
    # Return the common items from both lists.
    return [item for item in list1 if any(scan == item for scan in list2)]


def get_tor_session():
    # Create a session that's routed through Tor.
    session = requests.session()
    session.headers.update({'User-Agent': agent})
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    return session


def setup_logger(loglevel):
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    my_logger = logging.getLogger()
    os.makedirs(os.path.join(script_dir, 'logs'), exist_ok=True)
    filehandler = TimedRotatingFileHandler(
        os.path.join(script_dir, 'logs', 'TorSpider.log'),
        when='midnight', backupCount=7, interval=1)
    filehandler.setFormatter(formatter)
    my_logger.addHandler(filehandler)
    if log_to_console:
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(formatter)
        my_logger.addHandler(consolehandler)
    my_logger.setLevel(logging.getLevelName(loglevel))
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return my_logger


def log(line, level):
    message = '{}: {}'.format(
        mp.current_process().name,
        line)
    message = ' '.join(message.split())  # Remove unnecessary whitespace.
    if level.lower() == 'debug':
        logger.debug(message)
    elif level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'critical`':
        logger.critical(message)


def prune_exact(items, scan_list):
    # Return all items from items list that match no items in scan_list.
    return [item for item in items
            if not any(scan == item for scan in scan_list)]


def unique(items):
    # Return the same list without duplicates)
    return list(set(items))


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


'''---[ SCRIPT ]---'''

if __name__ == '__main__':
    if not os.path.exists('spider.cfg'):
        # If we don't yet have a configuration file, make one and tell the
        # user to set it up before continuing.
        default_config = configparser.RawConfigParser()
        default_config.optionxform = lambda option: option
        default_config['TorSpider'] = {
            'LogToConsole': 'True',
        }
        default_config['API'] = {
            'API_URL': 'http://127.0.0.1/api/',
            'API_KEY': 'Configure_api_key',
            'API_NODE': 'Configure_api_node'
        }
        default_config['LOGGING'] = {
            'loglevel': 'INFO'
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
        node_name = config['API'].get('API_NODE')
        api_url = config['API'].get('API_URL')
        api_key = config['API'].get('API_KEY')
        api_node = config['API'].get('API_NODE')
        log_level = config['LOGGING'].get('loglevel')
    except Exception as e:
        print('Could not parse spider.cfg. Please verify its syntax.')
        sys.exit(0)
    logger = setup_logger(log_level)
    log('-' * 40, 'info')
    log('TorSpider v{} Initializing...'.format(version), 'info')

    # Create a Tor session and check if it's working.
    log("Establishing Tor connection...", 'info')
    session = get_tor_session()
    try:
        local_ip = get_my_ip(None)
        if not local_ip:
            log("Cannot determine local IP address.", 'error')
            sys.exit(0)
        tor_ip = get_my_ip(session)
        if not tor_ip:
            log("Cannot determine tor IP address.", 'error')
            sys.exit(0)
        if local_ip == tor_ip:
            log("Tor connection failed: IPs match.", 'error')
            log('-' * 40, 'info')
            sys.exit(0)
        else:
            log("Tor connection established.", 'info')
    except Exception as e:
        log("Tor connection failed: {}".format(e), 'error')
        log('-' * 40, 'info')
        sys.exit(0)

    # Awaken the spiders!
    Spiders = []
    Spider_Procs = []

    log('Waking the Spiders...', 'info')
    # There are enough names here for a 32-core processor.
    my_names = []

    # We'll start two processes for every processor.
    count = (mp.cpu_count() * 2)
    for x in range(count):
        spider = Spider()
        spider_proc = mp.Process(target=spider.crawl)
        spider_proc.name = names.get_first_name()
        while spider_proc.name in my_names:
            spider_proc.name = names.get_first_name()
        my_names.append(spider_proc.name)
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
    log('The Spiders have gone to sleep. ZzZzz...', 'info')
    log('-' * 40, 'info')
