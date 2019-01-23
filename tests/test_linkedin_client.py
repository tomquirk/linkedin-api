import pytest
import json
import os
from linkedin_api.client import Client


@pytest.fixture
def client():
    return Client()


def test_authenticate(client):
    client.authenticate(
        os.environ["LINKEDIN_USERNAME"], os.environ["LINKEDIN_PASSWORD"]
    )

    assert client.session.cookies
