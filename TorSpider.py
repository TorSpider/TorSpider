#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' ______________________________________________________________________
   |                         |                  |                         |
   |                   +-----^---TorSpider-v2---^-----+                   |
   |                   |  Crawling the Invisible Web  |                   |
   |                   +----------------by CMSteffen--+                   |
   |                                                                      |
   | TorSpider employs an army of spiders to explore Tor hidden services, |
   | seeking to uncover and catalogue the deepest reaches of the darknet. |
   | They are accompanied by Voltaire, their trusty historian and scribe, |
   | who chronicles their adventure with his sharp quill and sharper wit. |
    ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
'''

import os                    # +----------------------------------------+ #
import sys                   # |       Beware, ye who enter here:       | #
import time                  # |     The Invisible Web is rife with     | #
import random                # | wondrous and terrible things. It is no | #
import requests              # |  place for the squeamish or the faint  | #
import sqlite3 as sql        # |    of heart. Here there be dragons!    | #
from hashlib import sha1     # +----------------------------------------+ #
import multiprocessing as mp
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit


'''---[ CAST OF CHARACTERS ]---'''


class Spider():
    def __init__(self, queue):
        self.queue = queue

    def crawl(self):
        print('{} awake!'.format(mp.current_process().name))
        time_to_sleep = False
        while(not time_to_sleep):
            message = str('{} is thinking of number {}'.format(
                    mp.current_process().name,
                    random.randint(1, 1000)))
            self.queue.put(message)
            if(os.path.exists('sleep')):
                time_to_sleep = True
            time.sleep(0.1)
        print('{} sleeping...'.format(mp.current_process().name))


class Scribe():
    def __init__(self, queue):
        self.queue = queue

    def begin(self):
        print('{} awake!'.format(mp.current_process().name))
        time_to_sleep = False
        while(not time_to_sleep or not self.queue.empty()):
            message = self.queue.get()
            print('{}: {}'.format(mp.current_process().name, message))
            if(os.path.exists('sleep')):
                time_to_sleep = True
        print('{} sleeping...'.format(mp.current_process().name))


'''---[ SCRIPT ]---'''

if __name__ == '__main__':
    queue = mp.Queue()
    Voltaire = Scribe(queue)
    Voltaire_Process = mp.Process(target=Voltaire.begin)
    Voltaire_Process.name = 'Voltaire'
    Voltaire_Process.start()
    Spiders = []
    Spider_Procs = []

    count = mp.cpu_count() - 1
    count = count if count > 0 else 1
    print(count)
    for x in range(count):
        spider = Spider(queue)
        spider_proc = mp.Process(target=spider.crawl)
        spider_proc.name = 'Spider{}'.format(x + 1)
        Spider_Procs.append(spider_proc)
        Spiders.append(spider)
        spider_proc.start()
        time.sleep(1)

    for spider_proc in Spider_Procs:
        spider_proc.join()

    Voltaire_Process.join()
    print('Terminated')
    os.unlink('sleep')
