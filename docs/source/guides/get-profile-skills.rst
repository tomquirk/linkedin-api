How To Get Profile Skills Using the LinkedIn API
=========================================

.. note::
    This guide uses the unofficial `linkedin-api <https://github.com/tomquirk/linkedin-api>`_ Python package. While this package provides convenient access to LinkedIn's API, please note that it is not officially supported by LinkedIn.

Introduction
-----------

Analyzing professional skills can be valuable for recruitment, skill gap analysis, or professional development tracking. In this guide, we'll show you how to use the ``get_profile_skills()`` method to extract and analyze skills from LinkedIn profiles.

Prerequisites
------------

Before you begin, you'll need:

* Python 3.6 or higher installed on your system
* The ``linkedin-api`` package installed
* LinkedIn account credentials
* Profile public IDs or URNs to analyze

Step 1 — Setting Up the LinkedIn Client
----------------------------------

First, let's import the library and create a client instance:

.. code-block:: python

    from linkedin_api import Linkedin

    # Initialize the API client
    api = Linkedin('your-email@example.com', 'your-password')

Step 2 — Fetching Profile Skills
--------------------------

Let's retrieve the skills for a specific profile:

.. code-block:: python

    # Get skills using public profile ID
    skills = api.get_profile_skills(public_id='john-doe')

    # Print each skill and its endorsement count
    for skill in skills:
        print(f"Skill: {skill['name']}")
        print(f"Endorsements: {skill.get('endorsementCount', 0)}")
        print("---")

Step 3 — Analyzing Skills Data
------------------------

Here's how to process and analyze the skills data:

.. code-block:: python

    from collections import Counter

    def analyze_skills(skills_data):
        # Count endorsements per skill
        endorsements = {
            skill['name']: skill.get('endorsementCount', 0)
            for skill in skills_data
        }
        
        # Sort skills by endorsement count
        top_skills = sorted(
            endorsements.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Group skills by category
        categories = {}
        for skill in skills_data:
            category = skill.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(skill['name'])
            
        return {
            'top_skills': top_skills[:10],
            'skill_categories': categories
        }

Understanding Skills Data
--------------------

The skills data includes:

* **Skill Name**: The primary skill identifier
* **Endorsement Count**: Number of endorsements received
* **Category**: Skill category or type
* **Endorsers**: Information about who endorsed the skill

Working with Multiple Profiles
-------------------------

Here's how to analyze skills across multiple profiles:

.. code-block:: python

    def compare_skills(api, profile_ids):
        all_skills = {}
        
        for profile_id in profile_ids:
            skills = api.get_profile_skills(public_id=profile_id)
            all_skills[profile_id] = {
                skill['name']: skill.get('endorsementCount', 0)
                for skill in skills
            }
            
        # Find common skills
        common_skills = set.intersection(*[
            set(skills.keys()) 
            for skills in all_skills.values()
        ])
        
        return {
            'all_skills': all_skills,
            'common_skills': common_skills
        }

Troubleshooting Common Issues
-------------------------

Here are some common issues you might encounter:

* **Profile Not Found**: Verify the profile ID or URN
* **No Skills Listed**: Profile might have hidden skills
* **Rate Limiting**: LinkedIn limits API requests
* **Incomplete Data**: Some skills might lack endorsement counts

Best Practices and Tips
--------------------

1. **Standardize Skill Names**:

   .. code-block:: python

       def standardize_skill_names(skills):
           # Common variations mapping
           variations = {
               'javascript': ['js', 'java script', 'java-script'],
               'python': ['python3', 'python 3', 'python programming'],
               # Add more variations as needed
           }
           
           standardized = []
           for skill in skills:
               name = skill['name'].lower()
               for standard, variants in variations.items():
                   if name in variants:
                       skill['name'] = standard
                       break
               standardized.append(skill)
               
           return standardized

2. **Cache Skills Data**:

   .. code-block:: python

       import json
       from datetime import datetime

       def cache_skills(profile_id, skills, cache_file='skills_cache.json'):
           try:
               with open(cache_file, 'r') as f:
                   cache = json.load(f)
           except FileNotFoundError:
               cache = {}
               
           cache[profile_id] = {
               'skills': skills,
               'timestamp': datetime.now().isoformat()
           }
           
           with open(cache_file, 'w') as f:
               json.dump(cache, f)

3. **Best Practices for Skills Analysis**:
   * Group similar skills together
   * Consider endorsement counts for skill relevance
   * Update cached data regularly
   * Handle missing or incomplete data gracefully

Conclusion
---------

You now know how to fetch and analyze profile skills using the LinkedIn API. This functionality is perfect for building talent assessment tools, skill gap analysis systems, or professional development applications.

For more advanced usage, check out our other guides on profile analysis and recruitment tools. 