How To Send Messages Using the LinkedIn API
======================================

.. note::
    This guide uses the unofficial `linkedin-api <https://github.com/tomquirk/linkedin-api>`_ Python package. While this package provides convenient access to LinkedIn's API, please note that it is not officially supported by LinkedIn.

Introduction
-----------

Sending messages programmatically through LinkedIn can help automate networking, follow up with connections, or manage communication at scale. In this guide, we'll show you how to use the ``send_message()`` method to send messages to your LinkedIn connections.

Prerequisites
------------

Before you begin, you'll need:

* Python 3.6 or higher installed on your system
* The ``linkedin-api`` package installed
* LinkedIn account credentials
* Existing LinkedIn connections to message

Step 1 — Setting Up the LinkedIn Client
----------------------------------

First, let's import the library and create a client instance:

.. code-block:: python

    from linkedin_api import Linkedin

    # Initialize the API client
    api = Linkedin('your-email@example.com', 'your-password')

Step 2 — Sending a Message to an Existing Conversation
-----------------------------------------------

If you already have a conversation with someone, you can send a message using the conversation URN:

.. code-block:: python

    # Send a message to an existing conversation
    success = api.send_message(
        message_body="Hi! Thanks for connecting. I'd love to learn more about your work.",
        conversation_urn_id="123456789"
    )

    if not success:
        print("Message sent successfully!")

Step 3 — Starting a New Conversation
------------------------------

To start a new conversation with someone, you'll need their profile URN:

.. code-block:: python

    # Start a new conversation
    success = api.send_message(
        message_body="Hello! I saw your work on AI and would love to connect.",
        recipients=["urn:li:fs_miniProfile:AbC123_dEf"]
    )

    if not success:
        print("New conversation started successfully!")

Understanding Message Parameters
---------------------------

Here are the key parameters for sending messages:

* **message_body**: The text content of your message (required)
* **conversation_urn_id**: ID of an existing conversation
* **recipients**: List of profile URNs for new conversations

Working with Conversations
---------------------

Here's how to manage your conversations effectively:

.. code-block:: python

    def send_message_with_retry(api, message, conversation_id=None, recipients=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                success = api.send_message(
                    message_body=message,
                    conversation_urn_id=conversation_id,
                    recipients=recipients
                )
                if not success:
                    return True
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
        return False

Troubleshooting Common Issues
-------------------------

Here are some common issues you might encounter:

* **Message Not Sent**: Verify the recipient can receive messages
* **Rate Limiting**: LinkedIn limits how many messages you can send
* **Invalid URN**: Double-check conversation and profile URNs
* **Connection Required**: Some users only accept messages from connections

Best Practices and Tips
--------------------

1. **Message Templates**:

   .. code-block:: python

       def create_message_template(template_type="follow_up"):
           templates = {
               "follow_up": """Hi {name},
               Thanks for connecting! I noticed you work in {industry} 
               and would love to learn more about your experience.
               
               Best regards,
               {sender}""",
               "introduction": """Hi {name},
               I came across your profile and was impressed by {detail}.
               Would you be open to a brief conversation about {topic}?
               
               Best,
               {sender}"""
           }
           return templates.get(template_type, templates["follow_up"])

2. **Handle Rate Limits**:

   .. code-block:: python

       import time
       from random import uniform

       def send_bulk_messages(api, recipients, message_template, delay_range=(1, 3)):
           results = []
           for recipient in recipients:
               success = api.send_message(
                   message_body=message_template.format(**recipient),
                   recipients=[recipient['urn']]
               )
               results.append({
                   'recipient': recipient['urn'],
                   'success': not success
               })
               time.sleep(uniform(*delay_range))  # Random delay between messages
           return results

3. **Best Practices for Messaging**:
   * Personalize each message
   * Respect LinkedIn's messaging limits
   * Add delays between messages
   * Keep track of sent messages

Conclusion
---------

You now know how to send messages programmatically using the LinkedIn API. This functionality is perfect for building networking tools, automated follow-up systems, or communication management applications.

For more advanced usage, check out our other guides on managing connections and tracking conversations. 