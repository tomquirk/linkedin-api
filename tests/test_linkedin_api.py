import pytest
import json
import os
from linkedin_api import Linkedin

TEST_PROFILE_ID = os.environ["TEST_PROFILE_ID"]
TEST_CONVERSATION_ID = os.environ["TEST_CONVERSATION_ID"]
TEST_INVITATION_ID = os.environ["TEST_INVITATION_ID"]
TEST_INVITATION_SHARED_SECRET = os.environ["TEST_INVITATION_SHARED_SECRET"]

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


def test_send_message_to_conversation(linkedin):
    err = linkedin.send_message(
        conversation_urn_id=TEST_CONVERSATION_ID,
        message_body="test message from pytest",
    )
    assert not err


def test_send_message_to_recipients(linkedin):
    err = linkedin.send_message(
        recipients=[TEST_PROFILE_ID], message_body="test message from pytest"
    )
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
    assert school["name"] == "The University of Queensland"


def test_get_company(linkedin):
    company = linkedin.get_company("linkedin")
    assert company
    assert company["name"] == "LinkedIn"


def test_search(linkedin):
    results = linkedin.search({"keywords": "software"})
    assert results


def test_search_with_limit(linkedin):
    results = linkedin.search({"keywords": "tom"}, limit=1)
    assert len(results) == 1


def test_search_people(linkedin):
    results = linkedin.search_people(keywords="software")
    assert results
    assert results[0]["public_id"]


def test_search_people_with_limit(linkedin):
    results = linkedin.search_people(keywords="software", limit=1)
    assert results
    assert len(results) == 1


def test_get_profile_skills(linkedin):
    skills = linkedin.get_profile_skills(TEST_PROFILE_ID)
    assert skills

def test_get_invitations(linkedin):
    invitations = linkedin.get_invitations()
    assert len(invitations) >= 0

def test_reply_invitation(linkedin):
    accept_response = linkedin.reply_invitation(
        TEST_INVITATION_ID,
        TEST_INVITATION_SHARED_SECRET,
        "accept"
    )
    assert accept_response
