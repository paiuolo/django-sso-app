# Boostable functions
#
# import pyximport
# pyximport.install()


def get_apigateway_profile_groups_from_header(groups_header: str) -> list:
    """
    Extracts apigateway consumer groups from header
    :param groups_header:
    :return:
    """
    if groups_header not in (None, ''):
        return list(map(str.strip, groups_header.split(',')))

    return []
