# To Do

## Bugs
* SpiderStats reveals that there are more online sites than we've even scanned so far: `So far, TorSpider has scanned 43 (1.27%) of the 3,394 urls it has discovered. Of the scanned sites, 53 are known to be active. TorSpider has found 25 direct links between these sites.` Why is this happening?

```
Traceback (most recent call last):
  [...]
  File "./TorSpider.py", line 530, in crawl
    (interval, domain_id, interval, domain_id))
  File "./TorSpider.py", line 545, in db
    cursor.execute(query, args)
psycopg2.InternalError: current transaction is aborted, commands ignored until end of transaction block

Traceback (most recent call last):
  [...]
  File "./TorSpider.py", line 292, in crawl
    page_forms = self.get_forms(page_text)
  File "./TorSpider.py", line 612, in get_forms
    parse.feed(data)
  [...]
  File "/home/pi/TorSpider/libs/parsers.py", line 166, in handle_endtag
    self.text_areas[self.text_area_name] = self.text_area_value
AttributeError: 'FormParser' object has no attribute 'text_area_value'

SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('1 day', 163, '1 day', 163)
SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('3 days', 163, '3 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('13 days', 163, '13 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('5 days', 163, '5 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('8 days', 163, '8 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('7 days', 163, '7 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('2 days', 163, '2 days', 163)
UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('10 days', 163, '10 days', 163)
SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL '1 day') WHERE domain = 163; UPDATE onions SET date = (CURRENT_DATE + INTERVAL '1 day') WHERE id = 163; | Args: ('1 day', 163, '1 day', 163)

Infinite pause with UPDATE urls SET date = (CURRENT_DATE + INTERVAL '1 day') WHERE domain = 163;

UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('9 days', 163, '9 days', 163)
SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('14 days', 163, '14 days', 163)
SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('12 days', 163, '12 days', 163)
SQL Error: Message: UPDATE urls SET date = (CURRENT_DATE + INTERVAL %s) WHERE domain = %s; UPDATE onions SET date = (CURRENT_DATE + INTERVAL %s) WHERE id = %s; | Args: ('6 days', 163, '6 days', 163)
```

## High Priority
* Update the script to use ORM and Flask.
* Separate the backend code from the spider code.

## Medium Priority
* Find a secure way to allow access to remote spiders.
* Create a force-directed graph map of the known darknet.

## Low Priority
* Enable the script to become daemonized.
* Try to determine the title of the domain based on the titles of its pages.
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Enable notes to be stored regarding interesting information for pages and onions.

## In Process
* Optimize the process top to bottom.

## Complete
