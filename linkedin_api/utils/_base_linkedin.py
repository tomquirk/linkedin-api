from abc import ABC, abstractmethod
from httpx import Cookies
from linkedin_api.client import Client
from operator import itemgetter
from linkedin_api.utils.helpers import (
    get_id_from_urn,
    get_urn_from_raw_update,
)
from linkedin_api.utils.api_builder import ApiBuilder
from linkedin_api.utils import query_options
from linkedin_api.utils.schemas import (
    LinkedInProfile,
    LinkedInPrivacySettings,
    LinkedInMemberBadges,
    LinkedInNetwork,
    LinkedInOrganizationResponse,
    LinkedInContactInfo,
    LinkedInSearchPeopleResponse,
    LinkedInProfilePostsResponse,
    LinkedInProfileSkillsResponse,
    LinkedInPostCommentResponse,
    LinkedInSearchCompaniesResponse,
    LinkedInUpdatesResponse,
    LinkedInSelfProfile,
    LinkedInJobSearchResponse,
    LinkedInJob,
    LinkedInJobSkills,
)

import logging

class BaseLinkedIn(ABC):
    _MAX_POST_COUNT = 100  # max seems to be 100 posts per page
    _MAX_UPDATE_COUNT = 100  # max seems to be 100
    _MAX_SEARCH_COUNT = 49  # max seems to be 49, and min seems to be 2
    _MAX_REPEATED_REQUESTS = (
        200  # VERY conservative max requests count to avoid rate-limit
    )

    logger = logging.getLogger(__name__)
    _api_builder = ApiBuilder()

    def __init__(
        self,
        client: Client,
    ):
        """Constructor method"""
        self.client = client
        self._metadata: dict[str, LinkedInSelfProfile] = {}

    def _cookies(self):
        """Return client cookies"""
        return self.client.cookies

    def _headers(self):
        """Return client cookies"""
        return self.client.REQUEST_HEADERS

    def _normalize_person_data(self, data: dict) -> dict:
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

            profile["urn_id"] = get_id_from_urn(profile["miniProfile"]["entityUrn"])
            profile["profile_urn"] = profile["miniProfile"]["entityUrn"]
            profile["member_urn"] = profile["miniProfile"]["objectUrn"]
            profile["public_id"] = profile["miniProfile"]["publicIdentifier"]

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
        profile["languages"] = data["languageView"]["elements"]

        # massage [publications] data
        profile["publications"] = data["publicationView"]["elements"]

        # massage [certifications] data
        profile["certifications"] = data["certificationView"]["elements"]

        # massage [volunteer] data
        profile["volunteer"] = data["volunteerExperienceView"]["elements"]

        # massage [honors] data
        profile["honors"] = data["honorView"]["elements"]

        # massage [projects] data
        profile["projects"] = data["projectView"]["elements"]

        # massage [skills] data
        profile["skills"] = data["skillView"]["elements"]

        return profile

    def _parse_search_data(self, data: dict) -> dict:
        data_clusters: dict = data.get("data", {}).get("searchDashClustersByAll", {})

        if not data_clusters:
            return {}

        if (
            data_clusters.get("_type", "")
            != "com.linkedin.restli.common.CollectionResponse"
        ):
            return {}

        new_elements = []
        for it in data_clusters.get("elements", []):
            if (
                it.get("_type", "")
                != "com.linkedin.voyager.dash.search.SearchClusterViewModel"
            ):
                continue

            for el in it.get("items", []):
                if el.get("_type", "") != "com.linkedin.voyager.dash.search.SearchItem":
                    continue

                e = el.get("item", {}).get("entityResult", [])
                if not e:
                    continue
                if (
                    e.get("_type", "")
                    != "com.linkedin.voyager.dash.search.EntityResultViewModel"
                ):
                    continue
                new_elements.append(e)
        result = {"paging": data_clusters["paging"], "elements": new_elements}
        return result

    def _normalize_search_people_data(
        self, data: dict, include_private_profiles: bool
    ) -> list[dict]:
        results = []
        for item in data.get("elements", []):
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
                    "job_title": (item.get("primarySubtitle") or {}).get("text", None),
                    "location": (item.get("secondarySubtitle") or {}).get("text", None),
                    "name": (item.get("title") or {}).get("text", None),
                }
            )
        return results

    def _normalize_search_jobs_data(self, data: dict, v2: bool) -> dict:
        results = []
        if v2:
            elements = data.get("included", [])
            for element in elements:
                if element["$type"] == "com.linkedin.voyager.dash.jobs.JobPosting":
                    results.append(element)
        else:
            elements = data.get("elements", [])
            for element in elements:
                job_data = (
                    element.get("jobCardUnion", {})
                    .get("jobPostingCard", {})
                    .get("jobPosting", {})
                )
                if job_data:
                    results.append(job_data)

        if v2:
            paging = data["data"]["paging"]
        else:
            paging = data.get("paging", {})

        return {"paging": paging, "elements": results}

    def _normalize_search_company_data(self, data: dict) -> list[dict]:
        results = []
        for item in data.get("elements", []):
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

    def _normalize_contact_info(self, data: dict) -> dict:
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

    @abstractmethod
    def _fetch(self, uri: str, base_request=False, **kwargs): ...

    @abstractmethod
    def _post(self, uri: str, base_request=False, **kwargs): ...

    @abstractmethod
    def authenticate(
        self, username: str, password: str, cookies: Cookies | None = None
    ): ...

    @abstractmethod
    def get_profile_posts(
        self, urn_id: str, post_count=10, start=0, pagination_token=""
    ) -> LinkedInProfilePostsResponse | None:
        """
        :param urn_id: LinkedIn URN ID for a profile
        :param post_count: Number of posts to fetch
        :param start: Pagination start for the posts to fetch
        :param pagination_token: Pagination token if more than 100 posts

        :return: LinkedInProfilePostsResponse | None
        """

    @abstractmethod
    def get_post_comments(
        self,
        social_detail_urn: str,
        sort_by: query_options.SortOrder = query_options.SortOrder.RELEVANCE,
        comment_count=100,
        start=0,
        pagination_token="",
    ) -> LinkedInPostCommentResponse | None:
        """
        get_post_comments: Get post comments

        :param social_detail_urn: Post URN
        :param sort_by: sort param for the fetch request
        :param comment_count: Number of comments to fetch
        :param start: offset for pagination on fetch
        :param pagination_token: Pagination token if more than 100 posts

        :return: LinkedInPostCommentResponse | None
        """

    @abstractmethod
    def search(self, params: dict, offset=0) -> dict:
        """
        Perform a LinkedIn search. This function should never
        be used unless you know what you are doing since the JSONs are too nested

        :param params: Search parameters (see other search methods for an idea of what to pass)
        :param offset: Index to start searching from

        :return: dictionary
        """

    @abstractmethod
    def search_people(
        self,
        keywords: str = "",
        connection_of: str = "",
        network_depths: list[query_options.NetworkDepth] = [],
        current_company: list[query_options.CompanyID] = [],
        past_companies: list[query_options.CompanyID] = [],
        nonprofit_interests: list[str] = [],
        profile_languages: list[str] = [],
        regions: list[query_options.GeoID] = [],
        industries: list[str] = [],
        schools: list[str] = [],
        service_categories: list[str] = [],
        include_private_profiles=False,  # profiles without a public id, "Linkedin Member"
        keyword_first_name: str = "",
        keyword_last_name: str = "",
        keyword_title: str = "",
        keyword_company: str = "",
        keyword_school: str = "",
        offset: int = 0,
    ) -> LinkedInSearchPeopleResponse:
        """Perform a LinkedIn search for people.

        :param keywords: Keywords to search on
        :param connection_of: Connection of LinkedIn user, given by profile URN ID
        :param network_depths: A list containing one or many of "F", "S" and "O" (first, second and third+ respectively)
        :param current_company: A list of company URN IDs
        :param past_companies: A list of company URN IDs
        :param nonprofit_interests: A list of non-profit URN ID (?)
        :param profile_languages: A list of 2-letter language codes
        :param regions: A list of geo URN IDs
        :param industries: A list of industry URN IDs
        :param schools: A list of school URN IDs
        :param service_categories: A list of service category URN IDs
        :param include_private_profiles: Include private profiles in search results. If False, only public profiles are included
        :param keyword_first_name: First name
        :param keyword_last_name: Last name
        :param keyword_title: Job title
        :param keyword_company: Company name
        :param keyword_school: School name
        :param offset: pagination index of search

        :return: LinkedInSearchPeopleResponse
        """

    @abstractmethod
    def search_companies(
        self, keywords: str = "", offset: int = 0
    ) -> LinkedInSearchCompaniesResponse:
        """
        Perform a LinkedIn search for companies.

        :param keywords: key words to look up, optional
        :param offset: offset for pagination in search

        :return: LinkedInSearchCompaniesResponse
        """

    @abstractmethod
    def search_jobs(
        self,
        keywords: str = "",
        companies: list[query_options.CompanyID] = [],
        experience: list[query_options.Experience] = [],
        job_type: list[query_options.JobType] = [],
        job_title: list[query_options.JobTitle] = [],
        industries: list[str] = [],
        location: query_options.GeoID | None = None,
        remote: list[query_options.LocationType] = [],
        listed_at=24 * 60 * 60,
        distance: int | None = None,
        sort_by: query_options.SortBy = query_options.SortBy.RELEVANCE,
        v2: bool = False,
        limit=10,
        offset=0,
    ) -> LinkedInJobSearchResponse | None:
        """
        Perform a LinkedIn search for jobs.

        :param keywords: Search keywords
        :param companies: A list of company URN IDs
        :param experience: A list of experience levels, one or many of (internship, entry level, associate, mid-senior level, director and executive, respectively)
        :param job_type:  A list of job types , one or many of (full-time, contract, part-time, temporary, internship, volunteer and "other", respectively)
        :param job_title: A list of title URN IDs
        :param industries: A list of industry URN IDs
        :param location: Name of the location to search within. Example: "Kyiv City, Ukraine"
        :param remote: Filter for remote jobs, onsite or hybrid. onsite:"1", remote:"2", hybrid:"3"
        :param listed_at: maximum number of seconds passed since job posting. 86400 will filter job postings posted in last 24 hours.
        :param distance: maximum distance from location in miles
        :param sort_by: Filter for how to sort jobs, by one of relevancy or time posted
        :param limit: maximum number of results obtained from API queries. -1 means maximum which is defined by constants and is equal to 1000 now.
        :param offset: indicates how many search results shall be skipped

        :return: LinkedInJobSearchResponse | None
        """

    @abstractmethod
    def get_profile_contact_info(
        self, public_id: str = "", urn_id: str = ""
    ) -> LinkedInContactInfo | None:
        """
        Fetch contact information for a given LinkedIn profile. Pass a [public_id] or a [urn_id].

        :param public_id: LinkedIn public ID for a profile
        :param urn_id: LinkedIn URN ID for a profile

        :return: LinkedInContactInfo | None
        """

    @abstractmethod
    def get_profile_skills(
        self, public_id: str = "", urn_id: str = ""
    ) -> LinkedInProfileSkillsResponse | None:
        """
        Fetch the skills listed on a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :param urn_id: LinkedIn URN ID for a profile

        :return:  LinkedInProfileSkillsResponse | None
        """

    @abstractmethod
    def get_profile(
        self, public_id: str = "", urn_id: str = ""
    ) -> LinkedInProfile | None:
        """
        Fetch the skills listed on a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :param urn_id: LinkedIn URN ID for a profile

        :return:LinkedInProfile | None
        """

    @abstractmethod
    def get_profile_connections(
        self, urn_id: str, offset: int = 0
    ) -> LinkedInSearchPeopleResponse:
        """
        Fetch first-degree connections for a given LinkedIn profile.

        :param urn_id: LinkedIn URN ID for a profile
        :param offset: indicates how many search results shall be skipped

        :return: LinkedInSearchPeopleResponse
        """

    @abstractmethod
    def get_company_updates(
        self,
        public_id: str = "",
        urn_id: str = "",
        start: int = 0,
        count: int = _MAX_UPDATE_COUNT,
    ) -> LinkedInUpdatesResponse | None:
        """
        Fetch company updates (news activity) for a given LinkedIn company.

        :param public_id: LinkedIn public ID for a company
        :param urn_id: LinkedIn URN ID for a company
        :param start: offset for query due to pagination
        :param count: number of items to pull from LinkedIn

        :return: LinkedInUpdatesResponse | None
        """

    @abstractmethod
    def get_profile_updates(
        self,
        public_id: str = "",
        urn_id: str = "",
        start: int = 0,
        count: int = _MAX_UPDATE_COUNT,
    ) -> LinkedInUpdatesResponse | None:
        """
        Fetch profile updates (newsfeed activity) for a given LinkedIn profile.

        :param public_id: LinkedIn public ID for a profile
        :param urn_id: LinkedIn URN ID for a profile
        :param start: offset for query due to pagination
        :param count: number of items to pull from LinkedIn

        :return: LinkedInUpdatesResponse | None
        """

    @abstractmethod
    def get_organization(self, public_id: str) -> LinkedInOrganizationResponse | None:
        """
        Fetch data about a given school or Company on LinkedIn.

        :param public_id: LinkedIn public ID for a school
        :return: LinkedInOrganizationResponse | None
        """

    @abstractmethod
    def get_user_profile(self, use_cache=True) -> LinkedInSelfProfile | None:
        """
        Get the current user profile. If not cached, a network request will be fired.

        :return: LinkedInSelfProfile | None
        """

    @abstractmethod
    def get_profile_privacy_settings(
        self, public_profile_id: str
    ) -> LinkedInPrivacySettings | None:
        """
        Fetch privacy settings for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile

        :return: LinkedInPrivacySettings | None
        """

    @abstractmethod
    def get_profile_member_badges(
        self, public_profile_id: str
    ) -> LinkedInMemberBadges | None:
        """
        Fetch badges for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile

        :return: LinkedInMemberBadges | None
        """

    @abstractmethod
    def get_profile_network_info(
        self, public_profile_id: str
    ) -> LinkedInNetwork | None:
        """
        Fetch network information for a given LinkedIn profile.

        :param public_profile_id: public ID of a LinkedIn profile

        :return: LinkedInNetwork | None
        """

    @abstractmethod
    def get_job(self, job_id: str) -> LinkedInJob | None:
        """
        Fetch data about a given job.

        :param job_id: LinkedIn job ID

        :return: LinkedInJob | None
        """

    @abstractmethod
    def get_job_skills(self, job_id: str) -> LinkedInJobSkills | None:
        """
        Fetch skills associated with a given job.

        :param job_id: LinkedIn job ID

        :return: LinkedInJobSkills | None
        """
