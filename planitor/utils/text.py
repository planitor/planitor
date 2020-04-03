import re
from collections import defaultdict

from . import mapping


def none_factory():
    return None


default_translate_table = defaultdict(none_factory, mapping.translate_table)


def fold(string, replacement=""):
    """Fold string to ASCII.
    Unmapped characters should be replaced with empty string by default, or other
    replacement if provided.
    All astral plane characters are always removed, even if a replacement is
    provided.
    """

    if string is None:
        return ""

    try:
        # If string contains only ASCII characters, just return it.
        string.encode("ascii")
        return string
    except UnicodeEncodeError:
        pass

    if replacement:

        def replacement_factory():
            return replacement

        translate_table = defaultdict(replacement_factory, mapping.translate_table)
    else:
        translate_table = default_translate_table

    return string.translate(translate_table).lower()


def slugify(string):
    string = fold(string).lower()
    string = re.sub(r"[^\w]", "-", string)
    string = re.sub(r"\-+", "-", string)
    string = string.strip(" -")
    return string
