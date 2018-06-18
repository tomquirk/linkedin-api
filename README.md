# linkedin_api

👨‍💼 Python Wrapper for the Linkedin API

> No "official" access required - just use a valid Linkedin account!

## Overview

This project attempts to provide a simple Python interface for the Linkedin API.

> Do you mean the [legit Linkedin API](https://developer.linkedin.com/)?

NO! To retrieve structured data, the [Linkedin Website](https://linkedin.com) uses a service they call **Voyager**. Voyager endpoints give us access to pretty much everything we could want from Linkedin: profiles, companies, connections, messages, etc.

So specifically, this project aims to provide complete coverage for Voyager.

[How do we do it?](#in-depth-overview)

[How do I find endpoints?](to-find-endpoints)

## Example usage

```python
from linkedin_api import LinkedinAPI

api = LinkedinAPI()

# Authenticate using any Linkedin account credentials
api.authenticate('reedhoffman@linkedin.com', 'iheartmicrosoft')

# GET a profile
profile = api.get_profile('billy-g')

# GET a profiles contact info
contact_info = api.get_profile_contact_info('billy-g')

# GET all connected profiles (1st, 2nd and 3rd degree) of a given profile
connections = api.get_profile_connections('1234asc12304', max_connections=200)
```

## Setup

### Dependencies

* Python 3
* A valid Linkedin user account
* Pipenv (optional)

1. Using pipenv...

```
$ pipenv install
$ pipenv shell
```

## In-depth overview

Voyager endpoints look like this:
```
https://www.linkedin.com/voyager/api/identity/profileView/tom-quirk
```

Or, more clearly
```
 _______________________ _____________ _______________________________
|       base path       | path prefix |            resource           |
https://www.linkedin.com /voyager/api /identity/profileView/tom-quirk
```

They are authenticated with a simple cookie, which we send with every request, along with a bunch of headers.

To get a cookie, we POST a given username and password (of a valid Linkedin user account) to `https://www.linkedin.com/uas/authenticate`.

### To find endpoints...

We're looking at the Linkedin website and we spot some data we want. What now?

The most reliable method to find the relevant endpoint is to: 
1. `view source`
2. `command-f`/search the page for some keyword in the data. This will exist inside of a `<code>` tag.
3. Scroll down to the **next adjacent element** which will be another `<code>` tag, probably with an `id` that looks something like
```html
<code style="display: none" id="datalet-bpr-guid-3900675">
  {"request":"/voyager/api/identity/profiles/tom-quirk/profileView","status":200,"body":"bpr-guid-3900675"}
</code>
```
4. The value of `request` is the url! :woot:

You can also use the `network` tab in you browsers developer tools, but you will encounter mixed results.
