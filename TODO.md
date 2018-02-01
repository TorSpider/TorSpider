# To Do

## High Priority
* Streamline scans to reduce network and processor load on the database.

## Medium Priority
* Include [sshtunnel](https://github.com/pahaz/sshtunnel) to enable access to remote servers. You can set up the server like [so](https://unix.stackexchange.com/questions/235040/how-do-i-create-a-ssh-user-that-can-only-access-mysql) to prevent the public account from having any additional rights in the system.
* Learn to use [VivaGraph.js](https://github.com/anvaka/VivaGraphJS) to create a map of the darknet.
* Improve the VivaGraph.js map by adjusting colors, line lengths, etc.

## Low Priority
* Enable the script to become daemonized.
* Try to determine the title of the domain based on the titles of its pages.
* Detect forms in the HTML, save the action= and the input fields to the pages table.
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Enable notes to be stored regarding interesting information for pages and onions.
* Take note of important header information, such as server type.

## In Process
* Test new changes.
* Catch and fix exception psycopg2.OperationalError (server closed the connection unexpectedly) -- retry query if possible.
* Streamline scans to reduce network and processor load on the database.

## Complete
* Stop marking urls offline. Just mark sites offline.
* Add column offline_scans to onions. When it scans offline, set the scan date to the current date plus offline_scans days. That way, the longer the site is offline, the less frequently we scan it.
* If it comes online, set offline_scans to zero.
* Create script to update database with new fields and defaults.
* Update urls and pages set fault = none where fault = offline.
