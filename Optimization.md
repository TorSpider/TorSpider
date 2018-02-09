I want to optimize the whole scanning process in order to reduce the database size, reduce useless data in the database, and increase the scan speed.

### Here is the current scan process (pseudocode):

#### Selecting a URL:
1. Pull a random URL from the database that meets the following criteria:
	* The url has no recorded fault AND:
		* The URL's domain is online and the URL hasn't been scanned in a week
		* OR the URL's domain is listed as online but another node was unable to connect to it
		* OR the URL's domain is listed as offline and its last scan day was 24 hours ago.
2. If the URL was scanned offline by another node, be sure to keep note of how many times it has scanned offline.
	* If it was scanned offline and this node was the last node that scanned it, skip this URL and get another. We don't want the same node to check the online status of this link again, because if this node is having trouble connecting, a site might be falsely marked as offline.
3. If the URL is not an http/https link, set its fault to 'non-http', then go back and find another URL to scan. These URLs might be interesting, but they aren't within the scope of our scan.
4. If the URL passes all the tests so far, go ahead and update the database entry for its onion domain and set its date to today.

#### The Scanning Process:
Once a URL has been selected, we begin the scan process.

1. Request the header data for the given URL. We do this first to save time; retrieving the header is faster than retrieving the whole body of the document, and the header will tell us the document type, allowing us to skip over images and binaries (which we have no interest in scanning anyway). *At some future point, it might be in our interest to store a list of working binary and image links, so that we can do a search like Google's `filetype:pdf`, but for now we're just going to ignore these links.*
2. Check the status code provided in the header.
	* If the status is a redirect, find where it's redirecting us, add that URL to the database to be scanned (via `add_url`), and set the current URL's fault to its status code. Then, go back and find another URL to scan.
	* If the status is a fault code, set the current URL's fault to the status code, then go back and find a new URL to scan.
	* If the status is a non-fault code, this means that there's something wrong, but it's likely temporary. Don't set a fault flag for this URL, but don't process it either. Just go back and try a different URL.
	* If the status is a good code (200, etc.) then go ahead and move on to the next phase to process it.
	* If the status code is unknown, set its fault code to its status code, log it, then go find another URL to scan.
3. Once we've found that this is a working URL, make a note in the database that we scanned it today. Also make a note that the domain is online and set its offline scans and tries to 0.
4. Next, determine if this content is something we wish to scan. If the content type isn't text, set its fault to its content type, then go back and pick a new URL to scan. The only exception is if we receive no content type, in which case we'll move on to the next step, then check its content type again.
5. Go ahead and retrieve the full contents of the file. If we still don't know the content type after doing this, we'll process it anyway, just in case. But typically by this point we know it's a text file. *So far, the only time I've had trouble with text-based data is when I discovered an ePub ebook. The server labeled its content type as text rather than as binary, and the spider went ahead and pulled the entire file, only to run out of memory. It logged the error, set the fault on the URL, then went on its way.*
6. Check to see if the data for this URL has changed. To do this, we'll make a sha1 hash of the page's content and compare it to the hash in the database.
	* If the hashes match, then the site hasn't changed, and we can skip this URL and go get another one to scan. *This helps us save time by preventing redundant scans.*
	* If the hashes don't match, store the new hash and continue the scan.
7. Get the title of the page, if possible.
	* If this isn't possible, the script is set to set a fault for the URL then go back and find a different URL to scan. *This is problematic, though, because we could still find useful information from a page that has failed to add a title. Instead of skipping the page, we should just set its title to 'Unknown'.*
