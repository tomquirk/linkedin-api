import os
import sys
import pytest
import requests
from datetime import datetime

from linkedin_api.cookie_repository import (
    CookieRepository,
    LinkedinSessionExpired,
)


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
    repo = CookieRepository()
    repo.save(mock_cookies(), "testuser")
    assert True


def test_get():
    repo = CookieRepository()
    c = repo.get("testuser")
    assert c is not None
    assert c == mock_cookies()


def test_get_nonexistent_file():
    repo = CookieRepository()
    c = repo.get("ghost")
    assert c is None


def test_get_expired():
    repo = CookieRepository()
    repo.save(
        mock_cookies(date=datetime.strptime("2001-05-04", "%Y-%m-%d")), "testuserex"
    )
    try:
        repo.get("testuserex")
        assert False
    except LinkedinSessionExpired:
        assert True
