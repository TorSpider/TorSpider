# TorSpider Planning

### "Database is locked" problem. [CRITICAL]

At the moment, multiple processes are accessing the database simultaneously, each competing with the others over the ever-growing database. This is causing a regular "database is locked" issue. Currently, the solution is just to keep trying over and over until it works, but this is inefficient. A better way to solve this problem would be to have only one process acting on the database at any time. In order to do this, I need inter-process communication, allowing all the little spiders access to a queue where they can add their queries and get back responses. Another possible alternative is to use a database that can handle multiple concurrent connections and queries. (This is an important step in the direction of the cluster computing goal seen below.)

### Cluster Computing

I wish to convert this script so that it can be run on multiple machines in parallel, to share the load of scanning. This will require moving the database to an external server which all nodes can reach.

### Form Data as Separate Table?

Right now every unique form submission results in a different page in the pages table. However, this seems disingenuous, considering that pages with search queries could theoretically generate infinite pages. So, rather than list every single possible form submission in the pages table, it would be better to have unique pages in the pages table and offload the possible form submissions to a separate table.

### Re-Processing Links

Only re-process a link's information if the page's hash has changed, in order to save ourselves some processing power. Regardless of the hash, update the last-scanned date for the page and its parent domain.

### Daemonization

Allow the script to run as a silent daemon, so that it can be started without monopolizing a console window. You could also set it up to load on startup when the computer is started/rebooted.
