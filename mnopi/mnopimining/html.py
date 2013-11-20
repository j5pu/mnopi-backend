import re

RELEVANT_META_PROPERTIES = ["keywords",
                            "description"]

def get_html_metadata(html_code):
    """
    Process html code and returns a dictionary of relevant properties
    from meta and other tags
    """
    properties_list = {}

    # Retrieve important meta properties
    meta_tags = re.findall("<meta.*?>", html_code)
    for tag in meta_tags:
        relevant_tag = match_relevant_meta(tag)
        if relevant_tag:
            properties_list[relevant_tag[0]] = relevant_tag[1]

    # Title of page
    title_match = re.search("<title>(.*)</title>", html_code)
    if title_match:
        title = title_match.groups()[0]
        properties_list["title"] = title

    return properties_list

def match_relevant_meta(meta_tag):
    """
    Return tuples (name, content) of relevant meta properties
    <meta name="description" content="Fancy webpage" -> ("description", "Fancy webpage")
    """
    for tag in RELEVANT_META_PROPERTIES:
        name_matcher = re.compile("name.*?\"(.*?)\"")
        match = name_matcher.search(meta_tag)
        if match:
            meta_name = match.groups()[0]

            # Check if the type of meta data is of our interest
            if meta_name == tag:
                content_matcher = re.compile("content.*?\"(.*?)\"")
                match = content_matcher.search(meta_tag)
                meta_content = match.groups()[0]

                return (meta_name, meta_content)

    return None