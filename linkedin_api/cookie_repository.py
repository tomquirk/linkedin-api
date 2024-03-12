import logging
import os
import pickle
import time
import linkedin_api.settings as settings

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for other exceptions"""

    pass


class LinkedinSessionExpired(Error):
    pass


class CookieRepository(object):
    """
    Class to act as a repository for the cookies.

    TODO: refactor to use http.cookiejar.FileCookieJar
    """

    def __init__(self, cookies_dir=settings.COOKIE_PATH):
        self.logger = logger
        self.cookies_dir = cookies_dir or settings.COOKIE_PATH

    def save(self, cookies, username):
        self._ensure_cookies_dir()
        cookiejar_filepath = self._get_cookies_filepath(username)
        with open(cookiejar_filepath, "wb") as f:
            pickle.dump(cookies, f)

    def get(self, username, verbose=False):
        cookies = self._load_cookies_from_cache(username)
        if cookies and not self._is_token_still_valid(cookies, verbose=verbose):
            raise LinkedinSessionExpired

        return cookies

    def _ensure_cookies_dir(self):
        if not os.path.exists(self.cookies_dir):
            os.makedirs(self.cookies_dir)

    def _get_cookies_filepath(self, username):
        """
        Return the absolute path of the cookiejar for a given username
        """
        return "{}{}.jr".format(self.cookies_dir, username)

    def _load_cookies_from_cache(self, username):
        cookiejar_filepath = self._get_cookies_filepath(username)
        try:
            with open(cookiejar_filepath, "rb") as f:
                cookies = pickle.load(f)
                return cookies
        except FileNotFoundError:
            return None

    def _is_token_still_valid(self, cookiejar, verbose=False):
        _now = time.time()
        for cookie in cookiejar:
            # As of 2024/03/12, the cookie expiry time is not accurate
            # In practice, it will be expired within one day
            if cookie.name == "JSESSIONID" and cookie.value:
                if verbose:
                    self.logger.debug(
                        f"Cookies JSESSIONID expires at {cookie.expires} while the current time is {_now}")

                if cookie.expires and cookie.expires > _now:
                    return True
                break

        return False
