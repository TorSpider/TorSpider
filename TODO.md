# To Do

## High Priority
* Try to determine the title of the domain based on the titles of its pages.

## Medium Priority
* Set up remote database access.
* Detect forms in the HTML, save the action= and the input fields to the pages table.

## Low Priority
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Take note of important header information, such as server type.

## In Process

## Complete
* Convert v1 to v2 prior to making changes to database and functionality.
* Drop unnecessary log lines.
* Handle remaining common status code exceptions.
* Convert pages table to urls table.
* Create new pages table: (id, url, title, info)
* Create new forms table to record data about the forms on various pages.
* Set the title of a page based on the request's title and the previous titles.
* Populate the form_fields column in the pages table.
* Write database conversion script to update from last version to new version.
* db-con: Erase faults in urls and pages that need to be re-scanned (like 300-series faults), and set their scan date to 1900-01-01 00:00.
* Streamline existing code in preparation for stable release.
* Fix an index out of range bug.
