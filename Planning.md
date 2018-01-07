# TorSpider Planning

### Multithreading or Multiprocessing?

This is the big question to start with, as it will define the structure of the rest of the code. Threading might be simpler to implement, but multiprocessing would utilize the full capabilities of the system's processor. I'm leaning towards multiprocessing and using queues to organize the scan effort, but I'm going to have to do some research in order to determine the optimal way of executing this plan.

### Recursion Levels

Should TorSpider crawl the entire available website, or should it be limited to a certain depth? For most static sites, crawling the entire page should be fairly easy, but for dynamic and complex sites like forums or wikis, crawling could become a challenge.  The sheer volume of pages could provide a bounty of links, but would take up an egregious amount of space in the database and take a very long time to scan. The first problem could be mitigated by deleting any links that 404, while the second problem could be mitigated by limiting scans to a certain time period, like once a week. However, even with these limitations, such complex pages would severely hinder the spidering process.

I'd like to scan infinitely, as this is the simplest way to go about it, and while it might take more time to process a site, it will enable the spider to index the entire site rather than just a fraction. In order to prevent the spider from getting tied up in a single domain and ignoring the rest of the web, found links can be shuffled when added to the scan queue, so that it won't always be scanning the same page.

### Scan Dates

When a link is scanned, update that link's scan date as well as the scan date of its parent domain. When searching for links to re-scan, limit the search to dates older than one week from the present moment. This should prevent over-scanning various domains and eating up too much bandwidth.

### Re-Processing Links

Only re-process a link's information if the page's hash has changed, in order to save ourselves some processing power. Regardless of the hash, update the last-scanned date for the page and its parent domain.

### Attempt connection before scan?

It might be helpful, in order to save time, to attempt a preliminary connection the host before crawling the site. That way we're not wasting valuable time trying to connect to a site that's down. Obviously any attempt to scan a page that's down will automatically generate an error, but it might be faster to simply attempt a connection to their server's port instead of starting by loading the page. This would be as simple as a one-port port scan.

### Offline Domains

When scanning a page, if that page is offline, we can save time by not scanning any further pages in that domain during that day. To do this, when we scan a page in that domain, check to see if it's listed as offline in the database. If so, see if the last scan was within 24hr. If not, go ahead and scan the URL and see if it's offline. If you scan a page and it's offline, update the last-scanned date on the page and the domain for the time of the scan and set 'online' to false.