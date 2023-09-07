"""
Provides linkedin api-related code
"""
import base64
import json
import logging
import random
import uuid
from operator import itemgetter
from time import sleep, time
from urllib.parse import quote, urlencode

from linkedin_api.client import Client
from linkedin_api.utils.helpers import (
    append_update_post_field_to_posts_list,
    get_id_from_urn,
    get_urn_from_raw_update,
    get_list_posts_sorted_without_promoted,
    get_update_author_name,
    get_update_author_profile,
    get_update_content,
    get_update_old,
    get_update_url,
    parse_list_raw_posts,
    parse_list_raw_urns,
    generate_trackingId,
    generate_trackingId_as_charString,
)

logger = logging.getLogger(__name__)


def default_evade():
    """
    A catch-all method to try and evade suspension from Linkedin.
    Currenly, just delays the request by a random (bounded) time
    """
    sleep(random.randint(2, 5))  # sleep a random duration to try and evade suspention


class Linkedin(object):
    """
    Class for accessing the LinkedIn API.

    :param username: Username of LinkedIn account.
    :type username: str
    :param password: Password of LinkedIn account.
    :type password: str
    """

    _MAX_POST_COUNT = 100  # max seems to be 100 posts per page
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
        cookies_dir=None,
    ):
        """Constructor method"""
        self.client = Client(
            refresh_cookies=refresh_cookies,
            debug=debug,
            proxies=proxies,
            cookies_dir=cookies_dir,
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
        """GET request to Linkedin API"""
        evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.get(url, **kwargs)

    def _post(self, uri, evade=default_evade, base_request=False, **kwargs):
        """POST request to Linkedin API"""
        evade()

        url = f"{self.client.API_BASE_URL if not base_request else self.client.LINKEDIN_BASE_URL}{uri}"
        return self.client.session.post(url, **kwargs)

    def get_profile_posts(self, public_id=None, urn_id=None, post_count=10):
        """
        get_profile_posts: Get profile posts

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional
        :param post_count: Number of posts to fetch
        :type post_count: int, optional
        :return: List of posts
        :rtype: list
        """
        url_params = {
            "count": min(post_count, self._MAX_POST_COUNT),
            "start": 0,
            "q": "memberShareFeed",
            "moduleKey": "member-shares:phone",
            "includeLongTermHistory": True,
        }
        if urn_id:
            profile_urn = f"urn:li:fsd_profile:{urn_id}"
        else:
            profile = self.get_profile(public_id=public_id)
            profile_urn = profile["profile_urn"].replace(
                "fs_miniProfile", "fsd_profile"
            )
        url_params["profileUrn"] = profile_urn
        url = f"/identity/profileUpdatesV2"
        res = self._fetch(url, params=url_params)
        data = res.json()
        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}
        while data and data["metadata"]["paginationToken"] != "":
            if len(data["elements"]) >= post_count:
                break
            pagination_token = data["metadata"]["paginationToken"]
            url_params["start"] = url_params["start"] + self._MAX_POST_COUNT
            url_params["paginationToken"] = pagination_token
            res = self._fetch(url, params=url_params)
            data["metadata"] = res.json()["metadata"]
            data["elements"] = data["elements"] + res.json()["elements"]
            data["paging"] = res.json()["paging"]
        return data["elements"]

    def get_post_comments(self, post_urn, comment_count=100):
        """
        get_post_comments: Get post comments

        :param post_urn: Post URN
        :type post_urn: str
        :param comment_count: Number of comments to fetch
        :type comment_count: int, optional
        :return: List of post comments
        :rtype: list
        """
        url_params = {
            "count": min(comment_count, self._MAX_POST_COUNT),
            "start": 0,
            "q": "comments",
            "sortOrder": "RELEVANCE",
        }
        url = f"/feed/comments"
        url_params["updateId"] = "activity:" + post_urn
        res = self._fetch(url, params=url_params)
        data = res.json()
        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["status"]))
            return {}
        while data and data["metadata"]["paginationToken"] != "":
            if len(data["elements"]) >= comment_count:
                break
            pagination_token = data["metadata"]["paginationToken"]
            url_params["start"] = url_params["start"] + self._MAX_POST_COUNT
            url_params["count"] = self._MAX_POST_COUNT
            url_params["paginationToken"] = pagination_token
            res = self._fetch(url, params=url_params)
            if res.json() and "status" in res.json() and res.json()["status"] != 200:
                self.logger.info("request failed: {}".format(data["status"]))
                return {}
            data["metadata"] = res.json()["metadata"]
            """ When the number of comments exceed total available 
            comments, the api starts returning an empty list of elements"""
            if res.json()["elements"] and len(res.json()["elements"]) == 0:
                break
            if data["elements"] and len(res.json()["elements"]) == 0:
                break
            data["elements"] = data["elements"] + res.json()["elements"]
            data["paging"] = res.json()["paging"]
        return data["elements"]

    def search(self, params, limit=-1, offset=0):
        """Perform a LinkedIn search.

        :param params: Search parameters (see code)
        :type params: dict
        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional


        :return: List of search results
        :rtype: list
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

            keywords = (
                f"keywords:{default_params['keywords']},"
                if "keywords" in default_params
                else ""
            )

            res = self._fetch(
                f"/graphql?variables=(start:{default_params['start']},origin:{default_params['origin']},"
                f"query:("
                f"{keywords}"
                f"flagshipSearchIntent:SEARCH_SRP,"
                f"queryParameters:{default_params['filters']},"
                f"includeFiltersInResponse:false))&=&queryId=voyagerSearchDashClusters"
                f".b0928897b71bd00a5a7291755dcd64f0"
            )
            data = res.json()

            data_clusters = data.get("data", []).get("searchDashClustersByAll", [])

            if not data_clusters:
                return []

            if (
                not data_clusters.get("_type", [])
                == "com.linkedin.restli.common.CollectionResponse"
            ):
                return []

            new_elements = []
            for it in data_clusters.get("elements", []):
                if (
                    not it.get("_type", [])
                    == "com.linkedin.voyager.dash.search.SearchClusterViewModel"
                ):
                    continue

                for el in it.get("items", []):
                    if (
                        not el.get("_type", [])
                        == "com.linkedin.voyager.dash.search.SearchItem"
                    ):
                        continue

                    e = el.get("item", []).get("entityResult", [])
                    if not e:
                        continue
                    if (
                        not e.get("_type", [])
                        == "com.linkedin.voyager.dash.search.EntityResultViewModel"
                    ):
                        continue
                    new_elements.append(e)

            results.extend(new_elements)

            # break the loop if we're done searching
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            if (
                (-1 < limit <= len(results))  # if our results exceed set limit
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(new_elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results

    def search_people(
        self,
        keywords=None,
        connection_of=None,
        network_depths=None,
        current_company=None,
        past_companies=None,
        nonprofit_interests=None,
        profile_languages=None,
        regions=None,
        industries=None,
        schools=None,
        contact_interests=None,
        service_categories=None,
        include_private_profiles=False,  # profiles without a public id, "Linkedin Member"
        # Keywords filter
        keyword_first_name=None,
        keyword_last_name=None,
        # `keyword_title` and `title` are the same. We kept `title` for backward compatibility. Please only use one of them.
        keyword_title=None,
        keyword_company=None,
        keyword_school=None,
        network_depth=None,  # DEPRECATED - use network_depths
        title=None,  # DEPRECATED - use keyword_title
        **kwargs,
    ):
        """Perform a LinkedIn search for people.

        :param keywords: Keywords to search on
        :type keywords: str, optional
        :param current_company: A list of company URN IDs (str)
        :type current_company: list, optional
        :param past_companies: A list of company URN IDs (str)
        :type past_companies: list, optional
        :param regions: A list of geo URN IDs (str)
        :type regions: list, optional
        :param industries: A list of industry URN IDs (str)
        :type industries: list, optional
        :param schools: A list of school URN IDs (str)
        :type schools: list, optional
        :param profile_languages: A list of 2-letter language codes (str)
        :type profile_languages: list, optional
        :param contact_interests: A list containing one or both of "proBono" and "boardMember"
        :type contact_interests: list, optional
        :param service_categories: A list of service category URN IDs (str)
        :type service_categories: list, optional
        :param network_depth: Deprecated, use `network_depths`. One of "F", "S" and "O" (first, second and third+ respectively)
        :type network_depth: str, optional
        :param network_depths: A list containing one or many of "F", "S" and "O" (first, second and third+ respectively)
        :type network_depths: list, optional
        :param include_private_profiles: Include private profiles in search results. If False, only public profiles are included. Defaults to False
        :type include_private_profiles: boolean, optional
        :param keyword_first_name: First name
        :type keyword_first_name: str, optional
        :param keyword_last_name: Last name
        :type keyword_last_name: str, optional
        :param keyword_title: Job title
        :type keyword_title: str, optional
        :param keyword_company: Company name
        :type keyword_company: str, optional
        :param keyword_school: School name
        :type keyword_school: str, optional
        :param connection_of: Connection of LinkedIn user, given by profile URN ID
        :type connection_of: str, optional

        :return: List of profiles (minimal data only)
        :rtype: list
        """
        filters = ["(key:resultType,value:List(PEOPLE))"]
        if connection_of:
            filters.append(f"(key:connectionOf,value:List({connection_of}))")
        if network_depths:
            stringify = " | ".join(network_depths)
            filters.append(f"(key:network,value:List({stringify}))")
        elif network_depth:
            filters.append(f"(key:network,value:List({network_depth}))")
        if regions:
            stringify = " | ".join(regions)
            filters.append(f"(key:geoUrn,value:List({stringify}))")
        if industries:
            stringify = " | ".join(industries)
            filters.append(f"(key:industry,value:List({stringify}))")
        if current_company:
            stringify = " | ".join(current_company)
            filters.append(f"(key:currentCompany,value:List({stringify}))")
        if past_companies:
            stringify = " | ".join(past_companies)
            filters.append(f"(key:pastCompany,value:List({stringify}))")
        if profile_languages:
            stringify = " | ".join(profile_languages)
            filters.append(f"(key:profileLanguage,value:List({stringify}))")
        if nonprofit_interests:
            stringify = " | ".join(nonprofit_interests)
            filters.append(f"(key:nonprofitInterest,value:List({stringify}))")
        if schools:
            stringify = " | ".join(schools)
            filters.append(f"(key:schools,value:List({stringify}))")
        if service_categories:
            stringify = " | ".join(service_categories)
            filters.append(f"(key:serviceCategory,value:List({stringify}))")
        # `Keywords` filter
        keyword_title = keyword_title if keyword_title else title
        if keyword_first_name:
            filters.append(f"(key:firstName,value:List({keyword_first_name}))")
        if keyword_last_name:
            filters.append(f"(key:lastName,value:List({keyword_last_name}))")
        if keyword_title:
            filters.append(f"(key:title,value:List({keyword_title}))")
        if keyword_company:
            filters.append(f"(key:company,value:List({keyword_company}))")
        if keyword_school:
            filters.append(f"(key:school,value:List({keyword_school}))")

        params = {"filters": "List({})".format(",".join(filters))}

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, **kwargs)

        results = []
        for item in data:
            if (
                not include_private_profiles
                and (item.get("entityCustomTrackingInfo") or {}).get(
                    "memberDistance", None
                )
                == "OUT_OF_NETWORK"
            ):
                continue
            results.append(
                {
                    "urn_id": get_id_from_urn(
                        get_urn_from_raw_update(item.get("entityUrn", None))
                    ),
                    "distance": (item.get("entityCustomTrackingInfo") or {}).get(
                        "memberDistance", None
                    ),
                    "jobtitle": (item.get("primarySubtitle") or {}).get("text", None),
                    "location": (item.get("secondarySubtitle") or {}).get("text", None),
                    "name": (item.get("title") or {}).get("text", None),
                }
            )

        return results

    def search_companies(self, keywords=None, **kwargs):
        """Perform a LinkedIn search for companies.

        :param keywords: A list of search keywords (str)
        :type keywords: list, optional

        :return: List of companies
        :rtype: list
        """
        filters = ["(key:resultType,value:List(COMPANIES))"]

        params = {
            "filters": "List({})".format(",".join(filters)),
            "queryContext": "List(spellCorrectionEnabled->true)",
        }

        if keywords:
            params["keywords"] = keywords

        data = self.search(params, **kwargs)

        results = []
        for item in data:
            if "company" not in item.get("trackingUrn"):
                continue
            results.append(
                {
                    "urn_id": get_id_from_urn(item.get("trackingUrn", None)),
                    "name": (item.get("title") or {}).get("text", None),
                    "headline": (item.get("primarySubtitle") or {}).get("text", None),
                    "subline": (item.get("secondarySubtitle") or {}).get("text", None),
                }
            )

        return results

    def search_jobs(
        self,
        keywords=None,
        companies=None,
        experience=None,
        job_type=None,
        job_title=None,
        industries=None,
        location_name=None,
        remote=None,
        listed_at=24 * 60 * 60,
        distance=None,
        limit=-1,
        offset=0,
        **kwargs,
    ):
        """Perform a LinkedIn search for jobs.

        :param keywords: Search keywords (str)
        :type keywords: str, optional
        :param companies: A list of company URN IDs (str)
        :type companies: list, optional
        :param experience: A list of experience levels, one or many of "1", "2", "3", "4", "5" and "6" (internship, entry level, associate, mid-senior level, director and executive, respectively)
        :type experience: list, optional
        :param job_type:  A list of job types , one or many of "F", "C", "P", "T", "I", "V", "O" (full-time, contract, part-time, temporary, internship, volunteer and "other", respectively)
        :type job_type: list, optional
        :param job_title: A list of title URN IDs (str)
        :type job_title: list, optional
        :param industries: A list of industry URN IDs (str)
        :type industries: list, optional
        :param location_name: Name of the location to search within. Example: "Kyiv City, Ukraine"
        :type location_name: str, optional
        :param remote: Filter for remote jobs, onsite or hybrid. onsite:"1", remote:"2", hybrid:"3"
        :type remote: list, optional
        :param listed_at: maximum number of seconds passed since job posting. 86400 will filter job postings posted in last 24 hours.
        :type listed_at: int/str, optional. Default value is equal to 24 hours.
        :param distance: maximum distance from location in miles
        :type distance: int/str, optional. If not specified, None or 0, the default value of 25 miles applied.
        :param limit: maximum number of results obtained from API queries. -1 means maximum which is defined by constants and is equal to 1000 now.
        :type limit: int, optional, default -1
        :param offset: indicates how many search results shall be skipped
        :type offset: int, optional
        :return: List of jobs
        :rtype: list
        """
        count = Linkedin._MAX_SEARCH_COUNT
        if limit is None:
            limit = -1

        query = {"origin":"JOB_SEARCH_PAGE_QUERY_EXPANSION"}
        if keywords:
            query["keywords"] = "KEYWORD_PLACEHOLDER"
        if location_name:
            query["locationFallback"] = "LOCATION_PLACEHOLDER"

        # In selectedFilters()
        query['selectedFilters'] = {}
        if companies:
            query['selectedFilters']['company'] = f"List({','.join(companies)})"
        if experience:
            query['selectedFilters']['experience'] = f"List({','.join(experience)})"
        if job_type:
            query['selectedFilters']['jobType'] = f"List({','.join(job_type)})"
        if job_title:
            query['selectedFilters']['title'] = f"List({','.join(job_title)})"
        if industries:
            query['selectedFilters']['industry'] = f"List({','.join(industries)})"
        if distance:
            query['selectedFilters']['distance'] = f"List({distance})"
        if remote:
            query['selectedFilters']['workplaceType'] = f"List({','.join(remote)})"

        query['selectedFilters']['timePostedRange'] = f"List(r{listed_at})"
        query["spellCorrectionEnabled"] = "true"

        # Query structure:
        # "(
        #    origin:JOB_SEARCH_PAGE_QUERY_EXPANSION,
        #    keywords:marketing%20manager,
        #    locationFallback:germany,
        #    selectedFilters:(
        #        distance:List(25),
        #        company:List(163253),
        #        salaryBucketV2:List(5),
        #        timePostedRange:List(r2592000),
        #        workplaceType:List(1)
        #    ),
        #    spellCorrectionEnabled:true
        #  )"

        query = str(query).replace(" ","") \
                    .replace("'","") \
                    .replace("KEYWORD_PLACEHOLDER", keywords or "") \
                    .replace("LOCATION_PLACEHOLDER", location_name or "") \
                    .replace("{","(") \
                    .replace("}",")")
        results = []
        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(results) < count:
                count = limit - len(results)
            default_params = {
                "decorationId": "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-174",
                "count": count,
                "q": "jobSearch",
                "query": query,
                "start": len(results) + offset,
            }

            res = self._fetch(
                f"/voyagerJobsDashJobCards?{urlencode(default_params, safe='(),:')}",
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            data = res.json()

            elements = data.get("included", [])
            new_data = [
                i
                for i in elements
                if i["$type"] == 'com.linkedin.voyager.dash.jobs.JobPosting'
            ]
            # break the loop if we're done searching or no results returned
            if not new_data:
                break
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            results.extend(new_data)
            if (
                (-1 < limit <= len(results))  # if our results exceed set limit
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results

    def get_profile_contact_info(self, public_id=None, urn_id=None):
        """Fetch contact information for a given LinkedIn profile. Pass a [public_id] or a [urn_id].

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: Contact data
        :rtype: dict
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
        """Fetch the skills listed on a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional


        :return: List of skill objects
        :rtype: list
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

    def get_profile(self, public_id=None, urn_id=None):
        """Fetch data for a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: Profile data
        :rtype: dict
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

                images_data = profile["miniProfile"]["picture"][
                    "com.linkedin.common.VectorImage"
                ]["artifacts"]
                for img in images_data:
                    w, h, url_segment = itemgetter(
                        "width", "height", "fileIdentifyingUrlPathSegment"
                    )(img)
                    profile[f"img_{w}_{h}"] = url_segment

            profile["profile_id"] = get_id_from_urn(profile["miniProfile"]["entityUrn"])
            profile["profile_urn"] = profile["miniProfile"]["entityUrn"]
            profile["member_urn"] = profile["miniProfile"]["objectUrn"]
            profile["public_id"] = profile["miniProfile"]["publicIdentifier"]

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

        # massage [projects] data
        projects = data["projectView"]["elements"]
        for item in projects:
            del item["entityUrn"]
        profile["projects"] = projects

        return profile

    def get_profile_connections(self, urn_id):
        """Fetch first-degree connections for a given LinkedIn profile.

        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str

        :return: List of search results
        :rtype: list
        """
        return self.search_people(connection_of=urn_id, network_depth="F")

    def get_company_updates(
        self, public_id=None, urn_id=None, max_results=None, results=None
    ):
        """Fetch company updates (news activity) for a given LinkedIn company.

        :param public_id: LinkedIn public ID for a company
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a company
        :type urn_id: str, optional

        :return: List of company update objects
        :rtype: list
        """

        if results is None:
            results = []

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
            public_id=public_id,
            urn_id=urn_id,
            results=results,
            max_results=max_results,
        )

    def get_profile_updates(
        self, public_id=None, urn_id=None, max_results=None, results=None
    ):
        """Fetch profile updates (newsfeed activity) for a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :type public_id: str, optional
        :param urn_id: LinkedIn URN ID for a profile
        :type urn_id: str, optional

        :return: List of profile update objects
        :rtype: list
        """

        if results is None:
            results = []

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
            public_id=public_id,
            urn_id=urn_id,
            results=results,
            max_results=max_results,
        )

    def get_current_profile_views(self):
        """Get profile view statistics, including chart data.

        :return: Profile view data
        :rtype: dict
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
        """Fetch data about a given LinkedIn school.

        :param public_id: LinkedIn public ID for a school
        :type public_id: str

        :return: School data
        :rtype: dict
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
        """Fetch data about a given LinkedIn company.

        :param public_id: LinkedIn public ID for a company
        :type public_id: str

        :return: Company data
        :rtype: dict
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
        """Fetch conversation (message thread) details for a given LinkedIn profile.

        :param profile_urn_id: LinkedIn URN ID for a profile
        :type profile_urn_id: str

        :return: Conversation data
        :rtype: dict
        """
        # passing `params` doesn't work properly, think it's to do with List().
        # Might be a bug in `requests`?
        res = self._fetch(
            f"/messaging/conversations?\
            keyVersion=LEGACY_INBOX&q=participants&recipients=List({profile_urn_id})"
        )

        data = res.json()

        if data["elements"] == []:
            return {}

        item = data["elements"][0]
        item["id"] = get_id_from_urn(item["entityUrn"])

        return item

    def get_conversations(self):
        """Fetch list of conversations the user is in.

        :return: List of conversations
        :rtype: list
        """
        params = {"keyVersion": "LEGACY_INBOX"}

        res = self._fetch(f"/messaging/conversations", params=params)

        return res.json()

    def get_conversation(self, conversation_urn_id):
        """Fetch data about a given conversation.

        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str

        :return: Conversation data
        :rtype: dict
        """
        res = self._fetch(f"/messaging/conversations/{conversation_urn_id}/events")

        return res.json()

    def send_message(self, message_body, conversation_urn_id=None, recipients=None):
        """Send a message to a given conversation.

        :param message_body: Message text to send
        :type message_body: str
        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str, optional
        :param recipients: List of profile urn id's
        :type recipients: list, optional

        :return: Error state. If True, an error occured.
        :rtype: boolean
        """
        params = {"action": "create"}

        if not (conversation_urn_id or recipients):
            self.logger.debug("Must provide [conversation_urn_id] or [recipients].")
            return True

        message_event = {
            "eventCreate": {
                "originToken": str(uuid.uuid4()),
                "value": {
                    "com.linkedin.voyager.messaging.create.MessageCreate": {
                        "attributedBody": {
                            "text": message_body,
                            "attributes": [],
                        },
                        "attachments": [],
                    }
                },
                "trackingId": generate_trackingId_as_charString(),
            },
            "dedupeByClientGeneratedToken": False,
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
                f"/messaging/conversations",
                params=params,
                data=json.dumps(payload),
            )

        return res.status_code != 201

    def mark_conversation_as_seen(self, conversation_urn_id):
        """Send 'seen' to a given conversation.

        :param conversation_urn_id: LinkedIn URN ID for a conversation
        :type conversation_urn_id: str

        :return: Error state. If True, an error occured.
        :rtype: boolean
        """
        payload = json.dumps({"patch": {"$set": {"read": True}}})

        res = self._post(
            f"/messaging/conversations/{conversation_urn_id}", data=payload
        )

        return res.status_code != 200

    def get_user_profile(self, use_cache=True):
        """Get the current user profile. If not cached, a network request will be fired.

        :return: Profile data for currently logged in user
        :rtype: dict
        """
        me_profile = self.client.metadata.get("me")
        if not self.client.metadata.get("me") or not use_cache:
            res = self._fetch(f"/me")
            me_profile = res.json()
            # cache profile
            self.client.metadata["me"] = me_profile

        return me_profile

    def get_invitations(self, start=0, limit=3):
        """Fetch connection invitations for the currently logged in user.

        :param start: How much to offset results by
        :type start: int
        :param limit: Maximum amount of invitations to return
        :type limit: int

        :return: List of invitation objects
        :rtype: list
        """
        params = {
            "start": start,
            "count": limit,
            "includeInsights": True,
            "q": "receivedInvitation",
        }

        res = self._fetch(
            "/relationships/invitationViews",
            params=params,
        )

        if res.status_code != 200:
            return []

        response_payload = res.json()
        return [element["invitation"] for element in response_payload["elements"]]

    def reply_invitation(
        self, invitation_entity_urn, invitation_shared_secret, action="accept"
    ):
        """Respond to a connection invitation. By default, accept the invitation.

        :param invitation_entity_urn: URN ID of the invitation
        :type invitation_entity_urn: int
        :param invitation_shared_secret: Shared secret of invitation
        :type invitation_shared_secret: str
        :param action: "accept" or "reject". Defaults to "accept"
        :type action: str, optional

        :return: Success state. True if successful
        :rtype: boolean
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

    def add_connection(self, profile_public_id, message="", profile_urn=None):
        """Add a given profile id as a connection.

        :param profile_public_id: public ID of a LinkedIn profile
        :type profile_public_id: str
        :param message: message to send along with connection request
        :type profile_urn: str, optional
        :param profile_urn: member URN for the given LinkedIn profile
        :type profile_urn: str, optional

        :return: Error state. True if error occurred
        :rtype: boolean
        """

        # Validating message length (max size is 300 characters)
        if len(message) > 300:
            self.logger.info("Message too long. Max size is 300 characters")
            return False

        if not profile_urn:
            profile_urn_string = self.get_profile(public_id=profile_public_id)[
                "profile_urn"
            ]
            # Returns string of the form 'urn:li:fs_miniProfile:ACoAACX1hoMBvWqTY21JGe0z91mnmjmLy9Wen4w'
            # We extract the last part of the string
            profile_urn = profile_urn_string.split(":")[-1]

        trackingId = generate_trackingId()
        payload = {
            "trackingId": trackingId,
            "message": message,
            "invitations": [],
            "excludeInvitations": [],
            "invitee": {
                "com.linkedin.voyager.growth.invitation.InviteeProfile": {
                    "profileId": profile_urn
                }
            },
        }
        res = self._post(
            "/growth/normInvitations",
            data=json.dumps(payload),
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )

        return res.status_code != 201

    def remove_connection(self, public_profile_id):
        """Remove a given profile as a connection.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Error state. True if error occurred
        :rtype: boolean
        """
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
            headers={
                "accept": "*/*",
                "content-type": "text/plain;charset=UTF-8",
            },
            data=json.dumps(payload),
        )

        return res.status_code != 200

    def view_profile(
        self,
        target_profile_public_id,
        target_profile_member_urn_id=None,
        network_distance=None,
    ):
        """View a profile, notifying the user that you "viewed" their profile.

        Provide [target_profile_member_urn_id] and [network_distance] to save 2 network requests and
        speed up the execution of this function.

        :param target_profile_public_id: public ID of a LinkedIn profile
        :type target_profile_public_id: str
        :param network_distance: How many degrees of separation exist e.g. 2
        :type network_distance: int, optional
        :param target_profile_member_urn_id: member URN id for target profile
        :type target_profile_member_urn_id: str, optional

        :return: Error state. True if error occurred
        :rtype: boolean
        """
        me_profile = self.get_user_profile()

        if not target_profile_member_urn_id:
            profile = self.get_profile(public_id=target_profile_public_id)
            target_profile_member_urn_id = int(get_id_from_urn(profile["member_urn"]))

        if not network_distance:
            profile_network_info = self.get_profile_network_info(
                public_profile_id=target_profile_public_id
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
            "vieweeMemberUrn": f"urn:li:member:{target_profile_member_urn_id}",
            "profileTrackingId": self.client.metadata["clientPageInstanceId"],
            "entityView": {
                "viewType": "profile-view",
                "viewerId": me_member_id,
                "targetId": target_profile_member_urn_id,
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
                "path": f"/in/{target_profile_member_urn_id}/",
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
        """Fetch privacy settings for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Privacy settings data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/privacySettings",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_member_badges(self, public_profile_id):
        """Fetch badges for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Badges data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/memberBadges",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def get_profile_network_info(self, public_profile_id):
        """Fetch network information for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile
        :type public_profile_id: str

        :return: Network data
        :rtype: dict
        """
        res = self._fetch(
            f"/identity/profiles/{public_profile_id}/networkinfo",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        if res.status_code != 200:
            return {}

        data = res.json()
        return data.get("data", {})

    def unfollow_entity(self, urn_id):
        """Unfollow a given entity.

        :param urn_id: URN ID of entity to unfollow
        :type urn_id: str

        :return: Error state. Returns True if error occurred
        :rtype: boolean
        """
        payload = {"urn": f"urn:li:fs_followingInfo:{urn_id}"}
        res = self._post(
            "/feed/follows?action=unfollowByEntityUrn",
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            data=json.dumps(payload),
        )

        err = False
        if res.status_code != 200:
            err = True

        return err

    def _get_list_feed_posts_and_list_feed_urns(
        self, limit=-1, offset=0, exclude_promoted_posts=True
    ):
        """Get a list of URNs from feed sorted by 'Recent' and a list of yet
        unsorted posts, each one of them containing a dict per post.

        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional
        :param exclude_promoted_posts: Exclude from the output promoted posts
        :type exclude_promoted_posts: bool, optional

        :return: List of posts and list of URNs
        :rtype: (list, list)
        """
        _PROMOTED_STRING = "Promoted"
        _PROFILE_URL = f"{self.client.LINKEDIN_BASE_URL}/in/"

        l_posts = []
        l_urns = []

        # If count>100 API will return HTTP 400
        count = Linkedin._MAX_UPDATE_COUNT
        if limit == -1:
            limit = Linkedin._MAX_UPDATE_COUNT

        # 'l_urns' equivalent to other functions 'results' variable
        l_urns = []

        while True:
            # when we're close to the limit, only fetch what we need to
            if limit > -1 and limit - len(l_urns) < count:
                count = limit - len(l_urns)
            params = {
                "count": str(count),
                "q": "chronFeed",
                "start": len(l_urns) + offset,
            }
            res = self._fetch(
                f"/feed/updatesV2",
                params=params,
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            """
            Response includes two keya:
            - ['Data']['*elements']. It includes the posts URNs always
            properly sorted as 'Recent', including yet sponsored posts. The
            downside is that fetching one by one the posts is slower. We will
            save the URNs to later on build a sorted list of posts purging
            promotions
            - ['included']. List with all the posts attributes, but not sorted as
            'Recent' and including promoted posts
            """
            l_raw_posts = res.json().get("included", {})
            l_raw_urns = res.json().get("data", {}).get("*elements", [])

            l_new_posts = parse_list_raw_posts(
                l_raw_posts, self.client.LINKEDIN_BASE_URL
            )
            l_posts.extend(l_new_posts)

            l_urns.extend(parse_list_raw_urns(l_raw_urns))

            # break the loop if we're done searching
            # NOTE: we could also check for the `total` returned in the response.
            # This is in data["data"]["paging"]["total"]
            if (
                (limit > -1 and len(l_urns) >= limit)  # if our results exceed set limit
                or len(l_urns) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(l_raw_urns) == 0:
                break

            self.logger.debug(f"results grew to {len(l_urns)}")

        return l_posts, l_urns

    def get_feed_posts(self, limit=-1, offset=0, exclude_promoted_posts=True):
        """Get a list of URNs from feed sorted by 'Recent'

        :param limit: Maximum length of the returned list, defaults to -1 (no limit)
        :type limit: int, optional
        :param offset: Index to start searching from
        :type offset: int, optional
        :param exclude_promoted_posts: Exclude from the output promoted posts
        :type exclude_promoted_posts: bool, optional

        :return: List of URNs
        :rtype: list
        """
        l_posts, l_urns = self._get_list_feed_posts_and_list_feed_urns(
            limit, offset, exclude_promoted_posts
        )
        return get_list_posts_sorted_without_promoted(l_urns, l_posts)

    def get_job(self, job_id):
        """Fetch data about a given job.
        :param job_id: LinkedIn job ID
        :type job_id: str

        :return: Job data
        :rtype: dict
        """
        params = {
            "decorationId": "com.linkedin.voyager.deco.jobs.web.shared.WebLightJobPosting-23",
        }

        res = self._fetch(f"/jobs/jobPostings/{job_id}", params=params)

        data = res.json()

        if data and "status" in data and data["status"] != 200:
            self.logger.info("request failed: {}".format(data["message"]))
            return {}

        return data
