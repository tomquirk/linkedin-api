How To Search for People Using the LinkedIn API
=========================================

.. note::
    This guide uses the unofficial `linkedin-api <https://github.com/tomquirk/linkedin-api>`_ Python package. While this package provides convenient access to LinkedIn's API, please note that it is not officially supported by LinkedIn.

Introduction
-----------

Finding and analyzing LinkedIn profiles programmatically can be valuable for recruitment, networking, or market research. In this guide, we'll show you how to use the ``search_people()`` method to find LinkedIn users based on various criteria.

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

Step 2 — Performing a Basic People Search
-----------------------------------

Let's start with a simple search for software engineers:

.. code-block:: python

    # Search for software engineers at Google
    people = api.search_people(
        keyword_title="Software Engineer",
        keyword_company="Google"
    )

    # Process the results
    for person in people:
        print(f"Name: {person['name']}")
        print(f"Title: {person['jobtitle']}")
        print(f"Location: {person['location']}")
        print("---")

Step 3 — Using Advanced Search Filters
--------------------------------

The API supports several powerful filters to narrow your search:

.. code-block:: python

    # Advanced search with multiple filters
    people = api.search_people(
        keywords="Machine Learning",
        network_depths=["F", "S"],  # First and second connections
        current_company=["1441", "1035"],  # Company IDs
        profile_languages=["en", "es"],
        regions=["us:0", "gb:0"]  # US and UK
    )

Understanding Search Parameters
--------------------------

Here are the key search parameters:

* **Network Depth**
    * 'F' = 1st connections
    * 'S' = 2nd connections
    * 'O' = 3rd+ connections

* **Keyword Filters**
    * ``keyword_first_name``: First name
    * ``keyword_last_name``: Last name
    * ``keyword_title``: Job title
    * ``keyword_company``: Company name
    * ``keyword_school``: School name

* **Other Filters**
    * ``current_company``: List of company IDs
    * ``past_companies``: List of previous employers
    * ``nonprofit_interests``: Volunteer interests
    * ``regions``: Geographic locations
    * ``industries``: Industry codes

Processing Search Results
---------------------

Let's look at how to handle the search results:

.. code-block:: python

    # Get detailed information for each person
    for person in people:
        # Get full profile data
        if person.get('public_id'):
            profile = api.get_profile(public_id=person['public_id'])
            
            # Get contact information
            contact_info = api.get_profile_contact_info(
                public_id=person['public_id']
            )
            
            print(f"Name: {profile['firstName']} {profile['lastName']}")
            print(f"Email: {contact_info.get('email_address')}")
            print("---")

Troubleshooting Common Issues
-------------------------

Here are some common issues you might encounter:

* **No Results**: Try broadening your search criteria
* **Rate Limiting**: LinkedIn limits search requests
* **Private Profiles**: Some profiles may be hidden
* **Missing Data**: Not all fields are available for every profile

Best Practices and Tips
--------------------

1. **Optimize Your Search**:

   .. code-block:: python

       # Use multiple relevant keywords
       people = api.search_people(
           keywords="(Python OR Java) AND (Backend OR 'Back End')"
       )

2. **Handle Large Result Sets**:

   .. code-block:: python

       def get_all_results(search_func, **kwargs):
           results = []
           offset = 0
           while True:
               batch = search_func(**kwargs, offset=offset)
               if not batch:
                   break
               results.extend(batch)
               offset += len(batch)
           return results

3. **Respect Privacy and Rate Limits**:
   * Cache results when possible
   * Add delays between requests
   * Only collect necessary information

Conclusion
---------

You now know how to search for people using the LinkedIn API. This functionality is perfect for building recruitment tools, networking applications, or market research systems.

For more advanced usage, check out our other guides on profile analysis and connection management. 