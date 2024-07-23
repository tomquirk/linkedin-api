from pydantic import BaseModel, ConfigDict, Field, HttpUrl, EmailStr
from pydantic_extra_types.country import CountryShortName, CountryAlpha2
from typing import Any
from enum import Enum
from datetime import datetime
from linkedin_api.utils.query_options import LocationType


class ContentSource(Enum):
    JOBS_PREMIUM_OFFLINE = "JOBS_PREMIUM_OFFLINE"
    JOBS_PREMIUM = "JOBS_PREMIUM"
    JOBS_CREATE = "JOBS_CREATE"


class JobState(Enum):
    LISTED = "LISTED"
    SUSPENDED = "SUSPENDED"


class ContentType(Enum):
    UNIVERSAL = "UNIVERSAL"
    CONTENT_B = "CONTENT_B"


class DistanceValue(Enum):
    DISTANCE_1 = "DISTANCE_1"
    DISTANCE_2 = "DISTANCE_2"
    DISTANCE_3 = "DISTANCE_3"
    OUT_OF_NETWORK = "OUT_OF_NETWORK"


class EnabledIndicators(Enum):
    ALL_ENABLED = "ALL_ENABLED"
    # TODO add more later as we discover them


class VisibilitySettings(Enum):
    PUBLIC = "PUBLIC"
    # TODO add more later as we discover them


class Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Metadata(Base):
    pagination_token: str | None = Field(alias="paginationToken", default=None)


class MiniProfile(Base):
    # TODO see if we can add this to all the other requests that send back a mini profile
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    occupation: str | None = None
    entity_urn: str = Field(alias="entityUrn")
    public_identifier: str = Field(alias="publicIdentifier")


class Paging(Base):
    count: int
    start: int
    total: int | None = None


class Distance(Base):
    value: DistanceValue


class Skill(Base):
    name: str


class Date(Base):
    month: int | None = None
    day: int | None = None
    year: int | None = None


class TimePeriod(Base):
    start_date: Date = Field(alias="startDate")
    end_date: Date | None = Field(alias="endDate", default=None)


class Range(Base):
    start: int
    end: int


class Response(Base):
    paging: Paging


class Company(Base):
    employee_count_range: Range | None = None
    industries: list[str] | None = None


class LinkedInExperience(Base):
    entity_urn: str = Field(alias="entityUrn")
    company_name: str = Field(alias="companyName")
    time_period: TimePeriod | None = Field(alias="timePeriod", default=None)
    description: str | None = None
    company: Company | None = None
    title: str
    company_urn: str | None = Field(alias="companyUrn", default=None)
    company_logo_url: HttpUrl | None = Field(alias="companyLogoUrl", default=None)


class LinkedInEducation(Base):
    entity_urn: str = Field(alias="entityUrn")
    description: str | None = None
    degree_name: str | None = Field(alias="degreeName", default=None)
    school_name: str = Field(alias="schoolName")
    school_urn: str | None = Field(alias="schoolUrn", default=None)


class LinkedInPublication(Base):
    name: str
    description: str
    url: HttpUrl


class LinkedInCertification(Base):
    authority: str
    name: str
    time_period: TimePeriod | None = Field(alias="timePeriod", default=None)
    company: Company | None = None
    display_source: str | None = Field(alias="displaySource", default=None)
    url: HttpUrl | None = None


class LinkedInVolunteer(Base):
    role: str
    company_name: str = Field(alias="companyName")
    time_period: TimePeriod = Field(alias="timePeriod")
    cause: str | None = None
    description: str
    company_urn: str | None = Field(alias="companyUrn", default=None)


class LinkedInHonor(Base): ...


class LinkedInProject(Base):
    time_period: TimePeriod = Field(alias="timePeriod")
    description: str
    title: str


class LinkedInProfile(Base):
    summary: str | None = None
    industry_name: str = Field(alias="industryName")
    last_name: str = Field(alias="lastName")
    location_name: str = Field(alias="locationName")
    student: bool
    birth_date: Date | None = Field(alias="birthDate", default=None)
    country: CountryShortName = Field(alias="geoCountryName")
    country_urn: str = Field(alias="geoCountryUrn")
    industry_urn: str = Field(alias="industryUrn")
    first_name: str = Field(alias="firstName")
    entity_urn: str = Field(alias="entityUrn")
    geo_location_name: str = Field(alias="geoLocationName")
    headline: str
    display_picture_url: HttpUrl | None = Field(alias="displayPictureUrl", default=None)
    urn_id: str
    profile_urn: str
    member_urn: str
    public_id: str
    experience: list[LinkedInExperience]
    education: list[LinkedInEducation]
    languages: list[Skill]
    publications: list[LinkedInPublication]
    certifications: list[LinkedInCertification]
    volunteer: list[LinkedInVolunteer]
    honors: list[Any]  # TODO Replace this with actual fields
    projects: list[LinkedInProject]
    skills: list[Skill]


