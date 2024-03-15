import os
import sys
import pytest

from linkedin_api import Linkedin
from linkedin_api.utils.helpers import get_id_from_urn

TEST_LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
TEST_LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
TEST_PROFILE_ID = os.getenv("TEST_PROFILE_ID")
TEST_PUBLIC_PROFILE_ID = os.getenv("TEST_PUBLIC_PROFILE_ID")
TEST_CONVERSATION_ID = os.getenv("TEST_CONVERSATION_ID")

if not (
    TEST_LINKEDIN_USERNAME
    and TEST_LINKEDIN_PASSWORD
    and TEST_PROFILE_ID
    and TEST_PUBLIC_PROFILE_ID
    and TEST_CONVERSATION_ID
):
    print("Test config incomplete. Exiting...")
    sys.exit()


@pytest.fixture(scope="module")
def linkedin():
    return Linkedin(
        TEST_LINKEDIN_USERNAME, TEST_LINKEDIN_PASSWORD, refresh_cookies=True
    )


def test_get_profile(linkedin):
    profile = linkedin.get_profile(urn_id=TEST_PROFILE_ID)

    assert profile


def test_get_profile_privacy_settings(linkedin):
    data = linkedin.get_profile_privacy_settings(TEST_PUBLIC_PROFILE_ID)

    assert data


def test_get_profile_member_badges(linkedin):
    data = linkedin.get_profile_member_badges(TEST_PUBLIC_PROFILE_ID)

    assert data


def test_get_profile_network_info(linkedin):
    data = linkedin.get_profile_network_info(TEST_PUBLIC_PROFILE_ID)

    assert data


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
    results = linkedin.search(
        {"keywords": "software"},
        limit=10,  # arbitrary limit to stop test taking too long
    )
    assert results


@pytest.mark.skip(reason="Limit is broken")
def test_search_pagination(linkedin):
    results = linkedin.search({"keywords": "software"}, limit=4)
    # according to implementation of functions search_people, search_companies
    # limit is valid within the category only. So in every category/type of test
    # the number of results shall not exceed a given limit
    numbers_in_categories = {}
    for result in results:
        try:
            occurrence = numbers_in_categories[result["_type"]]
        except KeyError:
            occurrence = 0
            numbers_in_categories.update({result["_type"]: occurrence})
        occurrence += 1
        numbers_in_categories[result["_type"]] = occurrence
    assert results
    assert max(numbers_in_categories.values()) == 4


@pytest.mark.skip(reason="Limit is broken")
def test_search_with_limit(linkedin):
    results = linkedin.search({"keywords": "tom"}, limit=1)
    assert len(results) == 1


def test_search_people(linkedin):
    results = linkedin.search_people(
        keywords="software",
        include_private_profiles=True,
        limit=10,  # arbitrary limit to stop test taking too long
    )
    assert results


@pytest.mark.skip(reason="Limit is broken")
def test_search_people_with_limit(linkedin):
    results = linkedin.search_people(
        keywords="software", include_private_profiles=True, limit=1
    )
    assert results
    assert len(results) == 1


def test_search_people_by_region(linkedin):
    results = linkedin.search_people(
        keywords="software",
        include_private_profiles=True,
        regions=["105080838"],
        limit=10,  # arbitrary limit to stop test taking too long
    )
    assert results


def test_search_people_by_keywords_filter(linkedin: Linkedin):
    results = linkedin.search_people(
        keyword_first_name="John",
        keyword_last_name="Smith",
        include_private_profiles=True,
        limit=10,  # arbitrary limit to stop test taking too long
    )
    assert results


