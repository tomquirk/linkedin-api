import pytest
import json
import os
import sys
from linkedin_api.client import Client

from dotenv import load_dotenv

load_dotenv()

TEST_LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
TEST_LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

if not (TEST_LINKEDIN_USERNAME and TEST_LINKEDIN_PASSWORD):
    print("Test config incomplete. Exiting...")
    sys.exit()


@pytest.fixture
def client():
    return Client()


def test_authenticate(client):
    client.authenticate(TEST_LINKEDIN_USERNAME, TEST_LINKEDIN_USERNAME)

    assert client.session.cookies
