from datetime import date
import json


class SpiderURL:
    def __init__(self):
        self.new_urls = []
        self.online = False
        self.url = None
        self.scan_date = date.today().strftime('%Y-%m-%d')
        self.last_node = None
        self.fault = None
        self.title = None
        self.form_dicts = []
        self.hash = None

    def to_json(self):
        return json.dumps(self.__dict__)
