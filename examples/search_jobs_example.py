"""
Example script demonstrating how to search for jobs on LinkedIn
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
    api = Linkedin(TEST_LINKEDIN_USERNAME, TEST_LINKEDIN_PASSWORD, refresh_cookies=True)

    # Example search parameters
    search_params = {
        "keywords": "Python Developer",
        "location_name": "San Francisco Bay Area",
        "remote": ["2"],  # Remote jobs only
        "experience": ["2", "3"],  # Entry level and Associate
        "job_type": ["F", "C"],  # Full-time and Contract
        "limit": 5,
    }

    try:
        # Perform the job search
        jobs = api.search_jobs(**search_params)
        # Process and display results
        print(f"\nFound {len(jobs)} jobs matching your criteria:")

        for job in jobs:
            try:
                # Get detailed job information
                job_id = job["entityUrn"].split(":")[-1]
                details = api.get_job(job_id)

                print("\n-------------------")
                print(f"Title: {details.get('title', 'unknown')}")
                print(
                    f"Company: {details.get('companyDetails', {}).get('name', 'unknown')}"
                )
                print(f"Location: {details.get('formattedLocation', 'unknown')}")
                print(f"Remote? {details.get('workRemoteAllowed', 'unknown')}")
                print(f"Description:  {details.get('description', 'unknown')}")

                # Get job skills if available
                try:
                    skills = api.get_job_skills(job_id)
                    if skills:
                        print("\nRequired Skills:")
                        for skill in skills.get("skillMatchStatuses", []):
                            print(f"- {skill.get('skill', {}).get('name', 'unknown')}")
                except Exception as e:
                    print("Could not fetch skills:", str(e))

                # Cache the job details
                cache_job_data(job_id, details)

                # Respect rate limits
                time.sleep(2)

            except Exception as e:
                print(f"Error processing job {job_id}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error performing job search: {str(e)}")


def cache_job_data(job_id, job_data):
    """Cache job data to a JSON file"""
    try:
        # Create a cache directory if it doesn't exist
        import os

        os.makedirs("cache/jobs", exist_ok=True)

        cache_file = f"cache/jobs/job_{job_id}.json"
        with open(cache_file, "w") as f:
            json.dump(job_data, f, indent=2)
        print(f"Job data cached to {cache_file}")

    except Exception as e:
        print(f"Error caching job data: {str(e)}")


def get_workplace_type_string(type_code):
    """Convert workplace type code to readable string"""
    types = {1: "On-site", 2: "Remote", 3: "Hybrid"}
    return types.get(type_code, "Unknown")


if __name__ == "__main__":
    main()
