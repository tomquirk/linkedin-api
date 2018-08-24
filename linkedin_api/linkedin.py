"""
Provides linkedin api-related code
"""
import random
import logging
from time import sleep
import json

from linkedin_api.utils.helpers import get_id_from_urn

from linkedin_api.client import Client

logger = logging.getLogger(__name__)


class Linkedin(object):
    """
    Class for accessing Linkedin API.
    """

    _MAX_UPDATE_COUNT = 100 # max seems to be 100
    _MAX_SEARCH_COUNT = 49  # max seems to be 49
    _MAX_REPEATED_REQUESTS = (
        200
    )  # VERY conservative max requests count to avoid rate-limit

    def __init__(self, username, password):
        self.client = Client()
        self.client.authenticate(username, password)

        self.logger = logger

    def search(self, params, max_results=None, results=[]):
        """
        Do a search.
        """
        sleep(
            random.randint(0, 1)
        )  # sleep a random duration to try and evade suspention

        count = (
            max_results
            if max_results and max_results <= Linkedin._MAX_SEARCH_COUNT
            else Linkedin._MAX_SEARCH_COUNT
        )
        default_params = {
            "count": count,
            "guides": "List()",
            "origin": "GLOBAL_SEARCH_HEADER",
            "q": "guided",
            "start": len(results),
        }

        default_params.update(params)

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/search/cluster", params=default_params
        )
        data = res.json()

        total_found = data.get("paging", {}).get("total")
        if total_found == 0 or total_found is None:
            self.logger.debug("found none...")
            return []

        # recursive base case
        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or len(results) >= total_found
            or (max_results is not None and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS)
        ):
            return results

        results.extend(data["elements"][0]["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.search(params, results=results, max_results=max_results)

    def search_people(
        self,
        keywords=None,
        connection_of=None,
        network_depth=None,
        regions=None,
        industries=None,
    ):
        """
        Do a people search.
        """
        guides = ["v->PEOPLE"]
        if connection_of:
            guides.append(f"facetConnectionOf->{connection_of}")
        if network_depth:
            guides.append(f"facetNetwork->{network_depth}")
        if regions:
            guides.append(f'facetGeoRegion->{"|".join(regions)}')
        if industries:
            guides.append(f'facetIndustry->{"|".join(industries)}')

        params = {"guides": "List({})".format(",".join(guides))}

        if keywords:
            params["keywords"] = keywords

        data = self.search(params)

        results = []
        for item in data:
            search_profile = item["hitInfo"][
                "com.linkedin.voyager.search.SearchProfile"
            ]
            profile_id = search_profile["id"]
            distance = search_profile["distance"]["value"]

            results.append(
                {
                    "urn_id": profile_id,
                    "distance": distance,
                    "public_id": search_profile["miniProfile"]["publicIdentifier"],
                }
            )

        return results

    def get_profile_contact_info(self, public_id=None, urn_id=None):
        """
        Return data for a single profile.

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/identity/profiles/{public_id or urn_id}/profileContactInfo"
        )
        data = res.json()

        contact_info = {
            "email_address": data.get("emailAddress"),
            "websites": [],
            "phone_numbers": data.get("phoneNumbers", []),
        }

        websites = data.get("websites", [])
        for item in websites:
            if "com.linkedin.voyager.identity.profile.StandardWebsite" in item["type"]:
                item["label"] = item["type"][
                    "com.linkedin.voyager.identity.profile.StandardWebsite"
                ]["category"]
            elif "" in item["type"]:
                item["label"] = item["type"][
                    "com.linkedin.voyager.identity.profile.CustomWebsite"
                ]["label"]

            del item["type"]

        contact_info["websites"] = websites

        return contact_info

    def get_profile(self, public_id=None, urn_id=None):
        """
        Return data for a single profile.

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        sleep(
            random.randint(2, 5)
        )  # sleep a random duration to try and evade suspention
        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/identity/profiles/{public_id or urn_id}/profileView"
        )

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        # massage [profile] data
        profile = data["profile"]
        if "miniProfile" in profile:
            if "picture" in profile["miniProfile"]:
                profile["displayPictureUrl"] = profile["miniProfile"]["picture"][
                    "com.linkedin.common.VectorImage"
                ]["rootUrl"]
            profile["profile_id"] = get_id_from_urn(profile["miniProfile"]["entityUrn"])

            del profile["miniProfile"]

        del profile["defaultLocale"]
        del profile["supportedLocales"]
        del profile["versionTag"]
        del profile["showEducationOnProfileTopCard"]

        # massage [experience] data
        experience = data["positionView"]["elements"]
        for item in experience:
            if "company" in item and "miniCompany" in item["company"]:
                if "logo" in item["company"]["miniCompany"]:
                    logo = item["company"]["miniCompany"]["logo"].get(
                        "com.linkedin.common.VectorImage"
                    )
                    if logo:
                        item["companyLogoUrl"] = logo["rootUrl"]
                del item["company"]["miniCompany"]

        profile["experience"] = experience

        # massage [skills] data
        skills = [item["name"] for item in data["skillView"]["elements"]]

        profile["skills"] = skills

        # massage [education] data
        education = data["educationView"]["elements"]
        for item in education:
            if "school" in item:
                if "logo" in item["school"]:
                    item["school"]["logoUrl"] = item["school"]["logo"][
                        "com.linkedin.common.VectorImage"
                    ]["rootUrl"]
                    del item["school"]["logo"]

        profile["education"] = education

        return profile

    def get_profile_connections(self, urn_id):
        """
        Return a list of profile ids connected to profile of given [urn_id]
        """
        return self.search_people(connection_of=urn_id, network_depth="F")

    def get_company_updates(self, public_id=None, urn_id=None, max_results=None, results=[]):
        """"
        Return a list of company posts

        [public_id] - public identifier ie - microsoft
        [urn_id] - id provided by the related URN
        """
        sleep(
            random.randint(2, 5)
        )  # sleep a random duration to try and evade suspention

        params = {
            "companyUniversalName": {public_id or urn_id},
            "q": "companyFeedByUniversalName",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/feed/updates", params=params
        )

        data = res.json()
        
        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (max_results is not None and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS)
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_company_updates(public_id=public_id, urn_id=urn_id, results=results, max_results=max_results)

    def get_profile_updates(self, public_id=None, urn_id=None, max_results=None, results=[]):
        """"
        Return a list of profile posts

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        sleep(
            random.randint(2, 5)
        )  # sleep a random duration to try and evade suspention

        params = {
            "profileId": {public_id or urn_id},
            "q": "memberShareFeed",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/feed/updates", params=params
        )

        data = res.json()
        
        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (max_results is not None and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS)
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_profile_updates(public_id=public_id, urn_id=urn_id, results=results, max_results=max_results)

    def get_current_profile_views(self):
        """
        Get profile view statistics, including chart data.
        """
        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/identity/panels"
        )

        data = res.json()

        return data['elements'][0]['value']['com.linkedin.voyager.identity.me.ProfileViewsByTimePanel']


    def get_school(self, public_id):
        """
        Return data for a single school.

        [public_id] - public identifier i.e. uq
        """
        sleep(
            random.randint(2, 5)
        )  # sleep a random duration to try and evade suspention
        params = {
            "decoration": (
                """
                (
                autoGenerated,backgroundCoverImage,
                companyEmployeesSearchPageUrl,companyPageUrl,confirmedLocations*,coverPhoto,dataVersion,description,
                entityUrn,followingInfo,foundedOn,headquarter,jobSearchPageUrl,lcpTreatment,logo,name,type,overviewPhoto,
                paidCompany,partnerCompanyUrl,partnerLogo,partnerLogoImage,rankForTopCompanies,salesNavigatorCompanyUrl,
                school,showcase,staffCount,staffCountRange,staffingCompany,topCompaniesListName,universalName,url,
                companyIndustries*,industries,specialities,
                acquirerCompany~(entityUrn,logo,name,industries,followingInfo,url,paidCompany,universalName),
                affiliatedCompanies*~(entityUrn,logo,name,industries,followingInfo,url,paidCompany,universalName),
                groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url),
                showcasePages*~(entityUrn,logo,name,industries,followingInfo,url,description,universalName)
                )
                """
            ),
            "q": "universalName",
            "universalName": public_id,
        }

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/organization/companies", params=params
        )

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        school = data["elements"][0]

        return school

    def get_company(self, public_id):
        """
        Return data for a single company.

        [public_id] - public identifier i.e. univeristy-of-queensland
        """
        sleep(
            random.randint(2, 5)
        )  # sleep a random duration to try and evade suspention
        params = {
            "decoration": (
                """
                (
                affiliatedCompaniesWithEmployeesRollup,affiliatedCompaniesWithJobsRollup,articlePermalinkForTopCompanies,
                autoGenerated,backgroundCoverImage,companyEmployeesSearchPageUrl,
                companyPageUrl,confirmedLocations*,coverPhoto,dataVersion,description,entityUrn,followingInfo,
                foundedOn,headquarter,jobSearchPageUrl,lcpTreatment,logo,name,type,overviewPhoto,paidCompany,
                partnerCompanyUrl,partnerLogo,partnerLogoImage,permissions,rankForTopCompanies,
                salesNavigatorCompanyUrl,school,showcase,staffCount,staffCountRange,staffingCompany,
                topCompaniesListName,universalName,url,companyIndustries*,industries,specialities,
                acquirerCompany~(entityUrn,logo,name,industries,followingInfo,url,paidCompany,universalName),
                affiliatedCompanies*~(entityUrn,logo,name,industries,followingInfo,url,paidCompany,universalName),
                groups*~(entityUrn,largeLogo,groupName,memberCount,websiteUrl,url),
                showcasePages*~(entityUrn,logo,name,industries,followingInfo,url,description,universalName)
                )
                """
            ),
            "q": "universalName",
            "universalName": public_id,
        }

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/organization/companies", params=params
        )

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        company = data["elements"][0]

        return company

    def get_conversation_details(self, profile_urn_id):
        """
        Return the conversation (or "message thread") details for a given [public_profile_id]
        """
        # passing `params` doesn't work properly, think it's to do with List().
        # Might be a bug in `requests`?
        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/messaging/conversations?\
            keyVersion=LEGACY_INBOX&q=participants&recipients=List({profile_urn_id})"
        )

        data = res.json()

        item = data["elements"][0]
        item["id"] = get_id_from_urn(item["entityUrn"])

        return item

    def get_conversations(self):
        """
        Return list of conversations the user is in.
        """
        params = {"keyVersion": "LEGACY_INBOX"}

        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/messaging/conversations", params=params
        )

        return res.json()

    def get_conversation(self, conversation_urn_id):
        """
        Return the full conversation at a given [conversation_urn_id]
        """
        res = self.client.session.get(
            f"{self.client.API_BASE_URL}/messaging/conversations/{conversation_urn_id}/events"
        )

        return res.json()

    def send_message(self, conversation_urn_id, message_body):
        """
        Return the full conversation at a given [conversation_urn_id]
        """
        params = {"action": "create"}

        payload = json.dumps(
            {
                "eventCreate": {
                    "value": {
                        "com.linkedin.voyager.messaging.create.MessageCreate": {
                            "body": message_body,
                            "attachments": [],
                            "attributedBody": {"text": message_body, "attributes": []},
                            "mediaAttachments": [],
                        }
                    }
                }
            }
        )

        res = self.client.session.post(
            f"{self.client.API_BASE_URL}/messaging/conversations/{conversation_urn_id}/events",
            params=params,
            data=payload,
        )

        return res.status_code == 201
