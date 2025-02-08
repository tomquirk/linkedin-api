How To Search for Jobs Using the LinkedIn API
========================================

.. note::
    This guide uses the unofficial `linkedin-api <https://github.com/tomquirk/linkedin-api>`_ Python package. While this package provides convenient access to LinkedIn's API, please note that it is not officially supported by LinkedIn.

Introduction
-----------

Programmatically searching for jobs on LinkedIn can help you build job boards, track opportunities, or automate your job search. In this guide, we'll show you how to use the ``search_jobs()`` method to find and filter job listings.

Prerequisites
------------

Before you begin, you'll need:

* Python 3.6 or higher installed on your system
* The ``linkedin-api`` package installed
* LinkedIn account credentials

Step 1 — Setting Up the LinkedIn Client
----------------------------------

First, let's import the library and create a client instance:

.. code-block:: python

    from linkedin_api import Linkedin

    # Initialize the API client
    api = Linkedin('your-email@example.com', 'your-password')

Step 2 — Performing a Basic Job Search
---------------------------------

Let's start with a simple search for Python developer jobs:

.. code-block:: python

    # Search for Python developer jobs
    jobs = api.search_jobs(
        keywords='Python Developer',
        location_name='San Francisco'
    )

    # Process the results
    for job in jobs:
        print(f"Title: {job['title']}")
        print(f"Company: {job['companyName']}")
        print(f"Location: {job['locationName']}")
        print("---")

Step 3 — Adding Advanced Filters
---------------------------

The API supports several useful filters to narrow down your search:

.. code-block:: python

    # Search with multiple filters
    jobs = api.search_jobs(
        keywords='Data Scientist',
        remote=['2'],              # Remote jobs only
        experience=['2', '3'],   # Entry level and Associate
        job_type=['F', 'C'],    # Full-time and Contract
        location_name='London',
        limit=5
    )

Understanding Search Parameters
--------------------------

Here's what each filter does:

* **experience**: Experience level required
    * '1' = Internship
    * '2' = Entry level
    * '3' = Associate
    * '4' = Mid-Senior
    * '5' = Director
    * '6' = Executive

* **remote**: Work location type
    * 1 = On-site
    * 2 = Remote
    * 3 = Hybrid

* **job_type**: Employment type
    * 'F' = Full-time
    * 'P' = Part-time
    * 'C' = Contract
    * 'T' = Temporary
    * 'I' = Internship
    * 'V' = Volunteer

Handling the Results
----------------

Let's look at how to process and analyze the search results:

.. code-block:: python

    # Get detailed job information
    for job in jobs:
        # Extract key information
        job_id = job['entityUrn'].split(':')[-1]
        
        # Get full job details
        details = api.get_job(job_id)
        
        print(f"Title: {details.get('title', 'unknown')}")
        print(f"Company: {details.get('companyDetails', {}).get('name', 'unknown')}")
        print(f"Location: {details.get('formattedLocation', 'unknown')}")
        print(f"Remote? {details.get('workRemoteAllowed', 'unknown')}")
        print(f"Description: {details.get('description', 'unknown')}")
        
        # Get job skills
        skills = api.get_job_skills(job_id)
        if skills:
            print("\nRequired Skills:")
            for skill in skills.get('skillMatchStatuses', []):
                print(f"- {skill.get('skill', {}).get('name', 'unknown')}")
        print("---")

Troubleshooting Common Issues
-------------------------

Here are some common issues you might encounter:

* **No Results**: Try broadening your search terms or removing some filters
* **Rate Limiting**: LinkedIn limits how many searches you can perform
* **Missing Fields**: Some job listings might not include all fields

Best Practices and Tips
--------------------

1. **Optimize Your Search Terms**:

   .. code-block:: python

       # Use multiple related keywords
       jobs = api.search_jobs(
           keywords='(Python OR Django) AND (Backend OR "Back End")'
       )

2. **Handle Pagination**:

   .. code-block:: python

       # Get more results using offset
       all_jobs = []
       offset = 0
       while True:
           jobs = api.search_jobs(keywords='Developer', offset=offset)
           if not jobs:
               break
           all_jobs.extend(jobs)
           offset += len(jobs)

3. **Cache Results**: Save job data locally to avoid repeated API calls

Conclusion
---------

You now know how to search for jobs using the LinkedIn API. This functionality is perfect for building job tracking applications, automated job search tools, or market research applications.

For more advanced usage, check out our other guides on company information and job analytics.

Get the complete example source code here: https://github.com/tomquirk/linkedin-api/tree/main/examples/search_jobs_example.py 