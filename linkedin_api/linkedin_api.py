"""
Provides linkedin api-related code
"""
import requests
import pickle
import json
import logging
import os

REQUEST_HEADERS = {
    'X-Li-User-Agent': 'LIAuthLibrary:3.2.4 \
                        com.linkedin.LinkedIn:8.8.1 \
                        iPhone:8.3',
    'User-Agent': 'LinkedIn/8.8.1 CFNetwork/711.3.18 Darwin/14.0.0',
    'X-User-Language': 'en',
    'X-User-Locale': 'en_US',
    'Accept-Language': 'en-us',
}

_COOKIE_FILE_PATH = './tmp/cookies'

_AUTH_BASE_URL = 'https://www.linkedin.com'
_API_BASE_URL = 'https://www.linkedin.com/voyager/api'


class LinkedinAPI(object):
    """
    Class to authenticate with, and call, the Linkedin API.
    """

    logger = None

    def __init__(self):
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) \
                        AppleWebKit/537.36 (KHTML, like Gecko) \
                        Chrome/66.0.3359.181 Safari/537.36'
        }

        LinkedinAPI.logger = logging.getLogger('LinkedinAPI')
        logging.basicConfig(level=logging.INFO)

    @staticmethod
    def _request_session_cookies():
        """
        Return a new set of session cookies as given by Linkedin.
        """
        try:
            with open(_COOKIE_FILE_PATH, 'rb') as f:
                cookies = pickle.load(f)
                if cookies:
                    return cookies
        except FileNotFoundError:
            LinkedinAPI.logger.debug('Cookie file not found. Requesting new cookies.')
            os.mkdir('tmp')
            pass

        res = requests.get(
            f'{_AUTH_BASE_URL}/uas/authenticate',
            headers=REQUEST_HEADERS
        )

        return res.cookies

    def _set_session_cookies(self, cookiejar):
        """
        Set cookies of the current session and save them to a file.
        """
        self.session.cookies = cookiejar
        self.session.headers['csrf-token'] = self.session.cookies['JSESSIONID'].strip('\"')
        with open(_COOKIE_FILE_PATH, 'wb') as f:
            pickle.dump(cookiejar, f)

    def authenticate(self, username, password):
        """
        Authenticate with Linkedin.

        Return a session object that is authenticated.
        """
        self._set_session_cookies(self._request_session_cookies())

        payload = {
            'session_key': username,
            'session_password': password,
            'JSESSIONID': self.session.cookies['JSESSIONID'],
        }

        res = requests.post(
            f'{_AUTH_BASE_URL}/uas/authenticate',
            data=payload,
            cookies=self.session.cookies,
            headers=REQUEST_HEADERS
        )

        data = res.json()

        # TODO raise better exceptions
        if res.status_code != 200:
            raise Exception()
        elif data['login_result'] != 'PASS':
            raise Exception()

        self._set_session_cookies(res.cookies)

    def get_profile_contact_info(self, public_profile_id=None, profile_urn_id=None):
        """
        Return data for a single profile.

        [public_profile_id] - public identifier i.e. tom-quirk-1928345
        [profile_urn_id] - id provided by the related URN
        """
        res = self.session.get(
            f'{_API_BASE_URL}/identity/profiles/{public_profile_id or profile_urn_id}/profileContactInfo',
        )
        data = res.json()

        contact_info = {
            'email_address': data.get('emailAddress'),
            'websites': [],
            'phone_numbers': data.get('phoneNumbers', [])
        }

        websites = data.get('websites', [])
        for item in websites:
            item['label'] = item['type']['com.linkedin.voyager.identity.profile.CustomWebsite']['label']
            del item['type']

        contact_info['websites'] = websites

        return contact_info

    def get_profile(self, public_profile_id=None, profile_urn_id=None):
        """
        Return data for a single profile.

        [public_profile_id] - public identifier i.e. tom-quirk-1928345
        [profile_urn_id] - id provided by the related URN
        """
        res = self.session.get(
            f'{_API_BASE_URL}/identity/profiles/{public_profile_id or profile_urn_id}/profileView',
        )
        data = res.json()

        # massage [profile] data
        profile = data['profile']
        if 'miniProfile' in profile:
            profile['displayPictureUrl'] = (
                profile['miniProfile']
                ['picture']['com.linkedin.common.VectorImage']['rootUrl']
            )
            profile['profile_id'] = profile['miniProfile']['entityUrn'].split(':')[3]

            del profile['miniProfile']

        del profile['defaultLocale']
        del profile['supportedLocales']
        del profile['versionTag']
        del profile['showEducationOnProfileTopCard']

        # massage [experience] data
        experience = data['positionView']['elements']
        for item in experience:
            if 'company' in item:
                item['company']['logoUrl'] = (
                    item['company']['miniCompany']
                    ['logo']['com.linkedin.common.VectorImage']['rootUrl']
                )
                del item['company']['miniCompany']

        profile['experience'] = experience

        # massage [skills] data
        skills = [item['name'] for item in data['skillView']['elements']]

        profile['skills'] = skills

        # massage [education] data
        education = data['educationView']['elements']
        for item in education:
            if 'school' in item:
                item['school']['logoUrl'] = (
                    item['school']
                    ['logo']['com.linkedin.common.VectorImage']['rootUrl']
                )
                del item['school']['logo']

        profile['education'] = education

        return profile

    def get_profile_connections(self, profile_urn_id, connections=[], max_connections=None):
        """
        Return a list of profile ids connected to profile of given [profile_urn_id]
        """
        _MAX_COUNT = 49  # max seems to be 49
        params = {
            'count': max_connections if max_connections and max_connections < _MAX_COUNT else _MAX_COUNT,
            'guides': f"List(v->PEOPLE,facetNetwork->F|S,facetConnectionOf->{profile_urn_id})",
            'origin': 'MEMBER_PROFILE_CANNED_SEARCH',
            'q': 'guided',
            'start': len(connections)
        }
        res = self.session.get(
            f'{_API_BASE_URL}/search/cluster',
            params=params
        )
        data = res.json()

        total_found = data['paging']['total']

        discovered_connections = []
        for item in data['elements'][0]['elements']:
            search_profile = item['hitInfo']['com.linkedin.voyager.search.SearchProfile']

            profile_id = search_profile['id']
            distance = search_profile['distance']['value']

            discovered_connections.append({'profile_id': profile_id, 'distance': distance})

        connections.extend(discovered_connections)

        # recursive base case
        if (
            (max_connections is not None and len(connections) >= max_connections) or
            len(connections) >= total_found
        ):
            return connections

        return self.get_profile_connections(profile_urn_id, connections, max_connections=max_connections)
