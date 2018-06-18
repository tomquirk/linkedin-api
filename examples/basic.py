import json
from linkedin_api import LinkedinAPI

api = LinkedinAPI()

with open('credentials.json', 'r') as f:
    credentials = json.load(f)

if credentials:
    api.authenticate(credentials['username'], credentials['password'])

    profile = api.get_profile('ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw')
    profile['contact_info'] = \
        api.get_profile_contact_info('ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw')
    connections = api.get_profile_connections(profile['profile_id'], max_connections=20)
