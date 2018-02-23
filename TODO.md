# To Do

## Bugs
* Malformed HTML resulted in the following error:
```
2018-02-23 03:41:10,094 - DEBUG - Michelle: Attempting to add a onion url to the queue: http://wikilink77h7lrbi.onion/</a> â see âPolitical Advocacyâ</li> </ul> <dl> <dd>running on: unknown, ports:: plaintext: 6667 ssl: 9999</dd> </dl> <ul> <li><a href=
2018-02-23 03:41:10,097 - DEBUG - Michelle: Fixed url is: http://wikilink77h7lrbi.onion/</a> â see âPolitical Advocacyâ</li> </ul> <dl> <dd>running on: unknown, ports:: plaintext: 6667 ssl: 9999</dd> </dl> <ul> <li><a href=
```

## High Priority
* Find a secure way to allow access to the remote API.

## Medium Priority
* Replace `merge_urls` with `merge_action`, since it does the same thing but better. Rename `merge_action` to `merge_urls`.
* Create a force-directed graph map of the known darknet.
* Enable the script to become daemonized.

## Low Priority
* Try to determine the title of the domain based on the titles of its pages.
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Enable notes to be stored regarding interesting information for pages and onions.

## In Process

## Complete
* Update the script to use ORM and Flask.
* Separate the backend code from the spider code.
