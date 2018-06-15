# linkedin_api

(unofficial) Python wrapper for the Linkedin API

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
1. Using pipenv...

```
$ pipenv install
$ pipenv shell
```
