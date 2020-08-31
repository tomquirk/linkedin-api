def get_id_from_urn(urn):
    """
    Return the ID of a given Linkedin URN.

    Example: urn:li:fs_miniProfile:<id>
    """
    return urn.split(":")[3]

def get_urn_from_raw_group_update(raw_string):
    """
    Return the URN of a raw group update

    Example: urn:li:fs_miniProfile:<id>
    Example: urn:li:fs_updateV2:(<urn>,GROUP_FEED,EMPTY,DEFAULT,false)
    """
    return raw_string.split('(')[1].split(',')[0]

def get_update_author_name(d_included):
    """Parse a dict and returns, if present, the post author name

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict

    :return: Author name
    :rtype: str
    """
    try:
        return d_included['actor']['name']['text']
    except KeyError:
        return ''
    except TypeError:
        return 'None'

def get_update_old(d_included):
    """Parse a dict and returns, if present, the post old string

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict

    :return: Post old string. Example: '2 mo'
    :rtype: str
    """
    try:
        return d_included['actor']['subDescription']['text']
    except KeyError:
        return ''
    except TypeError:
        return 'None'

def get_update_content(d_included):
    """Parse a dict and returns, if present, the post content

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict

    :return: Post content
    :rtype: str
    """
    try:
        return d_included['commentary']['text']['text']
    except KeyError:
        return ''
    except TypeError:
        return 'None'

def get_update_author_profile(d_included, base_url):
    """Parse a dict and returns, if present, the URL corresponding the profile

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict
    :param base_url: site URL
    :type d_raw: str

    :return: URL with either company or member profile
    :rtype: str
    """
    try:
        urn = d_included['actor']['urn']
    except KeyError:
        return ''
    except TypeError:
        return 'None'
    else:
        urn_id = urn.split(':')[-1]
        if 'company' in urn:
            return f"{base_url}/company/{urn_id}"
        elif 'member' in urn:
            return f"{base_url}/in/{urn_id}"

def get_update_url(d_included, base_url):
    """Parse a dict and returns, if present, the post URL

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict
    :param base_url: site URL
    :type d_raw: str

    :return: post url
    :rtype: str
    """
    try:
        urn = d_included['updateMetadata']['urn']
    except KeyError:
        return ''
    except TypeError:
        return 'None'
    else:
        return f"{base_url}/feed/update/{urn}"

def append_update_post_field_to_posts_list(d_included, l_posts, post_key,
    post_value):
    """Parse a dict and returns, if present, the desired value. Finally it
    updates an already existing dict in the list or add a new dict to it

    :param d_included: a dict, as returned by res.json().get("included", {})
    :type d_raw: dict
    :param l_posts: a list with dicts
    :type l_posts: list
    :param post_key: the post field name to extract. Example: 'author_name'
    :type post_key: str
    :param post_value: the post value correspoding to post_key
    :type post_value: str

    :return: post list
    :rtype: list
    """
    elements_current_index = len(l_posts) - 1

    if elements_current_index == -1:
        l_posts.append({post_key: post_value})
    else:
        if not post_key in l_posts[elements_current_index]:
            l_posts[elements_current_index][post_key] = post_value
        else:
            l_posts.append({post_key: post_value})
    return l_posts