class LinkedInPrivacySettings(Base):
    messaging_type_indicators: EnabledIndicators = Field(
        alias="messagingTypingIndicators"
    )
    allow_open_profile: bool = Field(alias="allowOpenProfile")
    profile_picture_visibility_setting: VisibilitySettings = Field(
        alias="profilePictureVisibilitySetting"
    )
    entity_urn: str = Field(alias="entityUrn")
    show_public_profile: bool = Field(alias="showPublicProfile")
    show_premium_subscriber_badge: bool = Field(alias="showPremiumSubscriberBadge")
    public_profile_picture_visibility_setting: VisibilitySettings = Field(
        alias="publicProfilePictureVisibilitySetting"
    )
    former_name_visibility_setting: VisibilitySettings = Field(
        alias="formerNameVisibilitySetting"
    )
    messaging_seen_receipts: EnabledIndicators = Field(alias="messagingSeenReceipts")
    allow_profile_edit_broadcasts: bool = Field(alias="allowProfileEditBroadcasts")


class LinkedInMemberBadges(Base):
    premium: bool
    influencer: bool
    entity_urn: str = Field(alias="entityUrn")
    open_link: bool = Field(alias="openLink")
    job_seeker: bool = Field(alias="jobSeeker")


class LinkedInNetwork(Base):
    distance: Distance
    entity_urn: str = Field(alias="entityUrn")
    following: bool
    followable: bool
    following_info: str = Field(alias="*followingInfo")
    followers_count: int = Field(alias="followersCount")
    connections_count: int = Field(alias="connectionsCount")


class CompanyIndustry(Base):
    localized_name: str = Field(alias="localizedName")


class OfficeLocation(Base):
    country: CountryAlpha2
    geographic_area: str = Field(alias="geographicArea")
    city: str
    postal_code: str | None = Field(alias="postalCode", default=None)
    line_1: str = Field(alias="line1")


class LinkedInOrganization(Base):
    staffing_company: bool = Field(alias="staffingCompany")
    staff_count: int = Field(alias="staffCount")
    ads_rule: str = Field(alias="adsRule")
    claimable: bool
    lcp_treatment: bool = Field(alias="lcpTreatment")
    name: str
    description: str
    paid_company: bool = Field(alias="paidCompany")
    company_page_url: HttpUrl = Field(alias="companyPageUrl")
    url: HttpUrl
    job_search_page_url: HttpUrl = Field(alias="jobSearchPageUrl")
    specialities: list[str]
    company_industries: list[CompanyIndustry] = Field(alias="companyIndustries")
    headquarter: OfficeLocation
    confirmed_locations: list[OfficeLocation] = Field(alias="confirmedLocations")


class LinkedInOrganizationResponse(Response):
    elements: LinkedInOrganization


class TwitterContactInfo(Base):
    name: str
    credential_id: str = Field(alias="credentialId")


class WebsiteContactInfo(Base):
    url: HttpUrl
    label: str | None = None


class LinkedInContactInfo(Base):
    email_address: EmailStr | None = None
    birth_date: Date | None = None
    twitter: list[TwitterContactInfo]
    websites: list[WebsiteContactInfo]
    phone_numbers: list[Any]  # TODO figure this out
    ims: Any | None = None  # TODO figure this out


class LinkedInSearchElement(Base):
    template: ContentType


class LinkedInSearchPeopleElement(Base):
    urn_id: str
    distance: DistanceValue
    job_title: str
    location: str
    name: str


class LinkedInSearchCompaniesElement(Base):
    urn_id: str
    name: str
    headline: str
    subline: str


class LinkedInSearchPeopleResponse(Response):
    elements: list[LinkedInSearchPeopleElement]


class LinkedInSearchCompaniesResponse(Response):
    elements: list[LinkedInSearchCompaniesElement]


