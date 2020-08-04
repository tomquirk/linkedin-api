"""
Provides linkedin api-related code
"""
import json
import logging
import random
from time import sleep, time
from urllib.parse import urlencode, quote

from linkedin_api.client import Client
from linkedin_api.utils.helpers import get_id_from_urn

logger = logging.getLogger(__name__)


def default_evade():
    """
    A catch-all method to try and evade suspension from Linkedin.
    Currenly, just delays the request by a random (bounded) time
    """
    sleep(random.randint(2, 5))  # sleep a random duration to try and evade suspention


class Linkedin(object):
    """
    Class for accessing Linkedin API.
    """

    _MAX_UPDATE_COUNT = 100  # max seems to be 100
    _MAX_SEARCH_COUNT = 49  # max seems to be 49, and min seems to be 2
    _MAX_REPEATED_REQUESTS = (
        200  # VERY conservative max requests count to avoid rate-limit
    )

    def __init__(
        self,
        username,
        password,
        *,
        authenticate=True,
        refresh_cookies=False,
        debug=False,
        proxies={},
        cookies=None,
    ):
        self.client = Client(
            refresh_cookies=refresh_cookies, debug=debug, proxies=proxies
        )
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = logger

        if authenticate:
            if cookies:
                # If the cookies are expired, the API won't work anymore since
                # `username` and `password` are not used at all in this case.
                self.client._set_session_cookies(cookies)
            else:
                self.client.authenticate(username, password)

    def _fetch(self, uri, evade=default_evade, base_request=False, **kwargs):
        """
        GET request to Linkedin API
        """
        evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.get(url, **kwargs)

    def _post(self, uri, evade=default_evade, base_request=False, **kwargs):
        """
        POST request to Linkedin API
        """
        evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.post(url, **kwargs)

    def search(self, params, limit=-1, offset=0):
        """
        Do a search.
        """
        count = Linkedin._MAX_SEARCH_COUNT
        if limit is None:
            limit = -1

        results = []
        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(results) < count:
                count = limit - len(results)
            default_params = {
                "count": str(count),
                "filters": "List()",
                "origin": "GLOBAL_SEARCH_HEADER",
                "q": "all",
                "start": len(results) + offset,
                "queryContext": "List(spellCorrectionEnabled->true,relatedSearchesEnabled->true,kcardTypes->PROFILE|COMPANY)",
            }
            default_params.update(params)

            res = self._fetch(
                f"/search/blended?{urlencode(default_params, safe='(),')}",
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            data = res.json()

            new_elements = []
            elements = data.get("data", {}).get("elements", [])
            for i in range(len(elements)):
                new_elements.extend(elements[i]["elements"])
                # not entirely sure what extendedElements generally refers to - keyword search gives back a single job?
                # new_elements.extend(data["data"]["elements"][i]["extendedElements"])
            results.extend(new_elements)

            # break the loop if we're done searching
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            if (
                (
                    limit > -1 and len(results) >= limit
                )  # if our results exceed set limit
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(new_elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results

    def search_people(
        self,
        keywords=None,
        connection_of=None,
        network_depth=None,
        current_company=None,
        past_companies=None,
        nonprofit_interests=None,
        profile_languages=None,
        regions=None,
        industries=None,
        schools=None,
        title=None,  # `keyword_title` and `title` are the same. We kept `title` for backward compatibility. Please only use one of them.
        include_private_profiles=False,  # profiles without a public id, "Linkedin Member"
        # Keywords filter
        keyword_first_name=None,
        keyword_last_name=None,
        keyword_title=None,  # `keyword_title` and `title` are the same. We kept `title` for backward compatibility. Please only use one of them.
        keyword_company=None,
        keyword_school=None,
        **kwargs,
    ):
        """
        Do a people search.
        """
        filters = ["resultType->PEOPLE"]
        if connection_of:
            filters.append(f"connectionOf->{connection_of}")
        if network_depth:
            filters.append(f"network->{network_depth}")
        if regions:
            filters.append(f'geoRegion->{"|".join(regions)}')
        if industries:
            filters.append(f'industry->{"|".join(industries)}')
        if current_company:
            filters.append(f'currentCompany->{"|".join(current_company)}')
        if past_companies:
            filters.append(f'pastCompany->{"|".join(past_companies)}')
        if profile_languages:
            filters.append(f'profileLanguage->{"|".join(profile_languages)}')
        if nonprofit_interests:
            filters.append(f'nonprofitInterest->{"|".join(nonprofit_interests)}')
        if schools:
            filters.append(f'schools->{"|".join(schools)}')
        # `Keywords` filter
        keyword_title = keyword_title if keyword_title else title
        if keyword_first_name:
            filters.append(f"firstName->{keyword_first_name}")
        if keyword_last_name:
            filters.append(f"lastName->{keyword_last_name}")
        if keyword_title:
            filters.append(f"title->{keyword_title}")
        if keyword_company:
            filters.append(f"company->{keyword_company}")
        if keyword_school:
            filters.append(f"school->{keyword_school}")

        params = {"filters": "List({})".format(",".join(filters))}

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, **kwargs)

        results = []
        for item in data:
            if "publicIdentifier" not in item:
                continue
            results.append(
                {
                    "urn_id": get_id_from_urn(item.get("targetUrn")),
                    "distance": item.get("memberDistance", {}).get("value"),
                    "public_id": item.get("publicIdentifier"),
                    "tracking_id": get_id_from_urn(item.get("trackingUrn")),
                }
            )

        return results

    def search_companies(self, keywords=None, limit=None):
        """
        Do a company search.
        """
        filters = ["resultType->COMPANIES"]

        params = {
            "filters": "List({})".format(",".join(filters)),
            "queryContext": "List(spellCorrectionEnabled->true)",
        }

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, limit=limit)

        results = []
        for item in data:
            if item.get("type") != "COMPANY":
                continue
            results.append(
                {
                    "urn": item.get("targetUrn"),
                    "urn_id": get_id_from_urn(item.get("targetUrn")),
                    "name": item.get("title", {}).get("text"),
                    "headline": item.get("headline", {}).get("text"),
                    "subline": item.get("subline", {}).get("text"),
                }
            )

        return results

    def search_jobs(self, keywords, location, count=25, start=0, listed_at=86400):
        """
        Do a job search.

        [keywords] - any queries using OR, AND, (), ""
        [location] - job location
        [count] - number of jobs returned
        [start] - for paging to fetch the next set of results
        [sort_by] - sort by relevance "List(R)" or by most recent "List(DD)"
        [posted_at] - limits the results based on date posted, in seconds
        
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.jserp.WebJobSearchHit-22",
            "location": location,
            "origin": "JOB_SEARCH_RESULTS_PAGE",
            "start": start,
            "q": "jserpAll",
            "query": "search",
            "sortBy": "List(DD)",
        }

        # count must be below 50
        if count > 49:
            count = 49
        params["count"] = count

        # check if input is int
        if isinstance(listed_at, int):
            params["f_TPR"] = f"List(r{listed_at})"
        else:
            params["f_TPR"] = "List(r86400)"
        str_params = urlencode(params, safe="(),")

        # we need to encode the keywords incase it used brackets, otherwise it will return an error
        if keywords:
            keywords_encoded = f"&keywords={quote(keywords)}"
            str_params += keywords_encoded
        res = self._fetch(
            f"/search/hits?{str_params}",
            headers={
                "accept": "application/vnd.linkedin.normalized+json+2.1",
                "x-li-track": '{"clientVersion":"1.6.*","osName":"web","timezoneOffset":1,"deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":1.100000023841858}',
            },
        )

        data = res.json()
        return data

    def get_profile_contact_info(self, public_id=None, urn_id=None):
        """
        Return data for a single profile.

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        res = self._fetch(
            f"/identity/profiles/{public_id or urn_id}/profileContactInfo"
        )
        data = res.json()

        contact_info = {
            "email_address": data.get("emailAddress"),
            "websites": [],
            "twitter": data.get("twitterHandles"),
            "birthdate": data.get("birthDateOn"),
            "ims": data.get("ims"),
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

    def get_profile_skills(self, public_id=None, urn_id=None):
        """
        Return the skills of a profile.

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        params = {"count": 100, "start": 0}
        res = self._fetch(
            f"/identity/profiles/{public_id or urn_id}/skills", params=params
        )
        data = res.json()

        skills = data.get("elements", [])
        for item in skills:
            del item["entityUrn"]

        return skills

    def get_profile(self, public_id=None, urn_id=None, with_skills=True):
        """
        Return data for a single profile.

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        # NOTE this still works for now, but will probably eventually have to be converted to
        # https://www.linkedin.com/voyager/api/identity/profiles/ACoAAAKT9JQBsH7LwKaE9Myay9WcX8OVGuDq9Uw
        res = self._fetch(f"/identity/profiles/{public_id or urn_id}/profileView")

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
            profile["profile_urn"] = profile["miniProfile"]["entityUrn"]
            profile["member_urn"] = profile["miniProfile"]["objectUrn"]

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
        # skills = [item["name"] for item in data["skillView"]["elements"]]
        # profile["skills"] = skills

        profile["skills"] = (
            self.get_profile_skills(public_id=public_id, urn_id=urn_id)
            if with_skills
            else {}
        )

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

        # massage [languages] data
        languages = data["languageView"]["elements"]
        for item in languages:
            del item["entityUrn"]
        profile["languages"] = languages

        # massage [publications] data
        publications = data["publicationView"]["elements"]
        for item in publications:
            del item["entityUrn"]
            for author in item.get("authors", []):
                del author["entityUrn"]
        profile["publications"] = publications

        # massage [certifications] data
        certifications = data["certificationView"]["elements"]
        for item in certifications:
            del item["entityUrn"]
        profile["certifications"] = certifications

        # massage [volunteer] data
        volunteer = data["volunteerExperienceView"]["elements"]
        for item in volunteer:
            del item["entityUrn"]
        profile["volunteer"] = volunteer

        # massage [honors] data
        honors = data["honorView"]["elements"]
        for item in honors:
            del item["entityUrn"]
        profile["honors"] = honors

        return profile

    def get_profile_connections(self, urn_id=None):
        """
        Return a list of profile ids connected to profile of given [urn_id].
        If urn_id is None, then the currently logged in user's connections are returned
        """
        return self.search_people(connection_of=urn_id, network_depth="F")

    def get_company_updates(
        self, public_id=None, urn_id=None, max_results=None, results=[]
    ):
        """"
        Return a list of company posts

        [public_id] - public identifier ie - microsoft
        [urn_id] - id provided by the related URN
        """
        params = {
            "companyUniversalName": {public_id or urn_id},
            "q": "companyFeedByUniversalName",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self._fetch(f"/feed/updates", params=params)

        data = res.json()

        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (
                max_results is not None
                and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS
            )
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_company_updates(
            public_id=public_id, urn_id=urn_id, results=results, max_results=max_results
        )

    def get_profile_updates(
        self, public_id=None, urn_id=None, max_results=None, results=[]
    ):
        """"
        Return a list of profile posts

        [public_id] - public identifier i.e. tom-quirk-1928345
        [urn_id] - id provided by the related URN
        """
        params = {
            "profileId": {public_id or urn_id},
            "q": "memberShareFeed",
            "moduleKey": "member-share",
            "count": Linkedin._MAX_UPDATE_COUNT,
            "start": len(results),
        }

        res = self._fetch(f"/feed/updates", params=params)

        data = res.json()

        if (
            len(data["elements"]) == 0
            or (max_results is not None and len(results) >= max_results)
            or (
                max_results is not None
                and len(results) / max_results >= Linkedin._MAX_REPEATED_REQUESTS
            )
        ):
            return results

        results.extend(data["elements"])
        self.logger.debug(f"results grew: {len(results)}")

        return self.get_profile_updates(
            public_id=public_id, urn_id=urn_id, results=results, max_results=max_results
        )

    def get_current_profile_views(self):
        """
        Get profile view statistics, including chart data.
        """
        res = self._fetch(f"/identity/wvmpCards")

        data = res.json()

        return data["elements"][0]["value"][
            "com.linkedin.voyager.identity.me.wvmpOverview.WvmpViewersCard"
        ]["insightCards"][0]["value"][
            "com.linkedin.voyager.identity.me.wvmpOverview.WvmpSummaryInsightCard"
        ][
            "numViews"
        ]

    def get_school(self, public_id):
        """
        Return data for a single school.

        [public_id] - public identifier i.e. uq
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain-12",
            "q": "universalName",
            "universalName": public_id,
        }

        res = self._fetch(f"/organization/companies?{urlencode(params)}")

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data))
            return {}

        school = data["elements"][0]

        return school

    def get_company(self, public_id):
        """
        Return data for a single company.

        [public_id] - public identifier i.e. univeristy-of-queensland
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain-12",
            "q": "universalName",
            "universalName": public_id,
        }

        res = self._fetch(f"/organization/companies", params=params)

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
        res = self._fetch(
            f"/messaging/conversations?\
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

        res = self._fetch(f"/messaging/conversations", params=params)

        return res.json()

    def get_conversation(self, conversation_urn_id):
        """
        Return the full conversation at a given [conversation_urn_id]
        """
        res = self._fetch(f"/messaging/conversations/{conversation_urn_id}/events")

        return res.json()

    def send_message(self, conversation_urn_id=None, recipients=[], message_body=None):
        """
        Send a message to a given conversation. If error, return true.

        Recipients: List of profile urn id's
        """
        params = {"action": "create"}

        if not (conversation_urn_id or recipients) and not message_body:
            return True

        message_event = {
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

        if conversation_urn_id and not recipients:
            res = self._post(
                f"/messaging/conversations/{conversation_urn_id}/events",
                params=params,
                data=json.dumps(message_event),
            )
        elif recipients and not conversation_urn_id:
            message_event["recipients"] = recipients
            message_event["subtype"] = "MEMBER_TO_MEMBER"
            payload = {
                "keyVersion": "LEGACY_INBOX",
                "conversationCreate": message_event,
            }
            res = self._post(
                f"/messaging/conversations", params=params, data=json.dumps(payload)
            )

        return res.status_code != 201

    def mark_conversation_as_seen(self, conversation_urn_id):
        """
        Send seen to a given conversation. If error, return True.
        """
        payload = json.dumps({"patch": {"$set": {"read": True}}})

        res = self._post(
            f"/messaging/conversations/{conversation_urn_id}", data=payload
        )

        return res.status_code != 200

    def get_user_profile(self, use_cache=True):
        """"
        Return current user profile
        """
        me_profile = self.client.metadata.get("me")
        if not self.client.metadata.get("me") or not use_cache:
            res = self._fetch(f"/me")
            me_profile = res.json()
            # cache profile
            self.client.metadata["me"] = me_profile

        return me_profile

    def get_invitations(self, start=0, limit=3):
        """
        Return list of new invites
        """
        params = {
            "start": start,
            "count": limit,
            "includeInsights": True,
            "q": "receivedInvitation",
        }

        res = self._fetch(
            f"{self.client.API_BASE_URL}/relationships/invitationViews", params=params
        )

        if res.status_code != 200:
            return []

        response_payload = res.json()
        return [element["invitation"] for element in response_payload["elements"]]

    def reply_invitation(
        self, invitation_entity_urn, invitation_shared_secret, action="accept"
    ):
        """
        Reply to an invite, the default is to accept the invitation.
        @Param: invitation_entity_urn: str
        @Param: invitation_shared_secret: str
        @Param: action: "accept" or "ignore"
        Returns True if sucess, False otherwise
        """
        invitation_id = get_id_from_urn(invitation_entity_urn)
        params = {"action": action}
        payload = json.dumps(
            {
                "invitationId": invitation_id,
                "invitationSharedSecret": invitation_shared_secret,
                "isGenericInvitation": False,
            }
        )

        res = self._post(
            f"{self.client.API_BASE_URL}/relationships/invitations/{invitation_id}",
            params=params,
            data=payload,
        )

        return res.status_code == 200

    # def add_connection(self, profile_urn_id):
    #     payload = {
    #         "emberEntityName": "growth/invitation/norm-invitation",
    #         "invitee": {
    #             "com.linkedin.voyager.growth.invitation.InviteeProfile": {
    #                 "profileId": profile_urn_id
    #             }
    #         },
    #     }

    #     print(payload)

    #     res = self._post(
    #         "/growth/normInvitations",
    #         data=payload,
    #         headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
    #     )

    #     return res.status_code != 201

    def remove_connection(self, public_profile_id):
        res = self._post(
            f"/identity/profiles/{public_profile_id}/profileActions?action=disconnect",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )

        return res.status_code != 200

    def track(self, eventBody, eventInfo):
        payload = {"eventBody": eventBody, "eventInfo": eventInfo}
        res = self._post(
            "/li/track",
            base_request=True,
            headers={"accept": "*/*", "content-type": "text/plain;charset=UTF-8"},
            data=json.dumps(payload),
        )

        return res.status_code != 200

    def view_profile(
        self, public_profile_id, network_distance=None, target_member_id=None
    ):
        me_profile = self.get_user_profile()

        if not target_member_id:
            profile = self.get_profile(public_id=public_profile_id, with_skills=False)
            target_member_id = int(get_id_from_urn(profile["member_urn"]))

        if not network_distance:
            profile_network_info = self.get_profile_network_info(
                public_profile_id=public_profile_id
            )
            network_distance = int(
                profile_network_info["distance"]
                .get("value", "DISTANCE_2")
                .split("_")[1]
            )

        viewer_privacy_setting = "F"
        me_member_id = me_profile["plainId"]

        client_application_instance = self.client.metadata["clientApplicationInstance"]

        eventBody = {
            "viewerPrivacySetting": viewer_privacy_setting,
            "networkDistance": network_distance,
            "vieweeMemberUrn": f"urn:li:member:{target_member_id}",
            "profileTrackingId": self.client.metadata["clientPageInstanceId"],
            "entityView": {
                "viewType": "profile-view",
                "viewerId": me_member_id,
                "targetId": target_member_id,
            },
            "header": {
                "pageInstance": {
                    "pageUrn": "urn:li:page:d_flagship3_profile_view_base",
                    "trackingId": self.client.metadata["clientPageInstanceId"],
                },
                "time": int(time()),
                "version": client_application_instance["version"],
                "clientApplicationInstance": client_application_instance,
            },
            "requestHeader": {
                "interfaceLocale": "en_US",
                "pageKey": "d_flagship3_profile_view_base",
                "path": f"/in/{public_profile_id}/",
                "referer": "https://www.linkedin.com/feed/",
            },
        }

        return self.track(
            eventBody,
            {
                "appId": "com.linkedin.flagship3.d_web",
                "eventName": "ProfileViewEvent",
                "topicName": "ProfileViewEvent",
            },
        )

    def get_profile_privacy_settings(self, public_profile_id):
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/privacySettings",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_member_badges(self, public_profile_id):
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/memberBadges",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_network_info(self, public_profile_id):
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/networkinfo",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def unfollow_entity(self, urn):
        payload = {"urn": f"urn:li:fs_followingInfo:{urn}"}
        res = self._post(
            "/feed/follows?action=unfollowByEntityUrn",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            data=json.dumps(payload),
        )

        err = False
        if res.status_code != 200:
            err = True

        return err
