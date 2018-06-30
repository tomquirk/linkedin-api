# Documentation

* [`linkedin.get_profile`](#get_profile)
* [`linkedin.get_profile_connections`](#get_profile_connections)
* [`linkedin.get_profile_contact_info`](#get_profile_contact_info)

* [`linkedin.get_school`](#get_school)
* [`linkedin.get_company`](#get_company)

* [`linkedin.search`](#search)
* [`linkedin.search_people`](#search_people)

---------------------------------------

<a name="get_profile"></a>
### linkedin.get_profile(public_id=None, urn_id=None)

Returns a Linkedin profile.

__Arguments__
One of:
* `public_id`<str> - public identifier i.e. tom-quirk-1928345
* `urn_id`<str> - id provided by the Linkedin URN

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.get_profile('tom-quirk')
```

---------------------------------------

<a name="get_profile_connections"></a>
### linkedin.get_profile(urn_id)

Returns a Linkedin profile's first degree (direct) connections

__Arguments__
* `urn_id`<str> - id provided by the Linkedin URN

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.get_profile_connections('AC000102305')
```

---------------------------------------

<a name="get_profile_contact_info"></a>
### linkedin.get_profile_contact_info(urn_id)

Returns a Linkedin profile's contact information.

__Arguments__
One of:
* `public_id`<str> - public identifier i.e. tom-quirk-1928345
* `urn_id`<str> - id provided by the Linkedin URN

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.get_profile_contact_info('tom-quirk')
```

---------------------------------------

<a name="get_school"></a>
### linkedin.get_school(public_id)

Returns a school's Linkedin profile.

__Arguments__
* `public_id`<str> - public identifier i.e. university-of-queensland

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.get_school('university-of-queensland')
```

---------------------------------------

<a name="get_company"></a>
### linkedin.get_company(public_id)

Returns a company's Linkedin profile.

__Arguments__
* `public_id`<str> - public identifier i.e. linkedin

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.get_company('linkedin')
```

---------------------------------------

<a name="search"></a>
### linkedin.search(self, params, max_results=None, results=[])

Perform a Linkedin search and return the results.

__Arguments__
* `params`<dict> - search parameters (see implementation of [search_people](#search_people) for a reference)
* `max_results`<int> - the max number of results to return

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.search({keywords: 'software'}, 200)
```

---------------------------------------

<a name="search_people"></a>
### linkedin.search_people(self, keywords=None, connection_of=None, network_depth=None, regions=None, industries=None)

Perform a Linkedin search and return the results.

__Arguments__
* `keywords`<str> - keywords, comma seperated
* `connection_of`<str> - urn id of a profile. Only people connected to this profile are returned
* `network_depth`<str> - the network depth to search within. One of {`F`, `S`, or `O`} (first, second and third+ respectively)
* `regions`<list> - list of Linkedin region ids
* `industries`<list> - list of Linkedin industry ids

__Example__

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

linkedin.search_people(
  keywords='software,lol', 
  connection_of='AC000120303',
  network_depth='F',
  regions=[4909],
  industries=[29, 1]
)
```
