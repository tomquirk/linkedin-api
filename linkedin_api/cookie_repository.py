import os
import pickle
import time
import logging
import linkedin_api.settings as settings

logger = logging.getLogger(__name__)


class CookieRepository(object):
    """
        Class to act as a repository for the cookies.
    """

    def __init__(self, debug=False):
        if not os.path.exists(settings.COOKIE_PATH):
            os.makedirs(settings.COOKIE_PATH)
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)


    def save(self, cookies, username):
        try:
            cookiejar_file = self._get_cookiejar_file(username)
            with open(cookiejar_file, "wb") as f:
                pickle.dump(cookies, f)
        except Exception:
            self.logger.debug("Cookie file could not be saved.")

    def get(self, username):
        cookies = self._load_cookies_from_cache(username)
        if cookies and self._is_token_still_valid(cookies):
            return cookies
        else:
            return None

    def _get_cookiejar_file(self, username):
        """
        Return the absolute path of the cookiejar for a given username
        """
        return "{}{}.jr".format(settings.COOKIE_PATH, username)

    def _load_cookies_from_cache(self, username):
        try:
            cookiejar_file = self._get_cookiejar_file(username)
            with open(cookiejar_file, "rb") as f:
                cookies = pickle.load(f)
                return cookies

        except Exception:
            self.logger.debug("Cookie file could not be retrieved.")
            return None

    def _is_token_still_valid(self, cookies):
        _now = time.time()
        for cookie in cookies:
            if cookie.name == "JSESSIONID" and cookie.value:
                if cookie.expires and cookie.expires > _now:
                    return True
                break

        return False
