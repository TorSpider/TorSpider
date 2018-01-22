# TorSpider Planning

### Cluster Computing

I wish to convert this script so that it can be run on multiple machines in parallel, to share the load of scanning. This will require moving the database to an external server which all nodes can reach.

### Daemonization

Allow the script to run as a silent daemon, so that it can be started without monopolizing a console window. You could also set it up to load on startup when the computer is started/rebooted.
