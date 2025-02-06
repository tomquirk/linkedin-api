How To Add Connections Using the LinkedIn API
=======================================

.. note::
    This guide uses the unofficial `linkedin-api <https://github.com/tomquirk/linkedin-api>`_ Python package. While this package provides convenient access to LinkedIn's API, please note that it is not officially supported by LinkedIn.

Introduction
-----------

Building your professional network programmatically can help automate outreach and grow your connections strategically. In this guide, we'll show you how to use the ``add_connection()`` method to send connection requests on LinkedIn.

Prerequisites
------------

Before you begin, you'll need:

* Python 3.6 or higher installed on your system
* The ``linkedin-api`` package installed
* LinkedIn account credentials
* Public profile URLs or URNs of people you want to connect with

Step 1 — Setting Up the LinkedIn Client
----------------------------------

First, let's import the library and create a client instance:

.. code-block:: python

    from linkedin_api import Linkedin

    # Initialize the API client
    api = Linkedin('your-email@example.com', 'your-password')

Step 2 — Sending a Basic Connection Request
-------------------------------------

Let's send a connection request with a personalized message:

.. code-block:: python

    # Send connection request using public profile ID
    success = api.add_connection(
        public_id='john-doe',
        message='Hi John! I noticed we share an interest in Python development. Would love to connect!'
    )

    if not success:
        print("Connection request sent successfully!")
    else:
        print("Failed to send connection request")

Step 3 — Advanced Connection Methods
------------------------------

You can also send connection requests using LinkedIn URNs or handle multiple requests:

.. code-block:: python

    # Using profile URN
    api.add_connection(
        profile_urn='ACoAAAB2_VQB4OJFKyAKQkxcrXXXXXXX',
        message='Hi! Found your profile through the Python developers group.'
    )

    # Batch connection requests (with delay to avoid rate limiting)
    def send_batch_requests(profile_ids, message_template):
        import time
        
        for profile_id in profile_ids:
            message = message_template.format(profile_id=profile_id)
            success = api.add_connection(public_id=profile_id, message=message)
            print(f"Request to {profile_id}: {'Success' if not success else 'Failed'}")
            time.sleep(random.randint(2, 5))  # Random delay between requests

Understanding Connection Parameters
-----------------------------

Here are the key parameters for adding connections:

* **public_id**: The public identifier from profile URL
* **message**: Optional connection message (max 300 characters)
* **profile_urn**: Alternative to public_id, using LinkedIn's internal ID

Managing Connection States
----------------------

Track and manage your connection requests:

.. code-block:: python

    # Get pending invitations
    invitations = api.get_invitations()
    
    for invitation in invitations:
        print(f"From: {invitation['fromMember']['firstName']}")
        print(f"Message: {invitation.get('message', 'No message')}")

Troubleshooting Common Issues
-------------------------

Here are some common issues you might encounter:

* **Rate Limiting**: LinkedIn restricts how many requests you can send
* **Invalid Profile**: Double-check the profile ID or URN
* **Message Too Long**: Keep messages under 300 characters
* **Already Connected**: Can't send request to existing connections

Best Practices and Tips
--------------------

1. **Personalize Your Messages**:

   .. code-block:: python

       def create_personalized_message(person_info):
           template = """Hi {first_name}!
           I noticed your work in {industry} and would love to connect.
           Best regards,
           {my_name}"""
           
           return template.format(
               first_name=person_info['first_name'],
               industry=person_info['industry'],
               my_name="Your Name"
           )[:300]  # Ensure under 300 chars

2. **Handle Rate Limits**:

   .. code-block:: python

       import random
       import time

       def send_safe_request(api, profile_id, message):
           try:
               success = api.add_connection(public_id=profile_id, message=message)
               time.sleep(random.randint(2, 5))  # Random delay
               return success
           except Exception as e:
               print(f"Error sending request: {str(e)}")
               return False

3. **Best Practices for Connection Requests**:
   * Always include a personalized message
   * Space out requests over time
   * Target relevant connections
   * Monitor acceptance rates

Conclusion
---------

You now know how to programmatically send connection requests using the LinkedIn API. This functionality is perfect for building networking tools, automating outreach campaigns, or growing your professional network strategically.

For more advanced usage, check out our other guides on searching for people and managing conversations. 