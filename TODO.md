# To Do

## High Priority

## Medium Priority
* Set up remote database access.
* Detect forms in the HTML, save the action= and the input fields to the pages table.

## Low Priority
* Begin work on WebCrawler site front-end. (Requires database redesign to be complete.)
* Take note of important header information, such as server type.

## In Process
* Populate the form_fields column in the pages table.
* Write database conversion script to update from last version to new version.

## Complete
* Convert v1 to v2 prior to making changes to database and functionality.
* Drop unnecessary log lines.
* Handle remaining common status code exceptions.
* Convert pages table to urls table.
* Create new pages table: (id, url, title, info, form_fields)
* Set the title of a page based on the request's title and the previous titles.
