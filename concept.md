# TorSpider
## The hidden service indexer.
###### Purpose:
To create a searchable database of the "dark web" which stores basic information about sites: their URLs and their titles and, if available, any metadata they provide.
###### Method:
Create a two-pronged application. One prong will be the spider, which will be fed a small seed database populated with a few unexplored links. From there, the spider will continue to branch out, pulling pages, scraping titles, and adding any newly-discovered domains to its discovery queue. It may even wish to append sub-pages to the queue, so that they can also be scanned for new links. This bot will crawl the web infinitely, pulling in as many links as possible, saving only the information that is useful. (We won't save information on every page, only on every unique domain, and new domains get scan-priority over new pages on previous domains.)
The second prong will be the web server, which will make the database available in a searchable or indexed format. It will list the number of pages indexed as well as provide them in an A-Z format by title or by URL. And, possibly, I'll implement a search function so that users can find exactly what they are seeking.
Eventually, it would be nice to put this index up as its own hidden service. I would not manually add it to its own list, though... I'd put a little easter egg in the code that would go off when the spider found the index, perhaps a little message "the spider found itself today" or something like that.
###### Implementation:
Using a limited thread queue, this kind of application can be hosted on a low-spec machine. I'll use my Raspberry Pi, and I'll set it up to automatically connect to an anonymous VPN just for safety's sake. Then, from the VPN, it'll connect to Tor, hosting the hidden service and scanning for others. The RPi could probably handle a fair number of threads gracefully. As long as there's enough space on the disk (and with 16gb, it'd have to find a LOT of content), there shouldn't be any problem letting the entire thing run from the Pi.


Sqlite3 DB Format:

CREATE TABLE IF NOT EXISTS `onions` (
    `id` INTEGER PRIMARY KEY,           # The domain's ID
    `url` TEXT                          # The domain's URL
);

CREATE TABLE IF NOT EXISTS `state` (
    `last_id` INTEGER                   # The last domain being scanned.
);

### For each onion:

The following tables are created on the fly, with their table names determined by the domain_id of the TLD they reference.

#### This is a table of urls, showing the various pages available within a domain:
CREATE TABLE IF NOT EXISTS `pages_domain_id` (
    `page_id` INTEGER PRIMARY KEY,      # The ID of this particular page within the domain.
    `url` TEXT,                         # The URL for this particular page within the domain.
    `hash` TEXT                         # The sha1 hash of the page, so we can tell if its content has changed.
);

#### This is a table of links, showing connections between domains:

CREATE TABLE IF NOT EXISTS `links_domain_id` (
    `domain_id` INTEGER                      # The domain_id to which the parent domain_id links.
);


## Note: Urls opened must have http: or https: before them.