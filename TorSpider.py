#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    ______________________________________________________________________
   |                         |                  |                         |
   |                   +-----^--TorSpider-v0.8--^-----+                   |
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
from urllib.parse import urlsplit, urlunsplit
from multiprocessing import cpu_count, Process
from libs.parsers import get_forms, get_links, get_title
from libs.classes import SpiderURL

'''---[ GLOBAL VARIABLES ]---'''

# The current release version.
version = '0.8'

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

    def __get_query(self, endpoint, query):
        # Request data from the backend API.
        logger.log("Running GET Query on endpoint: {}".format(endpoint),
                   'debug')
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

    def __post_parse(self, data):
        # Enqueue the data to be parsed on the backend
        logger.log('Pushing to parse queue.', 'debug')
        # Send the data to the backend API.
        r = requests.post(
            self.api_url + 'parse',
            headers=self.headers,
            data=data,
            verify=ssl_verify)
        if r.status_code == 201:
            # If created then it returns the object data.
            logger.log('Added successfully', 'debug')
            return json.loads(r.text)
        elif r.status_code == 401:
            # Unauthorized.
            logger.log('Receive 401 Unauthorized', 'error')
            return {}
        else:
            # Some other failure.
            return {}

    def crawl(self):
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
                # Initialize the scan_result class.
                scan_result = SpiderURL()

                # Ask the API for a url to scan.
                next_url_info = self.__get_query('next', {"node_name": node_name})
                if not next_url_info:
                    # There are currently no urls to scan.
                    logger.log('We found no urls to check, sleeping for 30 seconds.', 'debug')
                    # Wait thirty seconds before trying again.
                    time.sleep(30)
                    continue

                if 'hash' in next_url_info.keys() and 'url' in next_url_info.keys():
                    # We successfully retrieved a url from the API.
                    logger.log('Found next url: {}'.format(next_url_info.get('url')), 'debug')
                    url = next_url_info['url']
                    last_hash = next_url_info['hash']
                    if not last_hash:
                        last_hash = ''
                else:
                    # There are currently no urls to scan.
                    logger.log('We found no urls to check, sleeping for 30 seconds.', 'debug')
                    # Wait thirty seconds before trying again.
                    time.sleep(30)
                    continue

                # Set the url for the scan_result.
                scan_result.url = url

                # Set the last node information in scan_result.
                scan_result.last_node = node_name

                # Store an empty redirect, just in case.
                scan_result.redirect = None

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
                try:
                    # Attempt to retrieve the page's headers.
                    logger.log('Getting head of url: {}'.format(url), 'debug')
                    head = self.session.head(url, timeout=30)

                    # Analyze the status code sent by the server.
                    if head.status_code in redirect_codes:
                        # The url results in a redirection.
                        logger.log('Found a redirection url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        scan_result.fault = str(head.status_code)
                        try:
                            # Attempt to add the redirected url to the backend.
                            location = head.headers['location']
                            logger.log('Found redirection url: {}'.format(location), 'debug')
                            # Combine the provided url with the url we scanned
                            # in order to fill in any blanks in the redirect.
                            new_url = merge_urls(location, url)
                            if '.onion' in new_url and '.onion.' not in new_url:
                                # Ignore any non-onion domain.
                                scan_result.new_urls.append(new_url)
                            # Store information about where this url redirects.
                            scan_result.redirect = new_url
                        except Exception as e:
                            # The server did not provide a redirect url.
                            logger.log("{}: couldn't find redirect. ({})".format(
                                str(head.status_code), url), 'error')
                        # We are done here, Send off the scan_result and go to next url.
                        self.__post_parse(scan_result.to_json())
                        continue

                    elif head.status_code in fault_codes:
                        # We received a fault code from the server.
                        logger.log('Found a fault in url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        scan_result.fault = str(head.status_code)
                        # We are done here, Send off the scan_result and go to next url.
                        self.__post_parse(scan_result.to_json())
                        continue

                    elif head.status_code in no_fault_codes:
                        # The url results in a problem, but not a fault.
                        logger.log('Found a problem url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        # We are done here, Send off the scan_result and go to next url.
                        self.__post_parse(scan_result.to_json())
                        continue

                    elif head.status_code not in good_codes:
                        # Unknown status. More status codes will be added as
                        # they are discovered in the wild.
                        logger.log('Found a unknown status url: {} code: {}'.format(
                            url, head.status_code), 'debug')
                        logger.log("Unknown status code {}: {}".format(
                            head.status_code, url), 'error')
                        scan_result.fault = str(head.status_code)
                        # We are done here, Send off the scan_result and go to next url.
                        self.__post_parse(scan_result.to_json())
                        continue

                    # If we reach this point, we know the domain is online.
                    scan_result.online = True

                    # We only want to scan plaintext files, not binary data or
                    # images. Check the content type of the data before making
                    # an attempt to process it.
                    content_type = get_type(head.headers)
                    logger.log("Found content type of url: {} as: {}".format(
                        url, content_type), 'debug')
                    if content_type != 'text' and content_type is not None:
                        # This content is not text-based, so don't scan it.
                        scan_result.fault = 'type: {0}'.format(content_type)
                        # We are done here, Send off the scan_result and go to next url.
                        self.__post_parse(scan_result.to_json())
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
                            scan_result.fault = 'type: {}'.format(content_type)
                            # We are done here, Send off the scan_result and go to next url.
                            self.__post_parse(scan_result.to_json())
                            continue

                    # Let's see if the page has changed...
                    # Get the page's sha1 hash.
                    page_hash = get_hash(request.content)

                    logger.log('Page hash of url: {} is: {}'.format(url, page_hash), 'debug')
                    logger.log('Last page hash of url: {} is: {}'.format(url, last_hash), 'debug')

                    # If the hash hasn't changed, don't process the page.
                    if last_hash == page_hash:
                        logger.log('The hashes matched, nothing has changed.',
                                'debug')
                        # We are done here, Send off the scan_result and go to
                        # next url.
                        self.__post_parse(scan_result.to_json())
                        continue

                    scan_result.hash = page_hash

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
                    scan_result.title = page_title

                    # Get the page's links.
                    page_links = get_links(page_text, url)

                    # Add the links to the database.
                    for link_url in page_links:
                        if '.onion' in link_url and '.onion.' not in link_url:
                            # Ignore any non-onion domain.
                            scan_result.new_urls.append(link_url)

                    # Parse any forms on the page.
                    logger.log('Parsing forms on url: {}'.format(url), 'debug')
                    page_forms = get_forms(page_text)

                    # Add the forms to the database.
                    for form in page_forms:
                        # Process the form's information.
                        form_dict = dict(form)
                        # TODO: Let the backend parse the form dict.
                        scan_result.form_dicts.append(form_dict)

                        # TODO: Remove this section and let the backend handle
                        # all this processing.

                    # Parsing is complete for this page!
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.InvalidURL:
                    # The url provided was invalid.
                    logger.log("Invalid url: {}".format(url), 'error')
                    scan_result.fault = 'invalid url'
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.InvalidSchema:
                    # We got an invalid schema. Add the url with both http and
                    # https schemas to the database to see if those work.
                    (s, n, p, q, f) = urlsplit(url)
                    for scheme in ['http', 'https']:
                        s = scheme
                        new_url = urlunsplit((s, n, p, q, f))
                        if '.onion' in new_url and '.onion.' not in new_url:
                            # Ignore any non-onion domain.
                            scan_result.new_urls.append(new_url)
                    scan_result.fault = 'invalid schema'
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.SSLError as e:
                    # There was a problem with the site's SSL certificate.
                    logger.log("SSL Error at {}: {}".format(url, e), 'error')
                    scan_result.fault = 'Bad SSL'
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.ConnectionError:
                    # We had trouble connecting to the url.
                    # First let's make sure we're still online.
                    logger.log("Connection error to url: {}".format(url), 'debug')
                    try:
                        tor_ip = get_my_ip(self.session)
                        if tor_ip:
                            # If we've reached this point, Tor is working.
                            # Return the scan_result, which will show that
                            # the url is offline.
                            # Send off the scan_result.
                            self.__post_parse(scan_result.to_json())
                    except Exception as e:
                        # We aren't connected to Tor for some reason.
                        # It might be a temporary outage, so let's wait
                        # for a little while and see if it fixes itself.
                        logger.log('We seem to not be connected to Tor.', 'debug')
                        time.sleep(5)

                except requests.exceptions.Timeout:
                    # It took too long to load this page.
                    logger.log('Request timed out: {}'.format(url), 'debug')
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.TooManyRedirects as e:
                    # Redirected too many times. Let's not keep trying.
                    scan_result.fault = 'redirect'
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except requests.exceptions.ChunkedEncodingError as e:
                    # Server gave bad chunk. This might not be a permanent
                    # problem, so let's just roll with it. Don't report back,
                    # just move on.
                    continue

                except MemoryError as e:
                    # Whatever it is, it's way too big.
                    logger.log('Ran out of memory: {}'.format(url), 'error')
                    scan_result.fault = 'memory error'
                    # Send off the scan_result.
                    self.__post_parse(scan_result.to_json())

                except NotImplementedError as e:
                    logger.log("I don't know what this means: {} - {}".format(e, url), 'error')
                    # Don't report back, just move on.

                except Exception as e:
                    logger.log('Unknown exception: {}'.format(e), 'error')
                    raise
                    # Don't report back, just move on.

        # If we reach this point, the main loop is finished and the spiders are
        # going to sleep.
        logger.log("Going to sleep!", 'info')


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
