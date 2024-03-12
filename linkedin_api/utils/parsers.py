from operator import itemgetter
from linkedin_api.utils.helpers import get_id_from_urn


def parse_profile_data(data):
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

        profile["profile_id"] = get_id_from_urn(
            profile["miniProfile"]["entityUrn"])
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


def parse_response_text(text, max_len):
    return text[:max_len] + '... (truncated)' if len(
        text) > max_len else text
