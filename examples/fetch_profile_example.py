"""
Example script demonstrating how to fetch LinkedIn profiles
"""

import json
import time
from linkedin_api import Linkedin
import os
import sys

TEST_LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
TEST_LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")


def main():
    if not (TEST_LINKEDIN_USERNAME and TEST_LINKEDIN_PASSWORD):
        print("Test config incomplete. Exiting...")
        sys.exit()

    # Initialize the API client
    # Replace with your LinkedIn credentials
    api = Linkedin(TEST_LINKEDIN_USERNAME, TEST_LINKEDIN_PASSWORD, refresh_cookies=True)

    # Example profile IDs to fetch
    profile_ids = ["stephencurry30"]

    for profile_id in profile_ids:
        try:
            # Get profile using public ID
            profile = api.get_profile(public_id=profile_id)

            # Print basic information
            print("\nBasic Information:")
            print(f"Name: {profile['firstName']} {profile['lastName']}")
            print(f"Headline: {profile.get('headline', 'No headline')}")
            print(f"Location: {profile.get('locationName', 'No location')}")

            # Print work experience
            print("\nWork Experience:")
            for job in profile.get("experience", []):
                print(f"- {job.get('companyName')}: {job.get('title')}")

            # Print education
            print("\nEducation:")
            for school in profile.get("education", []):
                print(f"- {school.get('schoolName')}: {school.get('degreeName')}")

            # Cache the profile data
            cache_profile_data(profile_id, profile)

            # Respect rate limits
            time.sleep(2)

        except Exception as e:
            print(f"Error fetching profile {profile_id}: {str(e)}")


def cache_profile_data(profile_id, profile_data):
    """Cache profile data to a JSON file"""
    try:
        # Create a cache directory if it doesn't exist
        import os

        os.makedirs("cache", exist_ok=True)

        cache_file = f"cache/profile_{profile_id}.json"
        with open(cache_file, "w") as f:
            json.dump(profile_data, f, indent=2)
        print(f"\nProfile data cached to {cache_file}")

    except Exception as e:
        print(f"Error caching profile data: {str(e)}")


def safely_access_nested_data(profile, *keys, default=None):
    """Safely access nested dictionary data"""
    try:
        value = profile
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError, IndexError):
        return default


if __name__ == "__main__":
    main()
