""" Version
"""

import os
def string():
    """_summary_

    Returns:
        string: version number
    """
    try:
        filename = os.path.dirname(__file__) + "/VERSION"
        with open(filename, "r", encoding="utf-8") as handle:
            version = handle.read().strip()
            if version:
                return version
    except IOError as ex:
        print ('Caught exception: ', ex)

    return "unknown (git checkout)"
