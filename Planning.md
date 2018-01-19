# TorSpider Planning

### Form Data as Separate Table?

Right now every unique form submission results in a different page in the pages table. However, this seems disingenuous, considering that pages with search queries could theoretically generate infinite pages. So, rather than list every single possible form submission in the pages table, it would be better to have unique pages in the pages table and offload the possible form submissions to a separate table.

### Multithreading or Multiprocessing?

I've settled on multiprocessing. Even more, I plan to eventually craft this script so that it can be run on multiple machines in parallel, to share the load of scanning. This will require moving the database to an external server which all nodes can reach.

### Re-Processing Links

Only re-process a link's information if the page's hash has changed, in order to save ourselves some processing power. Regardless of the hash, update the last-scanned date for the page and its parent domain.

### Daemonization

Allow the script to run as a silent daemon, so that it can be started without monopolizing a console window. You could also set it up to load on startup when the computer is started/rebooted.
