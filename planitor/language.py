import re
from typing import Dict

from planitor import greynir

COMPANY_SUFFIXES = (
    "ehf.",
    "slhf.",
    "sf.",
    "hses.",
    "hf.",
    "ohf.",
    "bs.",
)

ICELANDIC_COMPANY_RE = re.compile(
    r"([0-9A-ZÉÝÚÍÓÁÖÞÐÆ](?:(?:(?:[\w,/]+)|og|&|,|-) ){{1,3}}(?:{})\.)".format(
        "|".join(suff.strip(".") for suff in COMPANY_SUFFIXES)
    )
)


def clean_company_name(name):
    # Ensure company suffixes are followed by the period character
    for suff in COMPANY_SUFFIXES:
        if name.endswith(" {}".format(suff.rstrip("."))):
            return "{}.".format(name)
    return name


def parse_icelandic_companies(text) -> Dict:
    """ This is only a regex so it does not tokenize. When company names are in
    different inflections, these are of course also not normalized to nefnifall. It
    does not pick company names with more than 4 word segments (see regex).

    """
    found = {}

    for match in re.finditer(ICELANDIC_COMPANY_RE, text):
        if match.group() not in found:
            found[match.group()] = [match.span()]
        else:
            found[match.group()].append(match.span())

    return found


def apply_title_casing(left, right):
    # Apply title casing of each word on the left to the right
    parts = []
    for left_word, right_word in zip(left.split(), right.split()):
        is_title = left_word[0] == left_word[0].upper()
        is_upper = left_word == left_word.upper()
        if is_title:
            right_word = right_word.title()
        if is_upper:
            right_word = right_word.upper()
        parts.append(right_word)
    return " ".join(parts)


def extract_company_names(text) -> Dict:
    """ Get company names with preserved plurality and in nominative form. The
    strategy is multipart:

    1.  First match companies named after their owner. This is done because they are
        simple to deal with. Use the `PERSON` kind token in Greynir followed by one of
        the company suffixes.
    2.  Use a regex substitution to match lowercase company names so we can deal with
        names like "Plúsarkitektar" as they won’t be inflected back to nominative
        if they are thought to be sérnafn. Use a look behind algorithm to match the
        tokenized text to the regex matches.
    3.  Use a title case detection to reapply the correct casing.

    This is definitely not a foolproof strategy. Caveats:

    1.  The regex does not match company names with more than three tokens (e.g.
        "Vektor, hönnun og ráðgjöf ehf.").
    2.  I’m still not sure if `node.indefinite` always gets us to the word form used in
        RSK fyrirtækjaskrá.

    """

    matched_names = {}
    name_positions = parse_icelandic_companies(text)

    if not parse_icelandic_companies(text):
        return matched_names

    for sentence in greynir.parse(text)["sentences"]:

        if not sentence.terminal_nodes:
            continue
        original_names = set(name_positions.keys()) - set(matched_names.keys())

        if not original_names:
            continue

        # For companies named after persons we can just use node.canonical
        for i, node in enumerate(sentence.terminal_nodes):
            if i == len(sentence.terminal_nodes) - 1:
                break
            next_node = sentence.terminal_nodes[i + 1]
            if node.kind == "PERSON" and next_node.text in COMPANY_SUFFIXES:
                original_name = node.text + " {}".format(next_node.text)
                if original_name not in original_names:
                    # Skip if we caught "Sigurjóns ehf." in "Hjólbarðaverkstæði
                    # Sigurjóns ehf."
                    continue
                original_names.remove(original_name)
                name = node.canonical + " {}".format(next_node.text)
                matched_names[name] = name_positions[original_name]

        if not original_names:
            continue

        # Must reparse in lowercase to get inflection of names like Plúsarkitektar
        def _(matchobj):
            return matchobj.group(0).lower()

        nodes = greynir.parse_single(
            re.sub(ICELANDIC_COMPANY_RE, _, sentence.text)
        ).terminal_nodes

        if not nodes:
            continue

        for original_name in original_names:
            for i, node in enumerate(nodes):
                if node.text not in COMPANY_SUFFIXES:
                    continue
                name_part_nodes = [node]
                steps = 1
                while True:
                    previous_index = i - steps
                    if previous_index <= 0:
                        break
                    name_part_nodes.insert(0, nodes[previous_index])

                    untokenized = " ".join(node.text for node in name_part_nodes)

                    _original_name = original_name.lower()

                    # # Greynir seems to convert to em-dash
                    _untokenized = untokenized.replace("—", "-").replace("–", "-")

                    if not _original_name.endswith(_untokenized):
                        break

                    if _untokenized == _original_name:
                        nominative_name = " ".join(
                            node.indefinite for node in name_part_nodes
                        )
                        nominative_name = apply_title_casing(
                            original_name, nominative_name
                        )
                        matched_names[nominative_name] = name_positions[original_name]
                        break
                    steps += 1
                    if steps > 4:  # Limit leftward matching to 4 extra words
                        break

    return matched_names
