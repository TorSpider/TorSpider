# TorSpider

## A Darknet Spider and Database.

### Purpose:

To create a Tor spider and link database, providing basic information about hidden sites, including URLs, titles, site structure, links to other sites, etc.

### Implementation:

This system comprises two scripts: TorSpider and WebCrawler.

TorSpider scans Tor hidden services, harvesting important information from each site it finds. It employs multiprocessing for speed, and stores data in an SQLite database.

WebCrawler provides an intuitive web-based front-end to this database, allowing users to explore and expand the information provided by TorSpider.

### Prerequisites:

TorSpider and TorWeb are both written in **Python 3**.

TorSpider requires the **requests** and **pysocks** libraries in order to scrape pages through Tor.

WebCrawler requires the **CherryPy** library to run the web server.

TorSpider requires **Tor** to be installed and running with the SOCKS proxy port set to 9095.

VisibleWeb requires **NetworkX** to be installed.

### Installation:

Once you've installed the prerequisites, simply place the TorSpider.py and WebCrawler.py files into the directory of your choosing. No other files are needed.

### Running the Scripts:

TorSpider and WebCrawler will both need to be run in their own separate consoles, as they currently print logs to the console window. For this reason, the **screen** utility comes in handy. Each script can run in its own screen instance without monopolizing a terminal window.

For the first run, it is advised to start the TorSpider script and let it run for a few minutes before starting the WebCrawler script. This allows the database to be built up a little before being accessed.

Once the database file exists, it is safe to stop and start the TorSpider process as necessary. The best way to cleanly stop the TorSpider script is to simply create a file called 'sleep' in the same directory as the TorSpider script. In the *nix command-line, this can be achieved with the **touch sleep** command. After creating this file, each spider will finish its current task and then deactivate. Once the sleep file has been deleted by the TorSpider script, the process has ended and the script has stopped.

WebCrawler doesn't require such a nuanced termination, and can be stopped with ctrl-c.
