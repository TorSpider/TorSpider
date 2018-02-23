# TorSpider

## A Darknet Spider and Database.

### Purpose:

To create a Tor spider and link database, providing basic information about hidden sites, including URLs, titles, site structure, links to other sites, etc.

### Implementation:

TorSpider scans Tor hidden services, harvesting important information from each site it finds. It employs multiprocessing for speed, and stores data in an PostgreSQL database.

### Prerequisites:

TorSpider is written in `Python 3`, and requires libraries that are available using the `pip` tool.

TorSpider requires [Tor](https://www.torproject.org/) to be installed and running with the SOCKS proxy port set to 9095.

TorSpider requires the [TorSpider-Backend](https://github.com/TorSpider/TorSpider-Backend) to be running.

In order to view and interact with the data from TorSpider, you'll need the [TorSpider-Frontend](https://github.com/TorSpider/TorSpider-Frontend) to be installed and functional.

### Installation:

1. Clone the TorSpider repository.
2. Enter the TorSpider directory.
3. Create a virtual environment, if you wish. (This is advised.)
4. Execute the command `pip3 install -r requirements.txt` to install the required libraries.
5. Run the `TorSpider.py` script. The first time this is run, it will generate a configuration file called `spider.cfg`.
6. Edit the `spider.cfg`, giving the node a name and directing it at the correct URL for the TorSpider-Backend API.

Enable TorSpider as a service:
Please note, we assume torspider is installed as the torpsider user in /home/torspider.
1. Run `sudo cp init/torspider-spider.service /etc/systemd/system/` 
2. Run `sudo systemctl daemon-reload`
3. Run `sudo systemctl enable torspider-spider`

### Running TorSpider:

*It is adviseable to run TorSpider within a virtual environment, and to run it using the `screen` command, so that you can exit the terminal without stopping the script.*

Once you've properly set up the `spider.cfg` file, you can run TorSpider and it will begin the spidering process. To cleanly stop the TorSpider script, simply create a file called 'sleep' in the TorSpider directory. In the *nix command-line, this can be achieved by using the `touch sleep` command within the directory where the `TorSpider.py` script is stored. After creating this file, each spider will finish its current tasks then deactivate. Once the sleep file has been deleted by the TorSpider script, the process has ended and the script has stopped. (Stopping the script might take some time, as the spiders might still be adding information to the database.)

You can also run TorSpider as a service by running systemctl start torspider-spider