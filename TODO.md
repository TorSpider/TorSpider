# To Do

## High Priority
* Convert pages table to urls table.
* Create new pages table: (id, url, title, info, form_fields)
* Create new queries table: (page_id, query)
* When encountering a url with a query, add the url sans query to the urls and to the pages table, add the query to the queries table, and add the query fields to the form_fields part of the pages table as CSV.

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
