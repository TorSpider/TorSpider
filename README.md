# TorSpider

## A Darknet Spider and Database.

### Purpose:

To create a Tor spider and link database, providing basic information about hidden sites, including URLs, titles, site structure, links to other sites, etc.

### Implementation:

TorSpider scans Tor hidden services, harvesting important information from each site it finds. It employs multiprocessing for speed, and stores data in an PostgreSQL database.

### Prerequisites:

TorSpider is written in `Python 3`.

TorSpider requires the `requests`, `psycopg2` and `pysocks` libraries in order to scrape pages through Tor.

TorSpider requires **Tor** to be installed and running with the SOCKS proxy port set to 9095.

### Installation:

Check out the `Fresh_Install.md` file to see how to set up a new TorSpider node. To create the backend database, read the file `PGSQL_Install.md`.

### Running the Scripts:

The first time you run TorSpider, it will create a configuration file. This file will need to be edited with the appropriate information for connecting to the TorSpider database. Once this is done, you can run TorSpider again and it will populate the database with initial values.

Once the database is initialized, it is safe to stop and start the TorSpider process as necessary. To cleanly stop the TorSpider script, simply create a file called 'sleep' in the TorSpider directory. In the *nix command-line, this can be achieved with the `touch sleep` command. After creating this file, each spider will finish its current task and then deactivate. Once the sleep file has been deleted by the TorSpider script, the process has ended and the script has stopped.
