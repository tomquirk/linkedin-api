# Documentation

## The `Linkedin` instance

### Linkedin(username, password, refresh_cookies=False, debug=False, proxies=proxies)

Where it all begins. Create an instance of `Linkedin` to get started. You'll automatically get authenticated.

**Arguments**

- `username <str>` - Linkedin username
- `password <str>` - Linkedin password
- `refresh_cookies <boolean>: kwarg` - Whether to refresh any cached cookies
- `debug <boolean>: kwarg` - Enable debug logging
- `proxies <dict>: kwarg` - Proxies to use, of [Python Requests](https://python-requests.org/en/master/user/advanced/#proxies) format

## API Reference

- [`linkedin.get_profile`](#get_profile)
- [`linkedin.get_profile_connections`](#get_profile_connections)
- [`linkedin.get_profile_contact_info`](#get_profile_contact_info)
- [`linkedin.get_profile_skills`](#get_profile_skills)
- [`linkedin.get_profile_privacy_settings`](#get_profile_privacy_settings)
- [`linkedin.get_profile_member_badges`](#get_profile_member_badges)
- [`linkedin.get_profile_network_info`](#get_profile_network_info)
- [`linkedin.remove_connection`](#remove_connection)

- [`linkedin.get_conversations`](#get_conversations)
- [`linkedin.get_conversation_details`](#get_conversation_details)
- [`linkedin.get_conversation`](#get_conversation)
- [`linkedin.send_message`](#send_message)
- [`linkedin.mark_conversation_as_seen`](#mark_conversation_as_seen)

- [`linkedin.get_current_profile_views`](#get_current_profile_views)

- [`linkedin.get_school`](#get_school)
- [`linkedin.get_company`](#get_company)

- [`linkedin.search`](#search)
- [`linkedin.search_people`](#search_people)
- [`linkedin.search_companies`](#search_companies)

- [`linkedin.get_invitations`](#get_invitations)
- [`linkedin.reply_invitation`](#reply_invitation)

---

<a name="get_profile"></a>

### linkedin.get_profile(public_id=None, urn_id=None)

Returns a Linkedin profile.

**Arguments**
One of:

- `public_id <str>` - public identifier i.e. tom-quirk-1928345
- `urn_id <str>` - id provided by the Linkedin URN

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile('tom-quirk')
```

---

<a name="get_profile_connections"></a>

### linkedin.get_profile(urn_id)

Returns a Linkedin profile's first degree (direct) connections

**Arguments**

- `urn_id <str>` - id provided by the Linkedin URN

**Return**

- `<list>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

connections = linkedin.get_profile_connections('AC000102305')
```

---

<a name="get_profile_contact_info"></a>

### linkedin.get_profile_contact_info(urn_id)

Returns a Linkedin profile's contact information.

**Arguments**
One of:

- `public_id <str>` - public identifier i.e. tom-quirk-1928345
- `urn_id <str>` - id provided by the Linkedin URN

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile_info = linkedin.get_profile_contact_info('tom-quirk')
```

---

<a name="get_profile_skills"></a>

### linkedin.get_profile_skills(urn_id)

Returns a Linkedin profile's skills.

**Arguments**
One of:

- `public_id <str>` - public identifier i.e. tom-quirk-1928345
- `urn_id <str>` - id provided by the Linkedin URN

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile_info = linkedin.get_profile_skills('AC000102305')
```

---

<a name="remove_connection"></a>

### linkedin.remove_connection(public_id)

Removes a connection on Linkedin

**Arguments**

- `public_id <str>` - public identifier i.e. tom-quirk-1928345

**Return**

- `<bool>` - True if err

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

err = linkedin.remove_connection('tom-tom-quirk-1928345')
```

---

<a name="get_school"></a>

### linkedin.get_school(public_id)

Returns a school's Linkedin profile.

**Arguments**

- `public_id <str>` - public identifier i.e. university-of-queensland

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

school = linkedin.get_school('university-of-queensland')
```

---

<a name="get_company"></a>

### linkedin.get_company(public_id)

Returns a company's Linkedin profile.

**Arguments**

- `public_id <str>` - public identifier i.e. linkedin

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

company = linkedin.get_company('linkedin')
```

---

<a name="search"></a>

### linkedin.search(params, max_results=None, results=[])

Perform a Linkedin search and return the results.
A reference of country and industry codes can be found [here](https://developer.linkedin.com/docs/reference).

**Arguments**

- `params <dict>` - search parameters (see implementation of [search_people](#search_people) for a reference)
- `max_results <int> - the max number of results to return

**Return**

- `<list>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

results = linkedin.search({'keywords': 'software'}, 200)
```

---

<a name="get_conversations"></a>

### linkedin.get_conversations()

Return a list of metadata of the user's conversations.

**Return**

- `<list>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

conversations = linkedin.get_conversations()
```

---

<a name="get_conversation"></a>

### linkedin.get_conversation(conversation_urn_id)

Return a conversation

**Arguments**

- `conversation_urn_id <str>` - ID of the conversation

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

conversation = linkedin.get_conversation('6446595445958545408')
```

---

<a name="get_conversation_details"></a>

### linkedin.get_conversation_details(profile_urn_id)

Return the conversation details (metadata) for a given profile_urn_id.
Use this endpoint to get the `conversation id` to send messages (see example).

**Arguments**

- `profile_urn_id <str>` - the urn id of the profile

**Return**

- `<dict>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile('bill-g')
profile_urn_id = profile['profile_id']

conversation_details = linkedin.get_conversation_details(profile_urn_id)
# example: getting the conversation_id
conversation_id = conversation_details['id']
```

---

<a name="send_message"></a>

### linkedin.send_message(conversation_urn_id=None, recipients=None, message_body=None)

Sends a message to the given [conversation_urn_id] OR list of recipients

**Arguments**

- `conversation_urn_id <str>` - the urn id of the conversation
- `recipients <list(str)>` - a list of profile urn id's
- `message_body <str>` - the message to send

**Return**

- `<boolean>` - True if error

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile('bill-g')
profile_urn_id = profile['profile_id']

conversation = linkedin.get_conversation_details(profile_urn_id)
conversation_id = conversation['id']

err = linkedin.send_message(conversation_urn_id=conversation_id, message_body="No I will not be your technical cofounder")
if err:
    # handle error
    return
```

---

<a name="mark_conversation_as_seen"></a>

### linkedin.mark_conversation_as_seen(conversation_urn_id)

Mark a given conversation as seen.

**Arguments**

- `conversation_urn_id <str>` - the urn id of the conversation

**Return**

- `<boolean>` - True if error

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile('bill-g')
profile_urn_id = profile['profile_id']

conversation = linkedin.get_conversation_details(profile_urn_id)
conversation_id = conversation['id']

err = linkedin.mark_conversation_as_seen(conversation_id)
if err:
    # handle error
    return
```

---

<a name="get_current_profile_views"></a>

### linkedin.get_current_profile_views()

Get view statistics for the current profile. Includes views over time (chart data)

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

views = linkedin.get_current_profile_views()
```

---

<a name="search_people"></a>

### linkedin.search_people(keywords=None, connection_of=None, network_depth=None, regions=None, industries=None)

Perform a Linkedin search for people and return the results.
A reference of country and industry codes can be found [here](https://developer.linkedin.com/docs/reference).

**Arguments**

- `keywords <str>` - keywords, comma seperated
- `connection_of <str>` - urn id of a profile. Only people connected to this profile are returned
- `network_depth <str>` - the network depth to search within. One of {`F`, `S`, or `O`} (first, second and third+ respectively)
- `regions <list>` - list of Linkedin region ids
- `industries <list>` - list of Linkedin industry ids
- ... more (see code)

**Return**

- `<list>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

results = linkedin.search_people(
  keywords='software,lol',
  connection_of='AC000120303',
  network_depth='F',
  regions=['au:4909'],
  industries=['29', '1']
)
```

---

<a name="search_companies"></a>

### linkedin.search_companies(keywords=None, connection_of=None, network_depth=None, regions=None, industries=None)

Perform a Linkedin search for companies and return the results.

**Arguments**

- `keywords <str>` - keywords, comma seperated
- `limit <int>` - search limit

**Return**

- `<list>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

results = linkedin.search_companies(
  keywords='linkedin'
)
```

---

<a name="get_invitations"></a>

### linkedin.get_invitations()

Get all the invitations for the current authenticated profile.

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

invitations = linkedin.get_invitations()
```

---

<a name="reply_invitation"></a>

### linkedin.reply_invitation(invitation_entity_urn, invitation_shared_secret, action="accept")

Reply to the given invite (invitation_entity_urn) with one of the possible actions action=["accept"|"ignore"].
The default is to accept the given invitation.

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

invite_to_accept = linkedin.get_invitations()[0]
invite_to_ignore = linkedin.get_invitations()[1]

linkedin.reply_invitation(invitation_entity_urn=invite_to_accept['entityUrn'], invitation_shared_secret=invite_to_accept['sharedSecret'])
linkedin.reply_invitation(invitation_entity_urn=invite_to_ignore['entityUrn'], invitation_shared_secret=invite_to_ignore['sharedSecret'], action="ignore")
```

---

<a name="view_profile"></a>

### linkedin.view_profile(public_id)

Send a profile view (i.e. "<your_name> viewed your profile")

#### NOTE: method does not work

**Arguments**

- `public_id <str>` - public identifier i.e. tom-quirk-1928345

**Return**

- `<boolean>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.view_profile('tom-quirk')
```

---

<a name="get_profile_privacy_settings"></a>

### linkedin.get_profile_privacy_settings(public_id)

Get the privacy settings for a given profile. Useful to determine whether the profile is publicly accessible.

**Arguments**

- `public_id <str>` - public identifier i.e. tom-quirk-1928345

**Return**

- `<boolean>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile_privacy_settings('tom-quirk')
```

---

<a name="get_profile_member_badges"></a>

### linkedin.get_profile_member_badges(public_id)

Get member badges for a given profile. As of writing this, badges may include:

- `influencer <boolean>`
- `jobSeeker <boolean>`
- `openLink <boolean>`
- `premium <boolean>`

**Arguments**

- `public_id <str>` - public identifier i.e. tom-quirk-1928345

**Return**

- `<boolean>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile_member_badges('tom-quirk')
```

---

<a name="get_profile_network_info"></a>

### linkedin.get_profile_network_info(public_id)

Get high level information about a given profile's network. Useful for follower counts followability, distance from the authed user, etc.

**Arguments**

- `public_id <str>` - public identifier i.e. tom-quirk-1928345

**Return**

- `<boolean>`

**Example**

```python
linkedin = Linkedin(credentials['username'], credentials['password'])

profile = linkedin.get_profile_network_info('tom-quirk')
```