8. Update the URL's title in the `urls` table.
9. Get the old title of the related page from the `pages` table. *We currently create a new variable here called new_title, which is technically not necessary.*
10. If the page's old title is 'none' or 'Unknown', set the page's title to the new title. Otherwise, merge the old title and the new title together, then if that value is different from the old title, store the new title in the `pages` table. *The merging process simply involves finding the words two titles have in common. For example, if Title A is "Have a good day!" and Title B is "Have a merry Christmas!" then the merged title would be "Have a".*
11. Once the page's title has been dealt with, scrape all the URLs we can find on the page, both from <a> tags and <img> tags. *There are other tags we could check, like script src, but right now we're only looking at links and images.*
12. Add every single discovered url (via `add_url`) to the database to be scanned.
13. Next, scan the page to see if there are any forms. If they exist:
	* Get the form's `action` value, turn it into a valid URL, then add it (with `add_url`) to the database for scanning.
	* Next, extract all the form's fields and default data, and add all of that information to the database.
14. Once all of these steps are complete, we're done scanning the page. Go get another URL to scan.

#### Possible Errors:

As we're scanning the page, we might come across some errors. Here's how we handle them:

* **requests.exceptions.InvalidURL** – set the url's fault, then go get a new URL to scan.
* **requests.exceptions.InvalidSchema** – first, see if they perhaps misspelled the scheme and 'http' is in the scheme. If so, add the URL to the database with both http and https schemes. Either way, fault the URL with an invalid schema. *It might be a good idea to simply add the URL with http and https, regardless of the given schema, rather than seeing if 'http' is in the schema.*
* **requests.exceptions.ConnectionError** – This means we weren't able to connect to the URL. If this happens, try to connect to api.ipify.org and get its text. If we can't connect there either, then we know this node is having connection issues, and we'll wait a while before moving on to scan the next URL. If, on the other hand, we CAN connect to ipify, then we know the issue is just with the onion. So we'll increment the number of tries we've made. If this is the third try, then we'll mark the site and all of its pages and urls offline. Either way, we get the next URL and move on. *It might be a good idea to try connecting to a different non-onion url, since ipify isn't always accessible in other countries.*
* **requests.exceptions.Timeout** – Basically the same as with ConnectionError.
* **requests.exceptions.TooManyRedirects** – Set the fault to 'redirect', then go grab the next URL and keep scanning.
* **requests.exceptions.ChunkedCodingError** – In this case, I think it's not a permanent error, so I'll just skip it and move on to the next URL.
* **requests.exceptions.SSLError** – Make a note of the error and the URL, set the fault, then go get the next URL to scan. *Interesting note: I've seen SSL Errors that revealed the public IP of a hidden service because they had certificates for the public IP but not for the hidden service.*
* **MemoryError** – We ran out of memory. Log the fault and move on to the next URL.
* **NotImplementedError** – Not sure what's going on here. Log it, then get the next URL.
* **Exception** – This is the catch-all. Log the exception, then raise the exception so we can see it in the cli, then move on and get the next URL.

#### The `add_url` Function:
This is the function used by default to add all newly-discovered urls to the database. I believe we can optimize the script's efficiency greatly just by modifying how we handle new URLs. (See my notes in the next section.)
1. When provided with a new URL and domain_id, first check to see if the URL links to a .onion domain. If not, don't even bother processing it.
2. Next, insert the URLs domain into the `onions` table, if it's not already there.
3. Next, insert the URL into the `urls` table, the page into the `pages` table, and a link between the given `domain_id` and the linked domain in the `links` table.
4. Process the link for any request data, then add that information to the `forms` table.

#### Possible Improvements:
* To start with, the add_url function automatically adds information to the `pages` and `forms` tables as if the link itself is assumed valid. This data should not be added to the database until the url has been successfully loaded and proves itself to be legitimate. By doing it this way, we can avoid storing lots of useless page and form data in the database for things that are invalid or offline. This would also reduce the number of database queries that must be performed.
* In step 7 of the scanning process, don't skip an entire page just because it has no title.
* In step 9 of the scanning process, rather than creating a new variable, just use page_title.
* In the **InvalidSchema** error, rather than checking the schema, just add two URLs to the urls table with http and https respectively.