class LinkedInLikes(Base):
    paging: Paging


class LinkedInSocialDetail(Base):
    urn: str
    total_shares: int = Field(alias="totalShares")
    thread_id: str = Field(alias="threadId")
    likes: LinkedInLikes


class LinkedInText(Base):
    text: str


class LinkedInCommentary(Base):
    num_lines: int = Field(alias="numLines")
    text: LinkedInText


class LinkedInProfilePostElement(Base):
    entity_urn: str = Field(alias="entityUrn")
    social_detail: LinkedInSocialDetail = Field(alias="socialDetail")
    commentary: LinkedInCommentary | None = None


class LinkedInProfilePostsResponse(Response):
    metadata: Metadata
    elements: list[LinkedInProfilePostElement]


class LinkedInProfileSkillsResponse(Response):
    elements: list[Skill]


class LinkedInCommentElement(Base):
    commenter_profile_urn: str = Field(alias="commenterProfileId")
    original_language: str | None = Field(alias="originalLanguage", default=None)
    comment: LinkedInText = Field(alias="commentV2")
    created_time: datetime = Field(alias="createdTime")


class LinkedInPostCommentResponse(Response):
    metadata: Metadata
    elements: list[LinkedInCommentElement]


class LinkedInVoyagerValueV2(Base):
    commentary: LinkedInCommentary | None = None
    social_detail: LinkedInSocialDetail = Field(alias="socialDetail")


class LinkedInUpdateValue(Base):
    value_v2: LinkedInVoyagerValueV2 = Field(
        alias="com.linkedin.voyager.feed.render.UpdateV2"
    )


class LinkedInUpdateElement(Base):
    value: LinkedInUpdateValue


class LinkedInUpdatesResponse(Response):
    elements: list[LinkedInUpdateElement]


class LinkedInSelfProfile(Base):
    plan_id: int = Field(alias="plainId")
    public_contact_info: Any = Field(
        alias="publicContactInfo"
    )  # TODO Figure this out later
    premium_subscriber: bool = Field(alias="premiumSubscriber")
    mini_profile: MiniProfile = Field(alias="miniProfile")


class LinkedInJobSearchElement(Base):
    content_source: ContentSource = Field(alias="contentSource")
    entity_urn: str = Field(alias="entityUrn")
    tracking_urn: str = Field(alias="trackingUrn")
    reposted_job: bool = Field(alias="repostedJob")
    title: str
    poster_id: str | None = Field(alias="posterId", default=None)


class LinkedInJobSearchResponse(Response):
    elements: list[LinkedInJobSearchElement]


class OffsiteApply(Base):
    applyStartersPreferenceVoid: bool | None = None
    company_apply_url: HttpUrl = Field(alias="companyApplyUrl")
    in_page_offsite_apply: bool | None = Field(alias="inPageOffsiteApply", default=None)


class ComplexApply(Base):
    unify_apply_enabled: bool | None = Field(alias="unifyApplyEnabled", default=None)
    company_apply_url: HttpUrl | None = Field(alias="companyApplyUrl", default=None)
    easy_apply_url: HttpUrl = Field(alias="easyApplyUrl")


class LinkedInApplyMethod(Base):
    off_site_apply: OffsiteApply | None = Field(
        default=None, alias="com.linkedin.voyager.jobs.OffsiteApply"
    )
    complex_site_apply: ComplexApply | None = Field(
        default=None, alias="com.linkedin.voyager.jobs.ComplexOnsiteApply"
    )


class LinkedInJob(Base):
    job_id: int = Field(alias="jobPostingId")
    listed_at: datetime = Field(alias="listedAt")
    title: str
    job_state: JobState = Field(alias="jobState")
    description: LinkedInText
    work_remote_allowed: bool = Field(alias="workRemoteAllowed")
    formatted_location: str = Field(alias="formattedLocation")
    work_place_types: list[LocationType] = Field(alias="workplaceTypes")
    apply_method: LinkedInApplyMethod = Field(alias="applyMethod")


class SkillMatchStatus(Base):
    localized_skill_display_name: str = Field(alias="localizedSkillDisplayName")
    skill: Skill


class LinkedInJobSkills(Base):
    company_urn: str | None = Field(alias="companyUrn", default=None)
    entity_urn: str = Field(alias="entityUrn")
    skill_match_status: list[SkillMatchStatus] = Field(alias="skillMatchStatuses")
