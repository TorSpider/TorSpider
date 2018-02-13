# Process of installation from fresh raspbian-lite installation.

## Initial setup of Raspberry Pi

1. Install raspbian.
2. Change keyboard layout using `sudo raspi-config`.
3. Set up a new password.
4. Set up static IP by modifying /etc/network/interfaces. (See: Google)
5. Update and upgrade everything.
6. Make sure you've got SSH enabled.
7. Make sure git is installed with `sudo apt install git`
8. Also install Tor. `sudo apt install tor`
9. Screen is a useful tool, too. `sudo apt install screen`
10. Reboot. `sudo shutdown -r now`

## Install pip for Python 3

The latest version of raspbian comes with Python 3.5 already installed. What we need, however, is pip3 and libpq-dev, so we can install our dependencies.

```
sudo apt install python3-pip libpq-dev
```

Once pip3 has installed, you can install the other remaining requirements for TorSpider with the following commands:

```
sudo pip3 install pysocks requests cherrypy psycopg2-binary networkx
```

## Install and configure PostgreSQL.

You'll need an installation of PostgreSQL. Check out the `PGSQL_Install.md` file to see how this is done.

## Clone TorSpider

To download the latest stable release of TorSpider, you'll want to clone it. First, change directories to wherever you want to keep TorSpider. Then:

```
git clone https://github.com/eloquentmess/TorSpider.git
```

The system will download TorSpider into ./TorSpider.

## Start TorSpider!

At this point, everything should be ready to go. Start up a new screen instance by using `screen -R TorSpider`, then `cd` to the TorSpider directory and run ./TorSpider.py. The first time you run the script, it'll create a configuration file called `spider.cfg`. Edit this file to include the login credentials and name of the PostgreSQL database, then save the file and run TorSpider again, like so:



```
bash $ ./TorSpider.py
2018-01-24 19:13:44| MainProcess: ----------------------------------------
2018-01-24 19:13:44| MainProcess: TorSpider v2 Initializing...
2018-01-24 19:13:44| MainProcess: Establishing Tor connection...
2018-01-24 19:13:46| MainProcess: Tor connection established.
2018-01-24 19:13:46| MainProcess: Waking the Scribe...
2018-01-24 19:13:46| Voltaire: I'm awake! Checking my database.
2018-01-24 19:13:46| Voltaire: Initializing new database...
2018-01-24 19:13:46| Voltaire: Database initialized.
2018-01-24 19:13:46| Voltaire: Okay, I'm ready.
2018-01-24 19:13:47| MainProcess: Waking the Spiders...
2018-01-24 19:13:47| Chester: Ready to explore!
```

Once the script is running, you can ctrl-a, ctrl-d to leave the screen running in the background. If you want to stop TorSpider, just `cd` to the TorSpider directory and `touch sleep`. Then you can `screen -R TorSpider` again to watch as the program goes to sleep. (This can take some time, so be patient.)
