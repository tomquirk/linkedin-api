from urllib.parse import urlencode, quote_plus


class ApiBuilder:
    @staticmethod
    def build_feed_url():
        return "/feed/updates"

    @staticmethod
    def get_default_params(count: int = 100, start: int = 0):
        return {"count": count, "start": start}

    @staticmethod
    def build_get_job_skill_url_params(job_id: str):
        url = f"/voyagerAssessmentsDashJobSkillMatchInsight/{quote_plus(f"urn:li:fsd_jobSkillMatchInsight:{job_id}")}"
        return url, {
            "decorationId": "com.linkedin.voyager.dash.deco.assessments.FullJobSkillMatchInsight-17",
        }

    @staticmethod
    def build_get_job_url_params(job_id: str):
        return f"/jobs/jobPostings/{job_id}", {
            "decorationId": "com.linkedin.voyager.deco.jobs.web.shared.WebLightJobPosting-23",
        }

    @staticmethod
    def get_unfollow_entity_payload(urn_id: str):
        return {"urn": f"urn:li:fs_followingInfo:{urn_id}"}

    @staticmethod
    def build_profile_updates_url_params(
        public_id: str, urn_id: str, count: int, start: int
    ):
        return ApiBuilder.build_feed_url(), {
            "profileId": public_id or urn_id,
            "q": "memberShareFeed",
            "moduleKey": "member-share",
            "count": count,
            "start": start,
        }

    @staticmethod
    def build_company_updates_url_params(
        public_id: str, urn_id: str, count: int, start: int
    ):
        return ApiBuilder.build_feed_url(), {
            "companyUniversalName": public_id or urn_id,
            "q": "companyFeedByUniversalName",
            "moduleKey": "member-share",
            "count": count,
            "start": start,
        }

    @staticmethod
    def build_profile_posts_url_params(
        urn_id: str, count: int, start: int, pagination_token: str
    ):
        params = {
            "count": count,
            "start": start,
            "q": "memberShareFeed",
            "moduleKey": "member-shares:phone",
            "includeLongTermHistory": True,
            "profileUrn": f"urn:li:fsd_profile:{urn_id}",
        }
        if pagination_token:
            params["paginationToken"] = pagination_token
        return "/identity/profileUpdatesV2", params

    @staticmethod
    def build_post_comments_url_query(
        post_urn: str, count: int, start: int, sort_order: str, pagination_token: str
    ):
        params = {
            "count": count,
            "start": start,
            "q": "comments",
            "sortOrder": sort_order,
            "updateId": f"activity:{post_urn}",
        }
        if pagination_token:
            params["paginationToken"] = pagination_token
        return "/feed/comments", params

    @staticmethod
    def build_search_url_params_query(params: dict, start: int):
        default_params = {
            "filters": "List()",
            "origin": "GLOBAL_SEARCH_HEADER",
            "q": "all",
            "start": start,
            "queryContext": "List(spellCorrectionEnabled->true,relatedSearchesEnabled->true,kcardTypes->PROFILE|COMPANY)",
            "includeWebMetadata": "true",
        }
        default_params.update(params)

        keywords = (
            f"keywords:{default_params['keywords']},"
            if "keywords" in default_params
            else ""
        )

        url = (
            f"/graphql?variables=(start:{default_params['start']},origin:{default_params['origin']},"
            f"query:("
            f"{keywords}"
            f"flagshipSearchIntent:SEARCH_SRP,"
            f"queryParameters:{default_params['filters']},"
            f"includeFiltersInResponse:false))&queryId=voyagerSearchDashClusters"
            f".b0928897b71bd00a5a7291755dcd64f0"
        )
        return url, default_params

    @staticmethod
    def build_search_companies_params(keywords: str):
        default_params = {
            "filters": "List((key:resultType,value:List(COMPANIES)))",
            "queryContext": "List(spellCorrectionEnabled->true)",
            "keywords": [keywords],
        }

        if not keywords:
            del default_params["keywords"]

        return default_params

    @staticmethod
    def build_search_people_params(**kwargs):
        filters = ["(key:resultType,value:List(PEOPLE))"]
        ops = {
            "connection_of": "(key:connectionOf,value:List({}))",
            "network_depths": "(key:network,value:List({stringify}))",
            "regions": "(key:geoUrn,value:List({stringify}))",
            "industries": "(key:industry,value:List({stringify}))",
            "current_company": "(key:currentCompany,value:List({stringify}))",
            "past_companies": "(key:pastCompany,value:List({stringify}))",
            "profile_languages": "(key:profileLanguage,value:List({stringify}))",
            "nonprofit_interests": "(key:nonprofitInterest,value:List({stringify}))",
            "schools": "(key:schools,value:List({stringify}))",
            "service_categories": "(key:serviceCategory,value:List({stringify}))",
            "keyword_first_name": "(key:firstName,value:List({}))",
            "keyword_last_name": "(key:lastName,value:List({}))",
            "keyword_title": "(key:title,value:List({}))",
            "keyword_company": "(key:company,value:List({}))",
            "keyword_school": "(key:school,value:List({}))",
        }
        for key, value in kwargs.items():
            if "stringify" in ops[key] and value:
                stringify = " | ".join(value)
                filters.append(ops[key].format(stringify=stringify))
            elif value:
                filters.append(ops[key].format(value))

        return {"filters": f"List({",".join(filters)})"}

    @staticmethod
    def build_search_jobs_url_query(count: int, offset: int, **kwargs):
        """
        Query structure:
         "(
            origin:JOB_SEARCH_PAGE_QUERY_EXPANSION,
            keywords:marketing%20manager,
            locationFallback:germany,
            selectedFilters:(
                distance:List(25),
                company:List(163253),
                salaryBucketV2:List(5),
                timePostedRange:List(r2592000),
                workplaceType:List(1)
            ),
            spellCorrectionEnabled:true
        #  )"
        """
        query = {
            "origin": "JOB_SEARCH_PAGE_QUERY_EXPANSION",
            "selectedFilters": {},
            "spellCorrectionEnabled": "true",
            "keywords": "KEYWORD_PLACEHOLDER",
            "locationUnion": "",
        }

        ops = {
            "experience": "List({stringify})",
            "jobType": "List({stringify})",
            "workplaceType": "List({stringify})",
            "locationUnion": "(geoId:{})",
            "company": "List({stringify})",
            "title": "List({stringify})",
            "industry": "List({stringify})",
            "distance": "List({})",
            "sortBy": "List({})",
            "timePostedRange": "List(r{})",
        }
        for key, value in kwargs.items():
            if key == "keywords":
                continue
            if key == "locationUnion":
                query[key] = ops[key].format(value)
            elif "stringify" in ops[key] and value:
                stringify = ",".join(value)
                query["selectedFilters"][key] = ops[key].format(stringify=stringify)
            elif value:
                query["selectedFilters"][key] = ops[key].format(value)

        query_string = (
            str(query)
            .replace(" ", "")
            .replace("'", "")
            .replace("KEYWORD_PLACEHOLDER", kwargs.get("keywords", ""))
            .replace("{", "(")
            .replace("}", ")")
        )

        default_params = {
            "decorationId": "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-174",
            "count": count,
            "q": "jobSearch",
            "query": query_string,
            "start": offset,
        }

        return (
            f"/voyagerJobsDashJobCards?{urlencode(default_params, safe='(),:')}",
            default_params,
        )

    @staticmethod
    def build_contact_info_url(public_id: str | None, urn_id: str | None):
        return f"/identity/profiles/{public_id or urn_id}/profileContactInfo"

    @staticmethod
    def build_skills_info_url(public_id: str | None, urn_id: str | None):
        return f"/identity/profiles/{public_id or urn_id}/skills"

    @staticmethod
    def build_privacy_settings_url(public_id: str):
        return f"/identity/profiles/{public_id}/privacySettings"

    @staticmethod
    def build_member_badges_url(public_id: str):
        return f"/identity/profiles/{public_id}/memberBadges"

    @staticmethod
    def build_profile_network_url(public_id: str):
        return f"/identity/profiles/{public_id}/networkinfo"

    @staticmethod
    def build_get_profile_url(public_id: str | None, urn_id: str | None):
        # NOTE this still works for now, but will probably eventually have to be converted to
        # https://www.linkedin.com/voyager/api/identity/profiles/ACoAAAKT9JQBsH7LwKaE9Myay9WcX8OVGuDq9Uw
        return f"/identity/profiles/{public_id or urn_id}/profileView"

    @staticmethod
    def build_get_organization_url_params(public_id: str):
        return "/organization/companies", {
            "decorationId": "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain-12",
            "q": "universalName",
            "universalName": public_id,
        }

    @staticmethod
    def get_v2_headers():
        return {"accept": "application/vnd.linkedin.normalized+json+2.1"}
