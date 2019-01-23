import pytest
import json
import os
from linkedin_api import Linkedin


@pytest.fixture
def linkedin():
    return Linkedin(os.environ["LINKEDIN_USERNAME"], os.environ["LINKEDIN_PASSWORD"])


def test_get_profile(linkedin):
    profile = linkedin.get_profile("ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw")

    assert profile["summary"] and profile["summary"][0] == "👋"
