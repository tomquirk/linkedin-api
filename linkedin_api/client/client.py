import json
import random
from time import sleep
import requests
import logging
from linkedin_api.client.cookie_repository import CookieRepository
from bs4 import BeautifulSoup, Tag
from requests.cookies import RequestsCookieJar
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class ChallengeException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


def default_evade():
    """
    A catch-all method to try and evade suspension from Linkedin.
    Currenly, just delays the request by a random (bounded) time
    """
    sleep(random.randint(2, 5))  # sleep a random duration to try and evade suspention


class Client(object):
    """
    Class to act as a client for the Linkedin API.
    """

    # Settings for general Linkedin API calls
    LINKEDIN_BASE_URL = "https://www.linkedin.com"
    API_BASE_URL = f"{LINKEDIN_BASE_URL}/voyager/api"
    REQUEST_HEADERS = {
        "user-agent": " ".join(
            [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5)",
                "AppleWebKit/537.36 (KHTML, like Gecko)",
                "Chrome/83.0.4103.116 Safari/537.36",
            ]
        ),
        "accept-language": "en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "x-li-lang": "en_US",
        "x-restli-protocol-version": "2.0.0",
    }

    # Settings for authenticating with Linkedin
    AUTH_REQUEST_HEADERS = {
        "X-Li-User-Agent": "LIAuthLibrary:0.0.3 com.linkedin.android:4.1.881 Asus_ASUS_Z01QD:android_9",
        "User-Agent": "ANDROID OS",
        "X-User-Language": "en",
        "X-User-Locale": "en_US",
        "Accept-Language": "en-us",
    }

    def __init__(
        self, *, debug=False, refresh_cookies=False, proxies={}, cookies_dir: str = ""
    ):
        self.session = requests.session()
        self.session.proxies.update(proxies)
        self.session.headers.update(Client.REQUEST_HEADERS)
        self.proxies = proxies
        self.logger = logger
        self.metadata = {}

        self._use_cookie_cache = not refresh_cookies
        self._cookie_repository = CookieRepository(cookies_dir=cookies_dir)

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    @property
    def cookies(self) -> RequestsCookieJar:
        return self.session.cookies

    @cookies.setter
    def cookies(self, cookies: RequestsCookieJar):
        """
        Set cookies of the current session and save them to a file named as the username.
        """
        self.session.cookies = cookies
        self.session.headers["csrf-token"] = self.session.cookies["JSESSIONID"].strip(
            '"'
        )

    def get(self, uri: str, evade=default_evade, base_request=False, **kwargs):
        """GET request to Linkedin API"""
        evade()

        url = (
            f"{self.API_BASE_URL if not base_request else self.LINKEDIN_BASE_URL}{uri}"
        )
        return self.session.get(url, **kwargs)

    def get_graphql(
        self,
        variables: dict,
        query_id: str | None = None,
        query: str | None = None,
        **kwargs,
    ):
        """GET request to Linkedin API GraphQL endpoint"""

        variables_list = [f"{k}:{v}" for k, v in variables.items()]
        variables_payload = f"({','.join(variables_list)})"

        payload = {
            "variables": variables_payload,
        }
        if query_id:
            payload["queryId"] = query_id
        if query:
            payload["query"] = query
        params = urlencode(payload, safe=":+()")

        return self.get(f"/graphql", params=params, **kwargs)

    def post(self, uri: str, evade=default_evade, base_request=False, **kwargs):
        """POST request to Linkedin API"""
        evade()

        url = (
            f"{self.API_BASE_URL if not base_request else self.LINKEDIN_BASE_URL}{uri}"
        )
        return self.session.post(url, **kwargs)

    def authenticate(self, username: str, password: str):
        if self._use_cookie_cache:
            self.logger.debug("Attempting to use cached cookies")
            cookies = self._cookie_repository.get(username)
            if cookies:
                self.logger.debug("Using cached cookies")
                self.cookies = cookies
                self._fetch_metadata()
                return

        self._do_authentication_request(username, password)
        self._fetch_metadata()

    def _request_session_cookies(self):
        """
        Return a new set of session cookies as given by Linkedin.
        """
        self.logger.debug("Requesting new cookies.")

        res = requests.get(
            f"{Client.LINKEDIN_BASE_URL}/uas/authenticate",
            headers=Client.AUTH_REQUEST_HEADERS,
            proxies=self.proxies,
        )
        return res.cookies

    def _fetch_metadata(self):
        """
        Get metadata about the "instance" of the LinkedIn application for the signed in user.

        Store this data in self.metadata
        """
        res = requests.get(
            f"{Client.LINKEDIN_BASE_URL}",
            cookies=self.session.cookies,
            headers=Client.AUTH_REQUEST_HEADERS,
            proxies=self.proxies,
        )

        soup = BeautifulSoup(res.text, "lxml")

        clientApplicationInstanceRaw = soup.find(
            "meta", attrs={"name": "applicationInstance"}
        )
        if clientApplicationInstanceRaw and isinstance(
            clientApplicationInstanceRaw, Tag
        ):
            clientApplicationInstanceRaw = clientApplicationInstanceRaw.attrs.get(
                "content", {}
            )
            clientApplicationInstance = json.loads(clientApplicationInstanceRaw)
            self.metadata["clientApplicationInstance"] = clientApplicationInstance

        clientPageInstanceIdRaw = soup.find(
            "meta", attrs={"name": "clientPageInstanceId"}
        )
        if clientPageInstanceIdRaw and isinstance(clientPageInstanceIdRaw, Tag):
            clientPageInstanceId = clientPageInstanceIdRaw.attrs.get("content", {})
            self.metadata["clientPageInstanceId"] = clientPageInstanceId

    def _do_authentication_request(self, username: str, password: str):
        """
        Authenticate with Linkedin.

        Return a session object that is authenticated.
        """
        self.cookies = self._request_session_cookies()

        payload = {
            "session_key": username,
            "session_password": password,
            "JSESSIONID": self.session.cookies["JSESSIONID"],
        }

        res = requests.post(
            f"{Client.LINKEDIN_BASE_URL}/uas/authenticate",
            data=payload,
            cookies=self.session.cookies,
            headers=Client.AUTH_REQUEST_HEADERS,
            proxies=self.proxies,
        )

        data = res.json()

        if data and data["login_result"] != "PASS":
            raise ChallengeException(data["login_result"])
        if res.status_code == 401:
            raise UnauthorizedException()
        if res.status_code != 200:
            raise Exception()

        self.cookies = res.cookies
        self._cookie_repository.save(res.cookies, username)
