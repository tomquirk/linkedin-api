import pytest
import json
import os
from linkedin_api import Linkedin

TEST_PROFILE_ID = "ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzw"
TEST_CONVERSATION_ID = "6419123050314375168"


@pytest.fixture
def linkedin():
    return Linkedin(
        os.environ["LINKEDIN_USERNAME"],
        os.environ["LINKEDIN_PASSWORD"],
        refresh_cookies=True,
    )


def test_get_profile(linkedin):
    profile = linkedin.get_profile(TEST_PROFILE_ID)

    assert profile["summary"] and profile["summary"][0] == "👋"


def test_get_profile_contact_info(linkedin):
    contact_info = linkedin.get_profile_contact_info(TEST_PROFILE_ID)
    assert contact_info


def test_get_profile_connections(linkedin):
    connections = linkedin.get_profile_connections(TEST_PROFILE_ID)
    assert connections


def test_get_conversations(linkedin):
    conversations = linkedin.get_conversations()
    assert conversations


def test_get_conversation_details(linkedin):
    conversation_details = linkedin.get_conversation_details(TEST_PROFILE_ID)
    assert conversation_details


def test_get_conversation(linkedin):
    conversation = linkedin.get_conversation(TEST_CONVERSATION_ID)
    assert conversation


def test_send_message(linkedin):
    err = linkedin.send_message(TEST_CONVERSATION_ID, "test message from pytest")
    assert not err


def test_mark_conversation_as_seen(linkedin):
    err = linkedin.mark_conversation_as_seen(TEST_CONVERSATION_ID)
    assert not err


def test_get_current_profile_views(linkedin):
    views = linkedin.get_current_profile_views()
    assert views >= 0


def test_get_school(linkedin):
    school = linkedin.get_school("university-of-queensland")
    assert school


def test_get_company(linkedin):
    company = linkedin.get_company("linkedin")
    assert company


def test_search(linkedin):
    results = linkedin.search({"keywords": "software"}, 200)
    assert results


def test_search_people(linkedin):
    results = linkedin.search_people(
        keywords="software,lol",
        connection_of="AC000120303",
        network_depth="F",
        regions=["4909"],
        industries=["29", "1"],
    )
    assert results


def test_get_profile_skills(linkedin):
    skills = linkedin.get_profile_skills(TEST_PROFILE_ID)
    assert skills

