import json
from linkedin_api import Linkedin

with open("credentials.json", "r") as f:
    credentials = json.load(f)

if credentials:
    linkedin = Linkedin(credentials["username"], credentials["password"])

    profile = linkedin.get_profile("ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw")
    profile["contact_info"] = linkedin.get_profile_contact_info(
        "ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw"
    )
    connections = linkedin.get_profile_connections(profile["profile_id"])
