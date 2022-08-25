import logging
from linkedin_api import Linkedin

log = logging.getLogger(__name__)

# Authenticate using any Linkedin account credentials
api = Linkedin('yourUsername', 'your password')
print("*******APIs", api)

# GET a profile
profile = api.get_profile('billy-g')
print("************Profile: ", profile)
# # GET a profiles contact info
# contact_info = api.get_profile_contact_info('billy-g')

# # GET 1st degree connections of a given profile
# connections = api.get_profile_connections('1234asc12304')