def test_search_jobs(linkedin):
    # test all filters for correct syntax
    # location_name -> "san francisco"
    # companies -> google="1441" or apple="162479"
    # experience ->"1", "2", "3", "4", "5" and "6" (internship, entry level, associate, mid-senior level, director and executive, respectively)
    # job_type -> "F", "C", "P", "T", "I", "V", "O" (full-time, contract, part-time, temporary, internship, volunteer and "other", respectively)
    # job_title -> software_eng="9",cloud_eng="30006"
    # industries -> computer_hardware="24", it_technology="6"
    # distance -> big number 1000 miles
    # remote -> onsite:"1", remote:"2", hybrid:"3"
    # listed_at -> large number 1000000 seconds
    jobs = linkedin.search_jobs(
        keywords="software engineer",
        location_name="San Francisco",
        companies=["1441", "162479"],
        experience=["1", "2", "3", "4", "5", "6"],
        job_type=["F", "C", "P", "T", "I", "V", "O"],
        job_title=["9", "30006"],
        industries=["24", "6"],
        distance=1000,
        remote=["1", "2", "3"],
        listed_at=1000000,
        limit=10,
    )
    assert jobs

    # Test that no results doesn't return an infinite loop
    jobs = linkedin.search_jobs(keywords="blurp", location_name="antarctica")
    assert len(jobs) == 0


def test_get_job(linkedin):
    jobs = linkedin.search_jobs(keywords="software engineer", limit=1)
    job_id = get_id_from_urn(jobs[0]["trackingUrn"])
    job_info = linkedin.get_job(job_id)
    assert job_info


def test_search_companies(linkedin):
    results = linkedin.search_companies(keywords="linkedin", limit=1)
    assert results
    assert results[0]["urn_id"] == "1337"


def test_search_people_distinct(linkedin):
    TEST_NAMES = ["Bill Gates", "Mark Zuckerberg"]
    results = [linkedin.search_people(name, limit=2)[0] for name in TEST_NAMES]
    assert results[0] != results[1]


def test_get_profile_skills(linkedin):
    skills = linkedin.get_profile_skills(TEST_PROFILE_ID)
    assert skills


def test_get_invitiations(linkedin):
    invitations = linkedin.get_invitations()
    assert len(invitations) >= 0


def test_accept_invitation(linkedin):
    """
    NOTE: this test relies on the existence of invitations. If you'd like to test this
    functionality, make sure the test account has at least 1 invitation.
    """
    invitations = linkedin.get_invitations()
    if not invitations:
        # If we've got no invitations, just force test to pass
        assert True
        return
    num_invitations = len(invitations)
    invite = invitations[0]
    invitation_response = linkedin.reply_invitation(
        invitation_entity_urn=invite["entityUrn"],
        invitation_shared_secret=invite["sharedSecret"],
        action="accept",
    )
    assert invitation_response

    invitations = linkedin.get_invitations()
    assert len(invitations) == num_invitations - 1


def test_reject_invitation(linkedin):
    """
    NOTE: this test relies on the existence of invitations. If you'd like to test this
    functionality, make sure the test account has at least 1 invitation.
    """
    invitations = linkedin.get_invitations()
    if not invitations:
        # If we've got no invitations, just force test to pass
        assert True
        return
    num_invitations = len(invitations)
    invite = invitations[0]
    invitation_response = linkedin.reply_invitation(
        invitation_entity_urn=invite["entityUrn"],
        invitation_shared_secret=invite["sharedSecret"],
        action="reject",
    )
    assert invitation_response

    invitations = linkedin.get_invitations()
    assert len(invitations) == num_invitations - 1


def test_unfollow_entity(linkedin):
    urn = f"urn:li:member:ACoAACVmHBkBdk3IYY1uodl8Ht4W79rmdVFccOA"
    err = linkedin.unfollow_entity(urn)
    assert not err


def test_get_feed_posts_pagination(linkedin):
    results = linkedin.get_feed_posts(101)
    assert results


def test_get_feed_posts_pagination_with_limit(linkedin):
    results = linkedin.get_feed_posts(4)
    # Currently promotions are always removed from results
    assert len(results) <= 4


def test_get_feed_posts_posts_keys(linkedin):
    results = linkedin.get_feed_posts(4)
    for i in results:
        assert i["author_name"]
        assert i["author_profile"]
        assert i["content"]
        assert i["old"]
        assert i["url"]


def test_get_feed_posts_urns_contains_no_duplicated(linkedin):
    l_posts, l_urns = linkedin._get_list_feed_posts_and_list_feed_urns(101)
    assert len(set([x for x in l_urns if l_urns.count(x) > 1])) == 0
