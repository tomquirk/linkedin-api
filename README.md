# linkedin_api

👨‍💼 Linkedin API for Python

[![Build Status](https://travis-ci.com/tomquirk/linkedin-api.svg?branch=master)](https://travis-ci.com/tomquirk/linkedin-api)
[![Documentation Status](https://readthedocs.org/projects/linkedin-api/badge/?version=latest)](https://linkedin-api.readthedocs.io/en/latest/?badge=latest)

> No "official" API access required - just use a valid Linkedin account!

Programmatically send messages, get jobs, search profiles and more, all with a regular Linkedin user account!

Before using this project, please consult the [Terms and Conditions](#terms-and-conditions) and [Legal Notice](#legal).

## Installation

> ⚠️ Python >= 3.6 required

```bash
pip3 install linkedin-api~=2.0.0a
```

> [Why v2.0.0a?](#versioning-note)

### Example usage

```python
from linkedin_api import Linkedin

# Authenticate using any Linkedin account credentials
api = Linkedin('reedhoffman@linkedin.com', '*******')

# GET a profile
profile = api.get_profile('billy-g')

# GET a profiles contact info
contact_info = api.get_profile_contact_info('billy-g')

# GET 1st degree connections of a given profile
connections = api.get_profile_connections('1234asc12304')
```

## Documentation

For a complete reference documentation, see the [documentation website](https://linkedin-api.readthedocs.io/).

## Overview

This project attempts to provide a simple Python interface for the Linkedin API.

> Do you mean the [legit Linkedin API](https://developer.linkedin.com/)?

NO! To retrieve structured data, the [Linkedin Website](https://linkedin.com) uses a service they call **Voyager**. Voyager endpoints give us access to pretty much everything we could want from Linkedin: profiles, companies, connections, messages, etc. - anything that you can see on linkedin.com, we can get from Voyager.

So specifically, this project aims to provide complete coverage for Voyager.

[How do we do it?](#in-depth-overview)

### How to contribute

[Learn how to find endpoints](#to-find-endpoints)

## Development Setup

### Dependencies

- Python 3.7
- A valid Linkedin user account (don't use your personal account, if possible)
- `pipenv` (optional)

### Development installation

1. Create a `.env` config file. An example is provided in `.env.example` - you include at least all of the settings set there.
2. Using pipenv...

   ```bash
   pipenv install --dev
   pipenv shell
   ```

### Running tests

```bash
python -m pytest tests
```

### Troubleshooting

#### I keep getting a `CHALLENGE`

Linkedin will throw you a curve ball in the form of a Challenge URL. We currently don't handle this, and so you're kinda screwed. We think it could be only IP-based (i.e. logging in from different location). Your best chance at resolution is to log out and log back in on your browser.

**Known reasons for Challenge** include:

- 2FA
- Rate-limit - "It looks like you’re visiting a very high number of pages on LinkedIn.". Note - n=1 experiment where this page was hit after ~900 contiguous requests in a single session (within the hour) (these included random delays between each request), as well as a bunch of testing, so who knows the actual limit.

Please add more as you come across them.

#### Search problems

- Mileage may vary when searching general keywords like "software" using the standard `search` method. They've recently added some smarts around search whereby they group results by people, company, jobs etc. if the query is general enough. Try to use an entity-specific search method (i.e. search_people) where possible.

## In-depth overview

Voyager endpoints look like this:

```text
https://www.linkedin.com/voyager/api/identity/profileView/tom-quirk
```

Or, more clearly

```text
 ___________________________________ _______________________________
|             base path             |            resource           |
https://www.linkedin.com/voyager/api /identity/profileView/tom-quirk
```

They are authenticated with a simple cookie, which we send with every request, along with a bunch of headers.

To get a cookie, we POST a given username and password (of a valid Linkedin user account) to `https://www.linkedin.com/uas/authenticate`.

### To find endpoints

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

4. The value of `request` is the url! 🤘

You can also use the `network` tab in you browsers developer tools, but you will encounter mixed results.

### How Clients query Voyager

Linkedin seems to have developed an internal query language/syntax where Clients (i.e. front-ends like linkedin.com) to specify what data they want (similar to the GraphQL concept). **If anyone knows what this is, I'd love to know!**.

Here's an example of making a request for an organisation's `name` and `groups` (the Linkedin groups it manages):

```text
/voyager/api/organization/companies?decoration=(name,groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url))&q=universalName&universalName=linkedin
```

The "querying" happens in the `decoration` parameter, which looks like

```text
(
    name,
    groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url)
)
```

So here, we request an organisation name, and a list of groups, where for each group we want `largeLogo`, `groupName`, etc.

Different endpoints use different parameters (and perhaps even different syntaxes) to specify these queries. Notice that the above query had a parameter `q` whose value was `universalName`; the query was then specified with the `decoration` parameter.

In contrast, the `/search/cluster` endpoint uses `q=guided`, and specifies its query with the `guided` parameter, whose value is something like

```text
List(v->PEOPLE)
```

It could be possible to document (and implement a nice interface for) this query language - as we add more endpoints to this project, I'm sure it will become more clear if such a thing would be possible (and if it's worth it).

## Terms and Conditions

By using this project, you agree to the following Terms and Conditions. We reserve the right to block any user of this repository that does not meet these conditions.

### Usage

This project may not be used for any of the following:

- Commercial use
- Spam
- Storage of any Personally Identifiable Information
- Personal abuse (i.e. verbal abuse)

## Legal

This code is in no way affiliated with, authorized, maintained, sponsored or endorsed by Linkedin or any of its affiliates or subsidiaries. This is an independent and unofficial API. Use at your own risk.

This project violates Linkedin's User Agreement Section 8.2, and because of this, Linkedin may (and will) temporarily or permanently ban your account. We are not responsible for your account being banned.

## Versioning Note

**Tl;dr:** Don't use anything < v2.0.0a.

Releases/tags for this package have not been kept up to date with changes and thus versions (like v1.0.0) are misleading and do not represent "stability".
Eventually, v2.0.0 will be the "stable" release.
