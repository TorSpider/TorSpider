# Offload To Backend

This will be a fairly large conversion, moving much of the processing overhead from the spider to the backend, which could possibly increase the load on the backend, but should simultaneously increase the speed and ease with which the backend handles the data coming from the spider. Rather than processing tens to hundreds of queries over the wire, the backend need only receive one query from the spider for every url the spider scans.

## Spider-Side

Rather than sending queries to the backend, the spider should instead compile all data into a JSON object, which will then be sent to the backend.

The data is as follows:
{
  'url': the url being scanned,
  'scan_date': the date of the scan,
  'last_node': the name of the node that scanned the url,
  'new_urls': a [list] of urls discovered on the page,
  'fault': an indicator of what kind of problems were encountered with the url,
  'online': whether the url was online (if True, tries = 0;
      if False, tries += 1. Let the backend determine offline_scans.),
  'title': the title of the url,
  'form_dicts': a [list] of dictionaries representing the forms on the page,
  'hash': the updated page hash for the url.
}

Set_Fault will need to be updated to add the fault to the scan_result and send off the query.

## Backend-Side

The backend will unpack the JSON data it receives, parsing the data and adding it to the database as necessary.

For "on conflict do nothing," see: http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html
