import requests
import pickle
import logging
import os

import linkedin_api.settings as settings

logger = logging.getLogger(__name__)


class Client(object):
    """
    Class to act as a client for the Linkedin API.
    """

    # Settings for general Linkedin API calls
    API_BASE_URL = "https://www.linkedin.com/voyager/api"
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) \
                        AppleWebKit/537.36 (KHTML, like Gecko) \
                        Chrome/66.0.3359.181 Safari/537.36"
    }

    # Settings for authenticating with Linkedin
    AUTH_BASE_URL = "https://www.linkedin.com"
    AUTH_REQUEST_HEADERS = {
        "X-Li-User-Agent": "LIAuthLibrary:3.2.4 \
                            com.linkedin.LinkedIn:8.8.1 \
                            iPhone:8.3",
        "User-Agent": "LinkedIn/8.8.1 CFNetwork/711.3.18 Darwin/14.0.0",
        "X-User-Language": "en",
        "X-User-Locale": "en_US",
        "Accept-Language": "en-us",
    }

    def __init__(self, debug=False):
        self.session = requests.session()
        self.session.headers = Client.REQUEST_HEADERS

        self.logger = logger
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    def _request_session_cookies(self):
        """
        Return a new set of session cookies as given by Linkedin.
        """
        try:
            with open(settings.COOKIE_FILE_PATH, "rb") as f:
                cookies = pickle.load(f)
                if cookies:
                    return cookies
        except FileNotFoundError:
            self.logger.debug("Cookie file not found. Requesting new cookies.")
            os.mkdir("tmp")
            pass

        res = requests.get(f"{Client._AUTH_BASE_URL}/uas/authenticate", headers=Client.AUTH_REQUEST_HEADERS)

        return res.cookies

    def _set_session_cookies(self, cookiejar):
        """
        Set cookies of the current session and save them to a file.
        """
        self.session.cookies = cookiejar
        self.session.headers["csrf-token"] = self.session.cookies["JSESSIONID"].strip('"')
        with open(settings.COOKIE_FILE_PATH, "wb") as f:
            pickle.dump(cookiejar, f)

    def authenticate(self, username, password):
        """
        Authenticate with Linkedin.

        Return a session object that is authenticated.
        """
        self._set_session_cookies(self._request_session_cookies())

        payload = {
            "session_key": username,
            "session_password": password,
            "JSESSIONID": self.session.cookies["JSESSIONID"],
        }

        res = requests.post(
            f"{Client.AUTH_BASE_URL}/uas/authenticate",
            data=payload,
            cookies=self.session.cookies,
            headers=Client.AUTH_REQUEST_HEADERS,
        )

        data = res.json()

        # TODO raise better exceptions
        if res.status_code != 200:
            raise Exception()
        elif data["login_result"] != "PASS":
            raise Exception()

        self._set_session_cookies(res.cookies)
