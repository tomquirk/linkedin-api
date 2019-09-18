# linkedin_api

👨‍💼 Python Wrapper for the Linkedin API

[![PyPI version](https://badge.fury.io/py/linkedin-api.svg)](https://badge.fury.io/py/linkedin-api)

[![Build](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/tomquirk)


> No "official" API access required - just use a valid Linkedin account!

Programmatically send messages, perform searches, get profile data and more, all with a regular Linkedin user account!

Before using this project, please consult the [Terms and Conditions](#t-c) and [Legal Notice](#legal).



## Overview

This project attempts to provide a simple Python interface for the Linkedin API.

> Do you mean the [legit Linkedin API](https://developer.linkedin.com/)?

NO! To retrieve structured data, the [Linkedin Website](https://linkedin.com) uses a service they call **Voyager**. Voyager endpoints give us access to pretty much everything we could want from Linkedin: profiles, companies, connections, messages, etc. - anything that you can see on linkedin.com, we can get from Voyager.

So specifically, this project aims to provide complete coverage for Voyager.

[How do we do it?](#in-depth-overview)

### Want to contribute?

[Learn how to find endpoints](#to-find-endpoints)

## Installation

Using **Python >= 3.6**:

```
$ pip install linkedin-api
```

### Example usage

```python
from linkedin_api import Linkedin

# Authenticate using any Linkedin account credentials
api = Linkedin('reedhoffman@linkedin.com', 'iheartmicrosoft')

# GET a profile
profile = api.get_profile('billy-g')

# GET a profiles contact info
contact_info = api.get_profile_contact_info('billy-g')

# GET all connected profiles (1st, 2nd and 3rd degree) of a given profile
connections = api.get_profile_connections('1234asc12304', max_connections=200)
```

## Documentation

For a complete reference documentation, see the [DOCS.md](https://github.com/tomquirk/linkedin-api/blob/master/DOCS.md)

## Development Setup

### Dependencies

- Python 3.7
- A valid Linkedin user account (don't use your personal account, if possible)
- Pipenv (optional)

### Installation

1. Create a `.env` config file. An example is provided in `.env.example` - you include at least all of the settings set there.
2. Using pipenv...

   ```
   $ pipenv install --dev
   $ pipenv shell
   ```

### Running tests

```
$ python -m pytest tests
```

### Troubleshooting

#### > I keep getting a CHALLENGE!?!

Linkedin will throw you a curve ball in the form of a Challenge URL. We currently don't handle this, and so you're kinda screwed. We think it could be only IP-based (i.e. logging in from different location). Your best chance at resolution is to log out and log back in on your browser.

##### Known reasons for Challenge:

- 2FA
- Rate-limit - "It looks like you’re visiting a very high number of pages on LinkedIn.". Note - n=1 experiment where this page was hit after ~900 contiguous requests in a single session (within the hour) (these included random delays between each request), as well as a bunch of testing, so who knows the actual limit.

Please add more as you come across them.

#### Search woes

- Mileage may vary when searching general keywords like "software" using the standard `search` method. They've recently added some smarts around search whereby they group results by people, company, jobs etc. if the query is general enough. Try to use an entity-specific search method (i.e. search_people) where possible.

<a name="in-depth-overview"></a>

## In-depth overview

Voyager endpoints look like this:

```
https://www.linkedin.com/voyager/api/identity/profileView/tom-quirk
```

Or, more clearly

```
 ___________________________________ _______________________________
|             base path             |            resource           |
https://www.linkedin.com/voyager/api /identity/profileView/tom-quirk
```

They are authenticated with a simple cookie, which we send with every request, along with a bunch of headers.

To get a cookie, we POST a given username and password (of a valid Linkedin user account) to `https://www.linkedin.com/uas/authenticate`.

<a name="to-find-endpoints"></a>

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

### How Clients query Voyager

Linkedin seems to have developed an internal query language/syntax where Clients (i.e. front-ends like linkedin.com) to specify what data they want (similar to the GraphQL concept). **If anyone knows what this is, I'd love to know!**.

Here's an example of making a request for an organisation's `name` and `groups` (the Linkedin groups it manages):

```
/voyager/api/organization/companies?decoration=(name,groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url))&q=universalName&universalName=linkedin
```

The "querying" happens in the `decoration` parameter, which looks like

```
(
    name,
    groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url)
)
```

So here, we request an organisation name, and a list of groups, where for each group we want `largeLogo`, `groupName`, etc.

Different endpoints use different parameters (and perhaps even different syntaxes) to specify these queries. Notice that the above query had a parameter `q` whose value was `universalName`; the query was then specified with the `decoration` parameter.

In contrast, the `/search/cluster` endpoint uses `q=guided`, and specifies its query with the `guided` parameter, whose value is something like

```
List(v->PEOPLE)
```

It could be possible to document (and implement a nice interface for) this query language - as we add more endpoints to this project, I'm sure it will become more clear if such a thing would be possible (and if it's worth it).

<a name="t-c"></a>

## Terms and Conditions

By using this project, you agree to the following Terms and Conditions. We reserve the right to block any user of this repository that does not meet these conditions.

### Usage

This project may not be used for any of the following:

* Commercial use
* Spam
* Storage of any Personally Identifiable Information
* Personal abuse (i.e. verbal abuse)

<a name="legal"></a>

## Legal

This code is in no way affiliated with, authorized, maintained, sponsored or endorsed by Linkedin or any of its affiliates or subsidiaries. This is an independent and unofficial API. Use at your own risk.

This project violates Linkedin's User Agreement Section 8.2, and because of this, Linkedin may (and will) temporarily or permantly ban your account. We are not responsible for your account being banned.
