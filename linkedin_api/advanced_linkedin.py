from datetime import datetime
import json
from random import random
import re
import time
from linkedin_api import Linkedin
from linkedin_api.utils.function import retry
from linkedin_api.utils.header import get_csrf_token_header, get_x_li_track_header
from linkedin_api.utils.helpers import generate_tracking_id
from linkedin_api.utils.response import APIResponse, encode_api_response, get_api_response_log, validate_retryable_response_factory
from linkedin_api.utils.parsers import parse_profile_data


class AdvancedLinkedin(Linkedin):
    def authenticate(self, force_refresh=True, delay=random() * 0.5 + 0.5):
        if not self.username:
            raise Exception(f"Unknow username {self.username}")

        if not self.password:
            raise Exception(f"Unknow password {self.password}")

        self.client.authenticate(
            self.username, self.password, force_refresh=force_refresh)

        if delay:
            time.sleep(delay)

    def backup_cookies(self):
        if not self.username:
            raise Exception(f"Unknow username {self.username}")

        # Load cookies from the local file
        cookies = self.client._cookie_repository._load_cookies_from_cache(
            self.username)

        # Save cookies into the local file
        self.client._cookie_repository.save(
            cookies=cookies, username=self.username, raw_time_suffix=datetime.now())

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([
                                                                        401, 403]),
    )
    def get_mini_profile(self, public_id=None, hash_id=None, temp_hash_id=None,
                         decorationIndex='21', raise_exception=False, verbose=True,
                         # Placeholder for enabling retry toggle
                         # To enable retry, you must specify "enable_retry=True" when calling the method
                         enable_retry=False, retry_limit=1, verbose_on_retry=False):
        api_name = 'mini profile API'
        notes = None

        res = self._fetch(
            f"/identity/dash/profiles?q=memberIdentity&memberIdentity={public_id or hash_id or temp_hash_id}"
            # "decorationIndex" can range from 1 to 22, as of 2024/03/08
            # One example: https://stackoverflow.com/questions/72755463/request-data-from-linkedin
            f"&decorationId=com.linkedin.voyager.dash.deco.identity.profile.WebTopCardCore-{decorationIndex}"
        )

        if verbose:
            self.logger.debug(get_api_response_log(
                api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))

        # NOTE: one example of 401 response:
        # { 'status': 401 }
        # This can happen when cookies are expired.
        if res.status_code != 200:
            if raise_exception:
                raise Exception(get_api_response_log(
                    api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))
            else:
                if res.status_code == 401:
                    notes = 'Cookies are expired'

                return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id, notes=notes)

        return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id)

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([
                                                                        401, 403, 999]),
    )
    def get_profile_v2(self, public_id=None, hash_id=None, temp_hash_id=None,
                       raise_exception=False, return_raw_data=False, verbose=True,
                       # Placeholder for enabling retry toggle
                       # To enable retry, you must specify "enable_retry=True" when calling the method
                       enable_retry=False, retry_limit=1, verbose_on_retry=False):
        api_name = 'profile v2 API'
        notes = None

        res = self._fetch(
            f"/identity/profiles/{public_id or hash_id or temp_hash_id}/profileView")

        if verbose:
            self.logger.debug(get_api_response_log(
                api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))

        # NOTE one example of 403 response:
        #
        # {
        #     "exceptionClass": "com.linkedin.voyager.common.VoyagerUserVisibleException",
        #     "message": "This profile can't be accessed",
        #     "status": 403
        # }
        #
        # This can happen when cookies are expired.
        # This might happen when requests are too frequently, or the profile cannot be accessed.
        if res.status_code != 200:
            if raise_exception:
                raise Exception(get_api_response_log(
                    api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))
            else:
                if res.status_code == 999:
                    notes = 'Cookies are expired'
                elif res.status_code == 403:
                    notes = 'Cookies are expired or the profile cannot be accessed'

                return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id, notes=notes)

        data = res.json()
        final_data = data if return_raw_data else parse_profile_data(data)
        return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id, data=final_data)

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([999]),
    )
    def get_profile_html(self, public_id=None, hash_id=None, temp_hash_id=None,
                         raise_exception=False, verbose=True,
                         # Placeholder for enabling retry toggle
                         # To enable retry, you must specify "enable_retry=True" when calling the method
                         enable_retry=False, retry_limit=1, verbose_on_retry=False):
        api_name = 'profile HTML API'
        notes = None

        url = f'https://www.linkedin.com/in/{public_id or hash_id or temp_hash_id}/'
        res = self._fetch(url)

        if verbose:
            self.logger.debug(get_api_response_log(
                api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))

        if res.status_code != 200:
            if raise_exception:
                raise Exception(get_api_response_log(
                    api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id))
            else:
                if res.status_code == 999:
                    notes = 'Cookies are expired'

                    return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id, notes=notes)

        return encode_api_response(api_name=api_name, response=res, user_id=public_id or hash_id or temp_hash_id)

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([503]),
    )
    def get_user_ids(self, public_id=None, hash_id=None, temp_hash_id=None,
                     raise_exception=False, verbose=True,
                     enable_mini_profile_fetch=True, enable_profile_fetch=True, enable_profile_html_fetch=True,
                     # Placeholder for enabling retry toggle
                     # To enable retry, you must specify "enable_retry=True" when calling the method
                     enable_retry=False, retry_limit=1, verbose_on_retry=False) -> APIResponse:
        api_name = 'user IDs retrieval API'
        error_dict = {
            'mini_profile': None,
            'profile': None,
            'profile_html': None,
        }

        if enable_mini_profile_fetch:
            # First attempt to retrieve user IDs from the mini profile
            try:
                data = self.get_mini_profile(
                    public_id=public_id, hash_id=hash_id, temp_hash_id=temp_hash_id, raise_exception=False,
                    # Avoid redundant logs
                    verbose=False
                )

                if data['ok']:
                    profile = data['data']['elements'][0]
                    public_id = profile['publicIdentifier']

                    # Parse from ""urn:li:fsd_profile:ACo..."
                    hash_id = profile['entityUrn'].split(":")[-1]

                    # Parse from "urn:li:member:123..."
                    member_id = profile['objectUrn'].split(":")[-1]
                    member_id = int(
                        member_id) if member_id is not None else None

                    id_dict = {
                        "public_id": public_id,
                        "hash_id": hash_id,
                        "member_id": member_id,
                    }

                    if verbose:
                        self.logger.debug(
                            f"Retrieved user IDs from mini profile: {id_dict}")

                    return encode_api_response(api_name=api_name, status=data['status'], data=id_dict,
                                               user_id=public_id or hash_id or temp_hash_id, error=error_dict)
                else:
                    error_dict['mini_profile'] = data

                    raise Exception(data)
            except Exception as e:
                if verbose:
                    self.logger.error(
                        f"Failed to retrieve user IDs based on mini profile with the following exception")
                    self.logger.error(e)

                if not error_dict['mini_profile']:
                    error_dict['mini_profile'] = encode_api_response(
                        api_name='mini profile API', status=500, data=str(e),
                        user_id=public_id or hash_id or temp_hash_id)

        if enable_profile_fetch:
            # Second attempt to retrieve user IDs from the profile
            try:
                data = self.get_profile_v2(
                    public_id=public_id, hash_id=hash_id, temp_hash_id=temp_hash_id, raise_exception=False,
                    # Avoid redundant logs
                    verbose=False
                )

                if data['ok']:
                    profile = data['data']
                    public_id = profile['public_id']
                    hash_id = profile['profile_id']

                    # Parse from "urn:li:member:123..."
                    member_id = profile['member_urn'].split(":")[-1]
                    member_id = int(
                        member_id) if member_id is not None else None

                    id_dict = {
                        "public_id": public_id,
                        "hash_id": hash_id,
                        "member_id": member_id,
                    }

                    if verbose:
                        self.logger.debug(
                            f"Retrieved user IDs from profile: {id_dict}")

                    return encode_api_response(api_name=api_name, status=data['status'], data=id_dict,
                                               user_id=public_id or hash_id or temp_hash_id, error=error_dict)
                else:
                    error_dict['profile'] = data

                    raise Exception(data)
            except Exception as e:
                if verbose:
                    self.logger.error(
                        f"Failed to retrieve user IDs based on profile with the following exception")
                    self.logger.error(e)

                if not error_dict['profile']:
                    error_dict['profile'] = encode_api_response(
                        api_name='profile v2 API', status=500, data=str(e),
                        user_id=public_id or hash_id or temp_hash_id)

        if enable_profile_html_fetch:
            # Third attempt to retrieve user IDs from the HTML
            try:
                # url = f'https://www.linkedin.com/in/{public_id or hash_id or temp_hash_id}/'
                # html_response = self.client.session.get(url)

                data = self.get_profile_html(
                    public_id=public_id, hash_id=hash_id, temp_hash_id=temp_hash_id, raise_exception=False,
                    # Avoid redundant logs
                    verbose=False
                )

                if data['ok']:
                    def get_public_id_from_html(html):
                        parsed_html = html.replace('&quot;', '')
                        matches = re.findall(
                            r'memberIdentity\\u003D([^\\]+)', parsed_html)

                        for match in matches:
                            if not match.startswith('AEM'):
                                return match

                        # Look for "vanityName:xxx"
                        matches = re.findall(r'vanityName:[^\)]+', parsed_html)
                        if matches and matches[0]:
                            return matches[0].split(':')[-1]

                        raise Exception("Could not find public ID from HTML")

                    def get_hash_id_from_html(html):
                        parsed_html = html.replace('&quot;', '')
                        matches = re.findall(
                            r'urn:li:fsd_profile:([^,]+)]', parsed_html)

                        if matches and matches[0]:
                            return matches[0]

                        raise Exception("Could not find hash ID from HTML")

                    def get_member_id_from_html(html, hash_id):
                        parsed_html = html.replace('&quot;', '')
                        matches = re.findall(
                            fr'\({hash_id}(.+),objectUrn:urn:li:member:([\d]+)', parsed_html)

                        if matches and matches[0] and matches[0][1]:
                            return int(matches[0][1])

                        raise Exception("Could not find member ID from HTML")

                    hash_id = get_hash_id_from_html(data['data'])
                    public_id = get_public_id_from_html(data['data'])
                    member_id = get_member_id_from_html(
                        data['data'], hash_id)

                    id_dict = {
                        "public_id": public_id,
                        "hash_id": hash_id,
                        "member_id": member_id,
                    }

                    if verbose:
                        self.logger.debug(
                            f"Retrieved user IDs from profile HTML: {id_dict}")

                    return encode_api_response(api_name=api_name, status=data['status'], data=id_dict,
                                               user_id=public_id or hash_id or temp_hash_id, error=error_dict)
                else:
                    error_dict['profile_html'] = data

                    raise Exception(data)
            except Exception as e:
                if verbose:
                    self.logger.error(
                        f"Failed to retrieve user IDs based on HTML with the following exception")
                    self.logger.error(e)

                if not error_dict['profile_html']:
                    error_dict['profile_html'] = encode_api_response(
                        api_name='profile HTML API', status=500, data=str(e),
                        user_id=public_id or hash_id or temp_hash_id)

        if raise_exception:
            # Does not add "error_dict" into the log as it's too long
            raise Exception(
                get_api_response_log(api_name=api_name, status=503, user_id=public_id or hash_id or temp_hash_id))
        else:
            if verbose:
                # Does not add "error_dict" into the log as it's too long
                self.logger.error(
                    get_api_response_log(api_name=api_name, status=503, user_id=public_id or hash_id or temp_hash_id))

            return encode_api_response(api_name=api_name, status=503, data=error_dict, user_id=public_id or hash_id or temp_hash_id)

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([
                                                                        401, 424]),
    )
    def add_connection_v2(self, public_id=None, hash_id=None, temp_hash_id=None, message="",
                          raise_exception=False, enable_public_id_sending=False, verbose=True,
                          # Placeholder for enabling retry toggle
                          # To enable retry, you must specify "enable_retry=True" when calling the method
                          enable_retry=False, retry_limit=1, verbose_on_retry=False):
        api_name = 'connection request v2 API'
        notes = None

        # If hash id is not empty, then no need to convert the ID to get the hash id
        if hash_id is None:
            # If hash id is empty, and public id sending is disabled, then need to retrieve the hash id
            # If hash id is empty, public id sending is enabled, and public id is empty, then need to retrieve the hash id (no need for public id)
            if not enable_public_id_sending or (enable_public_id_sending and public_id is None):
                data = self.get_user_ids(
                    public_id=public_id, temp_hash_id=temp_hash_id)

                if data['ok']:
                    hash_id = data['data']['hash_id']
                else:
                    if verbose:
                        self.logger.error(
                            f"Failed to retrieve hash ID as prerequisite for {api_name} with data {data}")

                    if raise_exception:
                        raise Exception(data)

                    return encode_api_response(f"Failed to retrieve hash ID as prerequisite for {api_name}", status=424, data=data)

        tracking_id = generate_tracking_id()
        payload = {
            "trackingId": tracking_id,
            "message": message,
            "invitations": [],
            "excludeInvitations": [],
            "invitee": {
                "com.linkedin.voyager.growth.invitation.InviteeProfile": {
                    "profileId": hash_id or public_id
                }
            },
        }
        res = self._post(
            "/growth/normInvitations",
            data=json.dumps(payload),
            headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )

        if verbose:
            self.logger.debug(get_api_response_log(
                api_name=api_name, response=res, user_id=hash_id))

        if res.status_code != 201:
            if raise_exception:
                raise Exception(
                    get_api_response_log(
                        api_name=api_name, response=res, user_id=hash_id))
            else:
                if res.status_code == 400 and 'CANT_RESEND_YET' in res.text:
                    notes = 'Already sent the connection request'
                elif res.status_code == 401:
                    notes = 'Cookies are expired'

                return encode_api_response(api_name=api_name, response=res, user_id=hash_id, notes=notes)

        return encode_api_response(api_name=api_name, response=res, user_id=hash_id, notes=notes)

    @retry(
        on_retry_prepare_method_name_in_class='authenticate',
        validate_retryable_response=validate_retryable_response_factory([
                                                                        401, 424]),
    )
    def add_connection_v3(self, public_id=None, hash_id=None, temp_hash_id=None, message="",
                          timezone=None, display_width=None, display_height=None,
                          raise_exception=False, verbose=True,
                          # Placeholder for enabling retry toggle
                          # To enable retry, you must specify "enable_retry=True" when calling the method
                          enable_retry=False, retry_limit=1, verbose_on_retry=False):
        api_name = 'connection request v3 API'
        notes = None

        # If hash id is not empty, then no need to convert the ID to get the hash id
        if hash_id is None:
            data = self.get_user_ids(
                public_id=public_id, temp_hash_id=temp_hash_id)

            if data['ok']:
                hash_id = data['data']['hash_id']
            else:
                if verbose:
                    self.logger.error(
                        f"Failed to retrieve hash ID as prerequisite for {api_name} with data {data}")

                if raise_exception:
                    raise Exception(data)

                return encode_api_response(f"Failed to retrieve hash ID as prerequisite for {api_name}", status=424, data=data)

        payload = {
            "invitee": {
                "inviteeUnion": {
                    "memberProfile": f"urn:li:fsd_profile:{hash_id}"
                }
            },
            "customMessage": message
        }

        # Add "csrf-token" header
        headers = {
            **get_csrf_token_header(self.client.session.cookies)
        }

        # Add "x-li-track" header
        if timezone and display_width and display_height:
            headers = {
                **headers,
                **get_x_li_track_header(
                    timezone=timezone, display_width=display_width, display_height=display_height)
            }

        if verbose:
            self.logger.debug(f"Prepared custom headers {headers}")

        res = self._post(
            "/voyagerRelationshipsDashMemberRelationships?action=verifyQuotaAndCreateV2&decorationId=com.linkedin.voyager.dash.deco.relationships.InvitationCreationResultWithInvitee-2",
            data=json.dumps(payload),
            headers=headers
        )

        if verbose:
            self.logger.debug(get_api_response_log(
                api_name=api_name, response=res, user_id=hash_id))

        if res.status_code != 200:
            if raise_exception:
                raise Exception(get_api_response_log(
                    api_name=api_name, response=res, user_id=hash_id))
            else:
                if res.status_code == 400 and 'CANT_RESEND_YET' in res.text:
                    notes = 'Already sent the connection request'
                elif res.status_code == 401:
                    notes = 'Cookies are expired'

                return encode_api_response(api_name=api_name, response=res, user_id=hash_id, notes=notes)

        return encode_api_response(api_name=api_name, response=res, user_id=hash_id, notes=notes)
