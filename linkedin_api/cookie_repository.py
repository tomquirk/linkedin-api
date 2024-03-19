from datetime import datetime
import logging
import os
import pickle
import time
import linkedin_api.settings as settings
from linkedin_api.utils.time import get_time_string

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

    def _save(self, cookies, username, raw_time_suffix=None):
        self._ensure_cookies_dir()
        cookiejar_filepath = self._get_cookies_filepath(
            username, raw_time_suffix)
        with open(cookiejar_filepath, "wb") as f:
            pickle.dump(cookies, f)

    def save(self, cookies, username, raw_time_suffix=None):
        self._ensure_cookies_dir()
        cookiejar_filepath = self._get_cookies_filepath(
            username, raw_time_suffix)
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

    def _get_cookies_filepath(self, username, raw_time_suffix=None):
        """
        Return the absolute path of the cookiejar for a given username
        """
        return f"{self.cookies_dir}{username}-{get_time_string(raw_time_suffix, separator='_')}.jr" if raw_time_suffix else f"{self.cookies_dir}{username}.jr"

    def _load_cookies_from_cache(self, username, raw_time_suffix=None):
        cookiejar_filepath = self._get_cookies_filepath(
            username, raw_time_suffix)
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
