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

import os
import sys
import time
import json
import names
import configparser
import urllib.parse
from libs.functions import *
from libs.logging import logger
from datetime import date, timedelta
from urllib.parse import urlsplit, urlunsplit
from multiprocessing import cpu_count, Process
from libs.parsers import get_forms, get_links, get_title


'''---[ GLOBAL VARIABLES ]---'''

# The current release version.
version = '0.7'

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
        logger.log('Adding onion: {}'.format(domain), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully: {}'.format(domain), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_url(self, domain, url):
        # Add a url to the backend DB.
        logger.log('Adding url: {}'.format(url), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_page(self, domain, url):
        # Add a page to the backend DB.
        logger.log('Adding page: {}'.format(url), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_link(self, domain_from, domain_to):
        # Add a link to the backend DB.
        logger.log('Adding link: {}->{}'.format(domain_from, domain_to), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully: {}->{}'.format(domain_from, domain_to),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __add_form(self, url, field):
        # Add a form field to the backend DB.
        logger.log('Adding Form Field: {} Url: {}'.format(field, url), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully: Field: {}, Url: {}'.format(field, url),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def __update_onions(self, domain, data):
        # Update some information about a domain.
        logger.log("Updating onion: {} data: {}".format(
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
            verify=ssl_verify)
        if r.status_code == 200:
            # if updated it returns the object data.
            logger.log('Updated successfully: {}'.format(domain), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            logger.log('Update failed: {}'.format(domain), 'debug')
            return {}

    def __update_urls(self, url, data):
        # Update some information about a URL.
        logger.log("Updating url: {} data: {}".format(url, json.dumps(data)), 'debug')
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
            verify=ssl_verify)
        if r.status_code == 200:
            # if updated it returns the object data.
            logger.log('Updated successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            logger.log('Update failed: {}'.format(url), 'debug')
            return {}

    def __update_pages(self, url, data):
        # Update some information about a page.
        logger.log("Updating page: {} data: {}".format(url, json.dumps(data)),
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
            verify=ssl_verify)
        if r.status_code == 200:
            # if updated it returns the object data.
            logger.log('Updated successfully: {}'.format(url), 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            logger.log('Update failed: {}'.format(url), 'debug')
            return {}

    def __update_forms(self, url, field, data):
        # Update some information about a form field.
        logger.log("Updating form: Field: {} Url: {} data: {}".format(
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
            verify=ssl_verify)
        if r.status_code == 200:
            # if updated it returns the object data.
            logger.log('Updated successfully: Field: {} Url: {}'.format(field, url),
                'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            logger.log('Updated failed: Field: {} Url: {}'.format(field, url),
                'debug')
            return {}

    def __get_query(self, endpoint, query):
        # Request data from the backend API.
        logger.log("Running GET Query on endpoint: {}".format(endpoint), 'debug')
        # Send the request for information from the API.
        r = requests.get(
            self.api_url + endpoint + '?q=' + urllib.parse.quote_plus(
                json.dumps(query)),
            headers=self.headers,
            verify=ssl_verify)
        if r.status_code == 200:
            # If successful then it returns the object data.
            logger.log('GET Query successful for endpoint: {}'.format(endpoint),
                'debug')
            return json.loads(r.text).get('objects')
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def add_to_queue(self, link_url, origin_domain):
        # Add a URL to the database to be scanned.
        logger.log("Attempting to add a onion url to the queue: {}".format(
                link_url), 'debug')

        # First, fix any potential issues with the url (fragmentation, etc.).
        link_url = fix_url(link_url)
        logger.log("Fixed url is: {}".format(link_url), 'debug')

        # Next, get the url's domain.
        link_domain = get_domain(link_url)
        logger.log("Link domain is: {}".format(link_domain), 'debug')

        # Ensure that the domain is a legitimate .onion domain.
        if '.onion' not in link_domain or '.onion.' in link_domain:
            logger.log("Link domain: {} not an onion site, ignoring.".format(
                    link_domain), 'debug')
            return

        # Add the url, domain and link to the database.
        # TODO: Check if onion/url/link already exist before adding them.
        self.__add_onion(link_domain)
        self.__add_url(link_domain, link_url)
        self.__add_link(origin_domain, link_domain)

    def crawl(self):
        # TODO: Optimize to remove redundant updates to API.
        logger.log("Ready to explore!", 'info')
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
                    logger.log('We found no urls to check, sleeping for 30 seconds.',
                        'debug')
                    # Wait thirty seconds before trying again.
                    time.sleep(30)
                    continue
                if 'domain' in next_url_info.keys() \
                        and 'url' in next_url_info.keys() \
                        and 'domain_info' in next_url_info.keys():
                    # We successfully retrieved a url from the API.
                    logger.log('Found next url: {}'.format(
                        next_url_info.get('domain')), 'debug')
                    domain = next_url_info['domain']
                    domain_info = next_url_info['domain_info']
                    url = fix_url(next_url_info['url'])
                else:
                    # There are currently no urls to scan.
                    logger.log('We found no urls to check, sleeping for 30 seconds.',
                        'debug')
                    # Wait thirty seconds before trying again.
                    time.sleep(30)
                    continue

                # Check if a previous domain has tried unsuccessfully
                # to connect to this domain before.
                tries = domain_info.get('tries', 0)
                last_node = domain_info.get('last_node', 'none')

                if last_node == node_name and tries > 0:
                    # This node was the last to scan this domain, and the
                    # domain was reported offline. Let's not re-scan the domain
                    # with the same node, just in case there's some problem
                    # with this node's connection.
                    logger.log('I was the last node to scan this url, skipping.',
                        'debug')
                    continue

                # Update the scan date for this domain, and set this node as
                # the last node to scan this domain.
                update_data = {
                    "scan_date": date.today().strftime('%Y-%m-%d'),
                    "last_node": node_name
                }
                self.__update_onions(domain, update_data)

                # Do not scan non-http/https links.
                if not is_http(url):
                    logger.log('Skipping non-http site.', 'debug')
                    self.set_fault(url, 'non-http')
                    continue

                # The following lists define possible response codes that a
                # server might send in reply to our request for their url.

                # Redirect codes: These status codes redirect to other pages,
                # so grab those other pages and scan them instead.
                redirect_codes = [301, 302, 303, 307, 308]

                # Fault codes: These status codes imply that there was
                # something wrong with the page being requested, such as being
                # non-existent. Don't rescan pages with these codes.
                fault_codes = [400, 401, 403, 404, 405, 406, 410,
                               413, 414, 444, 451, 495, 496,
                               500, 501, 502, 505, 508, 511]

                # No-Fault codes: These imply that something temporarily went
                # wrong, but it's possible that it might work in the future.
                # Just skip to the next url.
                no_fault_codes = [408, 421, 423, 429, 503, 504]

                # Good codes: These are the codes we want to see when we are
                # accessing a web service.
                good_codes = [200, 201]

                # Now that we've defined the possible response codes, attempt
                # to scrape the data from the provided url.
                url_offline = False
                try:
                    # Attempt to retrieve the page's headers.
                    logger.log('Getting head of url: {}'.format(url), 'debug')
                    head = self.session.head(url, timeout=30)

                    # Analyze the status code sent by the server.
                    if head.status_code in redirect_codes:
                        # The url results in a redirection.
                        logger.log('Found a redirection url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        self.set_fault(url, str(head.status_code))
                        try:
                            # Attempt to add the redirected url to the backend.
                            location = head.headers['location']
                            logger.log('Found redirection url: {}'.format(location),
                                'debug')
                            # Combine the provided url with the url we scanned
                            # in order to fill in any blanks in the redirect.
                            new_url = merge_urls(location, url)
                            # Add the new url to the database.
                            self.add_to_queue(new_url, domain)
                            continue
                        except Exception as e:
                            # The server did not provide a redirect url.
                            logger.log("{}: couldn't find redirect. ({})".format(
                                str(head.status_code), url), 'error')
                            continue

                    elif head.status_code in fault_codes:
                        # We received a fault code from the server.
                        logger.log('Found a fault in url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        self.set_fault(url, str(head.status_code))
                        continue

                    elif head.status_code in no_fault_codes:
                        # The url results in a problem, but not a fault.
                        logger.log('Found a problem url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        continue

                    elif head.status_code not in good_codes:
                        # Unknown status. More status codes will be added as
                        # they are discovered in the wild.
                        logger.log('Found a unknown status url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        self.set_fault(url, str(head.status_code))
                        logger.log("Unknown status code {}: {}".format(
                            head.status_code, url), 'error')
                        continue

                    # Update the database to reflect today's scan. Set the last
                    # scan date for the url and onion to today's date and reset
                    # the tries and offline scans.
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

                    # We only want to scan plaintext files, not binary data or
                    # images. Check the content type of the data before making
                    # an attempt to process it.
                    content_type = get_type(head.headers)
                    logger.log("Found content type of url: {} as: {}".format(
                        url, content_type), 'debug')
                    if content_type != 'text' and content_type is not None:
                        # This content is not text-based, so don't scan it.
                        self.set_fault(url, 'type: {0}'.format(content_type))
                        continue

                    request = self.session.get(url, timeout=30)
                    if content_type is None:
                        # If we were unable to get the content type from the
                        # headers, try to get the content type from the full
                        # request.
                        content_type = get_type(request.headers)
                        logger.log("Found content type of url: {} as: {}".format(
                            url, content_type), 'debug')
                        if content_type != 'text' and content_type is not None:
                            # We got a non-text content type, such as a binary
                            # or an image file.
                            self.set_fault(url, 'type: {}'.format(
                                content_type))
                            continue

                    # We've got the site's data. This page is live, so let's
                    # process the url's data.
                    self.process_url(url, domain)

                    # Let's see if the page has changed...
                    try:
                        # Get the page's sha1 hash.
                        page_hash = get_hash(request.content)
                        logger.log('Page hash of url: {} is: {}'.format(
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
                        logger.log('Last page hash of url: {} is: {}'.format(
                            url, last_hash), 'debug')
                        # If the hash hasn't changed, don't process the page.
                        if last_hash == page_hash:
                            logger.log('The hashes matched, nothing has changed.',
                                'debug')
                            continue

                        # Update the page's hash in the database.
                        data = {
                            "hash": page_hash
                        }
                        logger.log('Update hash for url: {} to: {}'.format(
                            url, page_hash), 'debug')
                        self.__update_urls(url, data)

                    except Exception as e:
                        # We were unable to retrieve the previous hash from the
                        # backend. Something went wrong.
                        logger.log("Couldn't retrieve previous hash: {0}".format(url),
                            'error')
                        continue

                    # The page's HTML changed since our last scan; let's
                    # process it.
                    page_text = request.text

                    # Get the title of the page.
                    try:
                        page_title = get_title(page_text)
                    except Exception as e:
                        page_title = 'Unknown'
                    logger.log('Page title for url: {} is: {}'.format(
                        url, page_title), 'debug')
                    # Set the title of the url.
                    # TODO: Only update the url's title if it has changed.
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
                        curr_title = 'Unknown'
                    logger.log('Previous page title for url: {} was: {}'.format(
                        url, curr_title), 'debug')
                    # Now, if the title is 'none' then just save
                    # page_title. But if it's something else, we'll need to
                    # make a hybrid title based on the current title and
                    # the title of the newly-scraped page.
                    if curr_title != 'Unknown' and curr_title:
                        page_title = merge_titles(curr_title, page_title)
                    page_title = ' '.join(page_title.split())
                    # If the title is now empty, just set it to Unknown.
                    page_title = 'Unknown' if page_title == '' else page_title
                    # Now, save the new title to the database, but only if
                    # the title has changed.
                    if page_title != curr_title:
                        logger.log('Page title has changed to: {}'.format(
                            page_title), 'debug')
                        data = {
                            "title": page_title
                        }
                        self.__update_pages(url, data)

                    # Get the page's links.
                    page_links = get_links(page_text, url)

                    # Add the links to the database.
                    for link_url in page_links:
                        # Get the link domain.
                        self.add_to_queue(link_url, domain)

                    # Parse any forms on the page.
                    logger.log('Parsing forms on url: {}'.format(url), 'debug')
                    page_forms = get_forms(page_text)

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
                        action_url = merge_urls(
                            form_dict['action'], url)
                        if '.onion' not in action_url \
                                or '.onion.' in action_url:
                            # Ignore any non-onion domain.
                            continue
                        self.add_to_queue(action_url, domain)

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
                            # TODO: Check that the form field isn't already
                            # present before adding it to the database.
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
                            examples_have_changed = False
                            if not result_examples:
                                # We have no current values.
                                examples = value
                            else:
                                # Merge with the returned examples.
                                example_list = result_examples.split(',')
                                old_list = list(example_list)
                                example_list.append(value)
                                example_list = unique(example_list)
                                example_list.sort()
                                if(old_list != example_list):
                                    examples_have_changed = True
                                examples = ','.join(example_list)

                            # Update the examples in the database, but only if
                            # the values have changed.
                            if(examples_have_changed):
                                data = {
                                    "examples": examples
                                }
                                self.__update_forms(action_url, key, data)

                # Parsing is complete for this page!
                except requests.exceptions.InvalidURL:
                    # The url provided was invalid.
                    logger.log("Invalid url: {}".format(url), 'error')
                    self.set_fault(url, 'invalid url')

                except requests.exceptions.InvalidSchema:
                    # We got an invalid schema. Add the url with both http and
                    # https schemas to the database to see if those work.
                    (s, n, p, q, f) = urlsplit(url)
                    for scheme in ['http', 'https']:
                        s = scheme
                        new_url = urlunsplit((s, n, p, q, f))
                        self.add_to_queue(new_url, domain)
                    self.set_fault(url, 'invalid schema')

                except requests.exceptions.SSLError as e:
                    # There was a problem with the site's SSL certificate.
                    logger.log("SSL Error at {}: {}".format(url, e), 'error')
                    self.set_fault(url, 'Bad SSL')

                except requests.exceptions.ConnectionError:
                    # We had trouble connecting to the url.
                    # First let's make sure we're still online.
                    logger.log("Connection error to url: {}".format(url), 'debug')
                    try:
                        tor_ip = get_my_ip(self.session)
                        if tor_ip:
                            # If we've reached this point, Tor is working.
                            tries += 1
                            if tries == 3:
                                # We've failed three times. Time to quit.
                                logger.log('Url is offline: {}'.format(url), 'debug')
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
                        logger.log('We seem to not be connected to Tor', 'debug')
                        time.sleep(5)
                        continue

                except requests.exceptions.Timeout:
                    # It took too long to load this page.
                    logger.log('Request timed out: {}'.format(url), 'debug')
                    tries += 1
                    if tries == 3:
                        # We've failed three times. Time to quit.
                        logger.log('Url is offline: {}'.format(url), 'debug')
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
                    logger.log('Ran out of memory: {}'.format(url), 'error')
                    self.set_fault(url, 'memory error')

                except NotImplementedError as e:
                    logger.log("I don't know what this means: {} - {}".format(e, url),
                        'error')

                except Exception as e:
                    logger.log('Unknown exception: {}'.format(e), 'error')
                    raise

                if url_offline:
                    # Set the domain to offline.
                    logger.log('Setting url as offline: {}'.format(url), 'debug')
                    data = {
                        "online": False,
                        "tries": 0
                    }
                    self.__update_onions(domain, data)
                    # In order to reduce the frequency of scans for offline
                    # pages, set the scan date ahead by the number of times the
                    # page has been scanned offline. To do this, first retrieve
                    # the number of times the page has been scanned offline.
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
                    # Save the new values to the database.
                    data = {
                        "offline_scans": offline_scans,
                        "scan_date": new_date
                    }
                    self.__update_onions(domain, data)

        # If we reach this point, the main loop is finished and the spiders are
        # going to sleep.
        logger.log("Going to sleep!", 'info')

    def process_url(self, link_url, link_domain):
        # When a URL shows up valid, add its information to the database.
        # TODO: Update this function to reduce redundant data submission.
        logger.log('Processing url: {}'.format(link_url), 'debug')
        link_url = fix_url(link_url)
        logger.log('Fixed link url: {}'.format(link_url), 'debug')
        link_query = get_query(link_url)
        logger.log('Link query: {}'.format(link_query), 'debug')
        try:
            # Insert the url into its various tables.
            logger.log('Add url: {} domain: {} into page table.'.format(
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
            # There was an error processing the url.
            logger.log("Couldn't process url: {0}".format(e), 'error')
            raise

    def set_fault(self, url, fault):
        logger.log('Setting fault status for url: {} fault: {}'.format(url, fault),
            'debug')
        # Update the url and page faults.
        data = {
            "fault": fault
        }
        self.__update_urls(url, data)
        self.__update_pages(url, data)


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
            'API_URL': 'https://api.torspider.pro/api/',
            'API_KEY': 'Configure_api_key',
            'API_NODE': 'Configure_api_node',
            'VERIFY_SSL': True
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
        node_name = os.environ.get('API_NODE', None)
        if not node_name:
            node_name = config['API'].get('API_NODE')
        api_url = os.environ.get('API_URL', None)
        if not api_url:
            api_url = config['API'].get('API_URL')
        api_key = os.environ.get('API_KEY', None)
        if not api_key:
            api_key = config['API'].get('API_KEY')
        api_node = os.environ.get('API_NODE', None)
        if not api_node:
            api_node = config['API'].get('API_NODE')
        if api_key == 'Configure_api_key' or api_node == 'Configure_api_node':
            print('You have not configured your API Key and Node.  Please update your spider.cfg file.')
            sys.exit(0)
        ssl_verify = os.environ.get('VERIFY_SSL', None)
        if not ssl_verify:
            ssl_verify = config['API'].getboolean('VERIFY_SSL')
        if not ssl_verify:
            # if we disable ssl verification, we'll also disable warning messages.
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    except Exception as e:
        print('Could not parse spider.cfg. Please verify its syntax.')
        sys.exit(0)
    logger.log('-' * 40, 'info')
    logger.log('TorSpider v{} Initializing...'.format(version), 'info')

    # Create a Tor session and check if it's working.
    logger.log("Establishing Tor connection...", 'info')
    session = get_tor_session()
    while True:
        try:
            logger.log("Verifying Tor connection...", 'info')
            local_ip = get_my_ip(None)
            if not local_ip:
                logger.log("Cannot determine local IP address.", 'error')
            tor_ip = get_my_ip(session)
            if not tor_ip:
                logger.log("Cannot determine tor IP address.", 'error')
            if local_ip == tor_ip:
                logger.log("Tor connection failed: IPs match.", 'error')
            else:
                logger.log("Tor connection established.", 'info')
                break
        except Exception as e:
            logger.log("Tor connection failed: {}".format(e), 'error')
            time.sleep(5)

    # Awaken the spiders!
    Spiders = []
    Spider_Procs = []

    logger.log('Waking the Spiders...', 'info')
    # There are enough names here for a 32-core processor.
    my_names = []

    # We'll start two processes for every processor.
    count = (cpu_count() * 2)
    for x in range(count):
        spider = Spider()
        spider_proc = Process(target=spider.crawl)
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
    logger.log('The Spiders have gone to sleep. ZzZzz...', 'info')
    logger.log('-' * 40, 'info')
