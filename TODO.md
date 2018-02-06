# To Do

## High Priority

## Medium Priority
* Detect forms in the HTML, save the action= and the input fields to the pages table.
* Include [sshtunnel](https://github.com/pahaz/sshtunnel) to enable access to remote servers. You can set up the server like [so](https://unix.stackexchange.com/questions/235040/how-do-i-create-a-ssh-user-that-can-only-access-mysql) to prevent the public account from having any additional rights in the system.
* Improve the VisualWeb.py map by adjusting colors and line lengths, and by including the name of the site above its dot.

## Low Priority
* Enable the script to become daemonized.
* Try to determine the title of the domain based on the titles of its pages.
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Enable notes to be stored regarding interesting information for pages and onions.
* Take note of important header information, such as server type.

## In Process

## Complete
* Have spiders retry connections if they seem to be offline.
* Export parser class definitions to a separate library.
* Rather than having the same spider retry connections, allow other spiders to retry the connection. Three failed attempts means the site is marked offline. Spread it among the spiders though, so that it's not always the same node that's making the attempt. Perhaps include the name of the last node that made the attempt, so that it is forced to try different nodes, rather than being able to try again with the same node. This would require storing the node name in the database and in the configuration file.
* Consolidate concurrent database queries into single queries rather than making multiple calls.
