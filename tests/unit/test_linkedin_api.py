import os
import sys
import pytest

from linkedin_api import Linkedin


def test_constructor():
    api = Linkedin("test", "test", authenticate=False)
    assert api
