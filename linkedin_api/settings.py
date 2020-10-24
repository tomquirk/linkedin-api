import os
from pathlib import Path

HOME_DIR = str(Path.home())
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LINKEDIN_API_USER_DIR = os.path.join(HOME_DIR, ".linkedin_api/")
COOKIE_PATH = os.path.join(LINKEDIN_API_USER_DIR, "cookies/")
