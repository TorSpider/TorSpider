#!/usr/bin/env python3

''' VisibleWeb.py
    Using VivaGraphJS (https://github.com/anvaka/VivaGraphJS), this script
    crafts a visible render of the Invisible Web as we presently know it.
'''

import sys, os
import configparser
import cherrypy as web
import psycopg2 as sql

class VisibleWeb:
    def __init__(self):
        # Get current configuration.
        config = configparser.ConfigParser()
        config.read('spider.cfg')
        self.username = config['PostgreSQL'].get('Username')
        self.password = config['PostgreSQL'].get('Password')
        self.hostname = config['PostgreSQL'].get('Hostname')
        self.database = config['PostgreSQL'].get('Database')

    def db_get(self, query):
        # Connect to the database.
        try:
            connection = sql.connect(
                    "dbname='{}' user='{}' host='{}' \
                    password='{}'".format(
                            self.database,
                            self.username,
                            self.hostname,
                            self.password))
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connection.close()
            return result
        except Exception as e:
            print('Error: {}'.format(e))
            return None

    def index(self):
        # Retrieve link information, then build visual representation.
        result = self.db_get("SELECT EXISTS (SELECT 1 FROM pg_tables \
                       WHERE tablename = 'links');")
        if(result[0][0] != False):
            # Get the list of domains.
            domain_list = self.db_get("SELECT id, domain FROM onions \
                                      WHERE online = 1 AND \
                                      date != '1900-01-01';")
            # Get the list of links.
            link_list = self.db_get("SELECT domain, link FROM links \
                                    WHERE domain IN ( \
                                        SELECT id FROM onions WHERE \
                                        online = 1 AND date != '1900-01-01' \
                                    ) AND link IN ( \
                                        SELECT id FROM onions WHERE \
                                        online = 1 AND date != '1900-01-01' \
                                    );")
            if(domain_list is None or link_list is None):
                return ''
            # Compile the domain dictionary.
            domains = {}
            for result in domain_list:
                (domain_id, domain_name) = result
                domains[domain_id] = domain_name
            # Compile the link list.
            links = []
            linked_domains = []
            for link in link_list:
                (link_from, link_to) = link
                if(link_from != link_to):
                    # We only want links that don't refer to themselves.
                    linked_domains.append(link_from)
                    linked_domains.append(link_to)
                    links.append([link_from, link_to])
            linked_domains = list(set(linked_domains))
            # Design output.
            output_list = []
            for domain in domains.keys():
                if(domain in linked_domains):
                    output_list.append("graph.addNode({}, '{}');".format(
                            domain, domains[domain]))
            for link in links:
                [link_from, link_to] = link
                output_list.append("graph.addLink({}, {});".format(
                        link_from, link_to))
            output_list.append('var renderer = \
                               Viva.Graph.View.renderer(graph);')
            # Create HTML.
            output = open('web/head.html','r').read()
            for item in output_list:
                stripped = ' '.join(item.split())
                output += '            {}\n'.format(stripped)
            output += open('web/foot.html','r').read()
            return output
    index.exposed = True

if __name__ == '__main__':
    conf = { # server configuration
        '/':{'tools.staticdir.root': os.getcwd()},
        '/web':{
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './web'
        },
        'global':{
            'server.environment':'production',
            'server.socket_host':'0.0.0.0',
            'server.socket_port':8080
        }
    }
    web.quickstart(VisibleWeb(), config=conf)
