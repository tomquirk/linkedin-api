import base64
import json
import logging
import random
import re

from linkedin_api import Linkedin
from linkedin_api.utils.dict import get_value
from linkedin_api.utils.helpers import get_id_from_urn, random_extra_large_delay, convert_complex_data_to_normal_data
from operator import itemgetter


def generate_tracking_id():
    """Generates and returns a random trackingId

    :return: Random trackingId string
    :rtype: str
    """
    random_int_array = [random.randrange(256) for _ in range(16)]
    rand_byte_array = bytearray(random_int_array)
    return str(base64.b64encode(rand_byte_array))[2:-1]


def parse_linkedin_response(response_text, logging_cb=None, return_original_data=False):
    try:
        data = json.loads(response_text)
        parsed_data = {
            "code": get_value(data, 'data|code'),
            "status": get_value(data, 'data|status'),
        }

        if return_original_data:
            parsed_data["original_data"] = data

        return parsed_data
    except Exception as e:
        if logging_cb:
            logging_cb(
                f"Failed to parse LinkedIn response {response_text} with the following error")
            logging_cb(e)

        return {}


class AdvancedLinkedin(Linkedin):
    def add_connection_v2(self, profile_public_id, message="", profile_urn=None):
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
            logging.info("Message too long. Max size is 300 characters")
            return False

        if not profile_urn:
            profile, status = self.get_profile_v2(public_id=profile_public_id)

            # If the profile is successfully retrieved, parse the profile urn, i.e. hash id
            if profile:
                profile_urn_string = profile["profile_urn"]
                # Returns string of the form 'urn:li:fs_miniProfile:ACoAACX1hoMBvWqTY21JGe0z91mnmjmLy9Wen4w'
                # We extract the last part of the string
                profile_urn = profile_urn_string.split(":")[-1]

            # Otherwise, directly return the failure result
            else:
                return {
                    # Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/424
                    "status": 424,
                    "data": {
                        "code": 'ID_CONVERSION_FAILED',
                        "status": 424,
                    }
                }

        tracking_id = generate_tracking_id()
        payload = {
            "trackingId": tracking_id,
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

        logging.info(
            f"Retrieved LinkedIn response from add connection v2 API with code {res.status_code} and data {res.text}")

        data = parse_linkedin_response(res.text)

        return {
            "status": res.status_code,
            "data": data
        }

    def get_profile_v2(self, public_id=None, urn_id=None):
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
        res = self._fetch(
            f"/identity/profiles/{public_id or urn_id}/profileView")

        if res.status_code == 999:
            logging.info(f"Failed to retrieve LinkedIn profile with code {res.status_code} and data {res.text}")
            return {}, res.status_code

        data = res.json()
        if data and "status" in data and data["status"] != 200:
            logging.info(
                f"Failed to retrieve LinkedIn profile with code {res.status_code} and data {res.text}")
            return {}, res.status_code

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

        return profile, res.status_code

    def add_connection_v3(self, profile_public_id, message="", profile_id=None):

        if not profile_id:
            profile, status = self.get_profile_v2(public_id=profile_public_id)

            # If the profile is successfully retrieved, parse the profile urn, i.e. hash id
            if profile:
                profile_urn_string = profile["profile_urn"]
                # Returns string of the form 'urn:li:fs_miniProfile:ACoAACX1hoMBvWqTY21JGe0z91mnmjmLy9Wen4w'
                # We extract the last part of the string
                profile_id = profile_urn_string.split(":")[-1]

            # Otherwise, directly return the failure result
            else:
                return {
                    # Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/424
                    "status": 424,
                    "data": {
                        "code": 'ID_CONVERSION_FAILED',
                        "status": 424,
                    }
                }

        url = 'https://www.linkedin.com/voyager/api/voyagerRelationshipsDashMemberRelationships?action=verifyQuotaAndCreateV2&decorationId=com.linkedin.voyager.dash.deco.relationships.InvitationCreationResultWithInvitee-2'
        data = {
            "invitee": {
                "inviteeUnion": {
                    "memberProfile": f"urn:li:fsd_profile:{profile_id}"
                }
            },
            "customMessage": message
        }

        cleaned_cookie_dict = {key: value.strip('"') for key, value in
                               self.client.cookies.get_dict().items()}
        target_string = '; '.join(
            f'{key}="{cleaned_cookie_dict[key]}"' for key in cleaned_cookie_dict)

        headers = {
            "Cookie": target_string,
            'Csrf-Token': cleaned_cookie_dict['JSESSIONID'],
        }
        ret = self.client.session.post(url, data=json.dumps(data), headers=headers)

        logging.info(
            f"Add connection v3 retrieved LinkedIn response with code {ret.status_code} and data {ret.text}")

        data = parse_linkedin_response(ret.text)

        return {
            "status": ret.status_code,
            "data": data
        }

    def get_profile_and_contact_info(self, public_id: str):
        profile, status = self.get_profile_v2(public_id)

        random_extra_large_delay()

        contact_info = self.get_profile_contact_info(public_id)

        return profile, contact_info

    def process_connection(self, public_id):
        logging.info(f'Processing connection with public id {public_id}')

        raw_profile, raw_contact_info = self.get_profile_and_contact_info(public_id)
        logging.info('Loaded the profile and contact information')

        profile = convert_complex_data_to_normal_data(
            {**raw_profile, **raw_contact_info})
        logging.info('Processed the profile and contact information')

        return {
            "raw_profile": {**raw_profile, **raw_contact_info},
            "profile": profile,
        }

    def get_profile_id(self, profile_public_id):
        status = None
        try:
            profile, status = self.get_profile_v2(public_id=profile_public_id)
            if profile:
                profile_urn_string = profile["profile_urn"]
                # Returns string of the form 'urn:li:fs_miniProfile:ACoAACX1hoMBvWqTY21JGe0z91mnmjmLy9Wen4w'
                # We extract the last part of the string
                profile_urn = profile_urn_string.split(":")[-1]
                return profile_urn

            # Otherwise, directly return the failure result
            else:
                return {
                    "code": 'ID_CONVERSION_FAILED',
                    "status": status,
                }
        except Exception as e:
            logging.info(f"Failed to get profile urn: {profile_public_id}")
            logging.error(e)
            return {
                "code": 'ID_CONVERSION_FAILED',
                "status": status,
            }

    def get_profile_id_v2(self, user_id: str):
        # 将temp hash id转化成public id,并获取hash id
        try:
            # "user_id" can be either public id, temporary hash id, or hash id
            response = self._fetch(
                f'/identity/dash/profiles?q=memberIdentity&memberIdentity={user_id}'
                f'&decorationId=com.linkedin.voyager.dash.deco.identity.profile.WebTopCardCore-21'
            )
            logging.info(f"Get profile id v2 API status {response.status_code} and message {response.text}")
            profile = response.json()
            hash_id = profile['elements'][0]['entityUrn'].split(":")[-1]
            return {
                "code": response.status_code,
                "profile_id": hash_id
            }
        except Exception as e:
            url = f'https://www.linkedin.com/in/{user_id}/'
            profile_rp = self.client.session.get(url)

            def get_hash_id_from_html(html):
                try:
                    parsed_html = html.replace('&quot;', '')
                    matches = re.findall(
                        r'urn:li:fsd_profile:([^,]+)]', parsed_html)

                    return matches[0] if matches else None
                except Exception:
                    return None

            hash_id = get_hash_id_from_html(profile_rp.text)

            if hash_id:
                return {
                    "code": profile_rp.status_code,
                    "profile_id": hash_id
                }
            else:
                return {
                    "code": 424,
                    "profile_id": hash_id
                }

    def get_user_ids(self, user_id: str):
        # 将temp hash id转化成public id,并获取member id和hash id
        try:
            # "user_id" can be either public id, temporary hash id, or hash id
            profile = self._fetch(
                f'/identity/dash/profiles?q=memberIdentity&memberIdentity={user_id}'
                f'&decorationId=com.linkedin.voyager.dash.deco.identity.profile.WebTopCardCore-21'
            ).json()

            public_id = profile['elements'][0]['publicIdentifier']
            hash_id = profile['elements'][0]['entityUrn'].split(":")[-1]
            member_id = profile['elements'][0]['objectUrn'].split(":")[-1]
            member_id = int(member_id) if member_id is not None else None
            return public_id, hash_id, member_id
        except Exception as e:
            url = f'https://www.linkedin.com/in/{user_id}/'
            profile_rp = self.client.session.get(url)

            def get_public_id_from_html(html):
                try:
                    parsed_html = html.replace('&quot;', '')
                    matches = re.findall(
                        r'memberIdentity\\u003D([^\\]+)', parsed_html)

                    for match in matches:
                        if not match.startswith('AEM'):
                            return match
                    return None
                except Exception:
                    return None

            def get_hash_id_from_html(html):
                try:
                    parsed_html = html.replace('&quot;', '')
                    matches = re.findall(
                        r'urn:li:fsd_profile:([^,]+)]', parsed_html)

                    return matches[0] if matches else None
                except Exception:
                    return None

            def get_member_id_from_html(html, hash_id):
                try:
                    parsed_html = html.replace('&quot;', '')
                    matches = re.findall(
                        fr'\({hash_id}(.+),objectUrn:urn:li:member:([\d]+)', parsed_html)

                    return int(matches[0][1]) if matches else None
                except Exception:
                    return None

            hash_id = get_hash_id_from_html(profile_rp.text)
            public_id = get_public_id_from_html(profile_rp.text)
            member_id = get_member_id_from_html(profile_rp.text, hash_id)
            return public_id, hash_id, member_id
