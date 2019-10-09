import os
import sys
import pytest
import requests
from datetime import datetime

from linkedin_api.cookie_repository import CookieRepository, LinkedinSessionExpired


def mock_cookies(date=datetime.strptime("2050-05-04", "%Y-%m-%d")):
    jar = requests.cookies.RequestsCookieJar()
    jar.set(
        "JSESSIONID",
        "1234",
        expires=date.timestamp(),
        domain="httpbin.org",
        path="/cookies",
    )
    return jar


def test_save():
    CookieRepository.save(mock_cookies(), "testuser")
    assert True


def test_get():
    c = CookieRepository.get("testuser")
    assert c is not None
    assert c == mock_cookies()


def test_get_nonexistent_file():
    c = CookieRepository.get("ghost")
    assert c is None


def test_get_expired():
    CookieRepository.save(
        mock_cookies(date=datetime.strptime("2001-05-04", "%Y-%m-%d")), "testuserex"
    )
    try:
        CookieRepository.get("testuserex")
        assert False
    except LinkedinSessionExpired:
        assert True
