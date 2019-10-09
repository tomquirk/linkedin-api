import os
import pickle
import time
import linkedin_api.settings as settings


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

    @staticmethod
    def save(cookies, username):
        CookieRepository._ensure_cookies_dir()
        cookiejar_filepath = CookieRepository._get_cookies_filepath(username)
        with open(cookiejar_filepath, "wb") as f:
            pickle.dump(cookies, f)

    @staticmethod
    def get(username):
        cookies = CookieRepository._load_cookies_from_cache(username)
        if cookies and not CookieRepository._is_token_still_valid(cookies):
            raise LinkedinSessionExpired

        return cookies

    @staticmethod
    def _ensure_cookies_dir():
        if not os.path.exists(settings.COOKIE_PATH):
            os.makedirs(settings.COOKIE_PATH)

    @staticmethod
    def _get_cookies_filepath(username):
        """
        Return the absolute path of the cookiejar for a given username
        """
        return "{}{}.jr".format(settings.COOKIE_PATH, username)

    @staticmethod
    def _load_cookies_from_cache(username):
        cookiejar_filepath = CookieRepository._get_cookies_filepath(username)
        try:
            with open(cookiejar_filepath, "rb") as f:
                cookies = pickle.load(f)
                return cookies
        except FileNotFoundError:
            return None

    @staticmethod
    def _is_token_still_valid(cookiejar):
        _now = time.time()
        for cookie in cookiejar:
            if cookie.name == "JSESSIONID" and cookie.value:
                if cookie.expires and cookie.expires > _now:
                    return True
                break

        return False
