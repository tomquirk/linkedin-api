user = "you@example.com"
# b64 encoded
password = "b64encodedpassword="

# What to look for in groups search
keywords = "barcelona"

# Path to output CSV file
path_file = "groups.csv"

# Number of groups to be returned
limit = 1000

######### Don't touch anything below this line ###########

from linkedin_api import Linkedin
from linkedin_api.utils.helpers import get_id_from_urn
from base64 import b64decode
from csv import writer

api = Linkedin(user, b64decode(password).decode("utf8"))

params = {
    "filters": "List(resultType->GROUPS)",
    "keywords": keywords,
    "queryContext": "List(spellCorrectionEnabled->true)",
}

l_d_groups = api.search(params, limit)

l_d_groups_sorted = sorted(
    l_d_groups,
    key=lambda k: int(
        k["headline"]["text"].split(" members")[0].split(" ")[2].replace(",", "")
    ),
    reverse=True,
)

l_l_groups = [
    (
        f"{api.client.LINKEDIN_BASE_URL}/groups/{get_id_from_urn(i['trackingUrn'])}",
        i["title"]["text"],
        i["headline"]["text"].split(" members")[0].split(" ")[2].replace(",", ""),
    )
    for i in l_d_groups_sorted
]

with open(path_file, "w") as f:
    writer = writer(f)
    writer.writerows(l_l_groups)
