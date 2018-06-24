"""
Provides linkedin api-related code
"""
import requests
import pickle
import logging
import os
import random
from time import sleep

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

_MAX_SEARCH_COUNT = 49  # max seems to be 49
_MAX_REPEATED_REQUESTS = 200  # VERY conservative max requests count to avoid rate-limit


class LinkedinAPI(object):
    """
    Class to authenticate with, and call, the Linkedin API.
    """

    logger = None

    def __init__(self, debug=False):
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) \
                        AppleWebKit/537.36 (KHTML, like Gecko) \
                        Chrome/66.0.3359.181 Safari/537.36'
        }

        LinkedinAPI.logger = logging.getLogger('LinkedinAPI')
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

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
            if 'com.linkedin.voyager.identity.profile.StandardWebsite' in item['type']:
                item['label'] = item['type']['com.linkedin.voyager.identity.profile.StandardWebsite']['category']
            elif '' in item['type']:
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
        sleep(random.randint(2, 5))  # sleep a random duration to try and evade suspention
        res = self.session.get(
            f'{_API_BASE_URL}/identity/profiles/{public_profile_id or profile_urn_id}/profileView',
        )

        data = res.json()

        if data and 'status' in data and data['status'] != 200:
            self.logger.info('request failed: {}'.format(data['message']))
            return {}

        # massage [profile] data
        profile = data['profile']
        if 'miniProfile' in profile:
            if 'picture' in profile['miniProfile']:
                profile['displayPictureUrl'] = (
                    profile['miniProfile']['picture']['com.linkedin.common.VectorImage']['rootUrl']
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
            if 'company' in item and 'miniCompany' in item['company']:
                if 'logo' in item['company']['miniCompany']:
                    logo = item['company']['miniCompany']['logo'].get(
                        'com.linkedin.common.VectorImage')
                    if logo:
                        item['companyLogoUrl'] = (
                            logo['rootUrl']
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
                if 'logo' in item['school']:
                    item['school']['logoUrl'] = (
                        item['school']
                        ['logo']['com.linkedin.common.VectorImage']['rootUrl']
                    )
                    del item['school']['logo']

        profile['education'] = education

        return profile

    def search(self, params, max_results=None, results=[]):
        """
        Do a search.
        """
        sleep(random.randint(0, 1))  # sleep a random duration to try and evade suspention

        count = (
            max_results
            if max_results and max_results <= _MAX_SEARCH_COUNT
            else _MAX_SEARCH_COUNT
        )
        default_params = {
            'count': count,
            'guides': 'List()',
            'origin': 'GLOBAL_SEARCH_HEADER',
            'q': 'guided',
            'start': len(results),
        }

        default_params.update(params)

        res = self.session.get(
            f'{_API_BASE_URL}/search/cluster',
            params=default_params
        )
        data = res.json()

        total_found = data.get('paging', {}).get('total')
        if total_found == 0 or total_found is None:
            self.logger.debug('found none...')
            return []

        # recursive base case
        if (
            len(data['elements']) == 0 or
            (max_results is not None and len(results) >= max_results) or
            len(results) >= total_found or
            len(results) / max_results >= _MAX_REPEATED_REQUESTS
        ):
            return results

        results.extend(data['elements'][0]['elements'])
        self.logger.debug(f'results grew: {len(results)}')

        return self.search(params, results=results, max_results=max_results)

    def get_profile_connections(self, profile_urn_id):
        """
        Return a list of profile ids connected to profile of given [profile_urn_id]
        """
        return self.search_people(connection_of=profile_urn_id, network_depth='F')

    def search_people(self, keywords=None, connection_of=None, network_depth=None, regions=None, industries=None):
        """
        Do a people search.
        """
        guides = ['v->PEOPLE']
        if connection_of:
            guides.append(f'facetConnectionOf->{connection_of}')
        if network_depth:
            guides.append(f'facetNetwork->{network_depth}')
        if regions:
            guides.append(f'facetGeoRegion->{"|".join(regions)}')
        if industries:
            guides.append(f'facetIndustry->{"|".join(industries)}')

        params = {
            'guides': 'List({})'.format(','.join(guides))
        }

        if keywords:
            params['keywords'] = keywords

        data = self.search(params)

        results = []
        for item in data:
            search_profile = item['hitInfo']['com.linkedin.voyager.search.SearchProfile']
            profile_id = search_profile['id']
            distance = search_profile['distance']['value']

            results.append({
                'profile_urn_id': profile_id,
                'distance': distance,
                'public_profile_id': search_profile['miniProfile']['publicIdentifier']
            })

        return results
