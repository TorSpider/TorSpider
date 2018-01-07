# TorSpider

## A Darknet Spider and Database.

### Purpose:

To create a darknet spider and link database, storing basic information about onion sites, including URLs, titles, site structure, links to other sites, etc.

### Method:

This system will involve two applications: TorSpider and TorWeb.

TorSpider will scan the darknet, crawling through every site it finds, harvesting important information from each site. All of this information will be stored in a database. TorWeb will access this database, making it available through a simple web interface which will allow users to explore and expand the information discovered via TorSpider.

### Implementation:

TorSpider and TorWeb will be two separate Python 3 scripts, each running concurrently. TorSpider will employ multithreading or multiprocessing for speed. Both scripts will use SQLite3 for storing and retrieving information.

### Requirements:

TorSpider will use the **requests** library for its scanning process, and will require **pysocks** to be installed in order to connect to Tor.

TorWeb will use the **CherryPy** library for hosting its web content.