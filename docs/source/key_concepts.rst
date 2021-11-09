Key Concepts
============

URN ID vs public ID
###################

While using the project, you'll come across two different types of identifier: URN IDs and public IDs.

URN ID
******

A URN ID is generally a number or something not human-readable. They will end up as part of a URN for a given
entity. Here is an example of a LinkedIn URN for a profile::

    urn:li:fs_miniProfile:ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzt

In this case, "ACoAABQ11fIBQLGQbB1V1XPBZJsRwfK5r1U2Rzt" is the URN ID. When asked for a URN ID, don't provide a full URN. Instead,
only provide the last item in the URN, delimited by ':' character (the URN ID).

Public ID
*********

A public ID is generally a string and something that is human-readable.
For example, for the LinkedIn profile at the URL https://www.linkedin.com/in/tom-quirk, the "public ID" is "tom-quirk".
The same applies for other entities across LinkedIn
