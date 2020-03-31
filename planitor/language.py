import re
from typing import Set

from sqlalchemy import func

from planitor import greynir
from planitor.models import Entity
from planitor.utils.text import fold


ICELANDIC_COMPANY_RE = (
    r"([0-9A-ZÉÝÚÍÓÁÖÞÐÆ](?:(?:(?:[\w,/]+)|og|&|,|-) ){1,3}(?:ehf|slhf|sf|hses|hf)\.)"
)


MAX_LEVENSHTEIN_DISTANCE = 5


def parse_icelandic_companies(text) -> Set:
    """ This is only a regex so it does not tokenize. When company names are in
    different inflections, these are of course also not normalized to nefnifall. It
    does not pick company names with more than 4 word segments.
    """
    return set(re.findall(ICELANDIC_COMPANY_RE, text))


def apply_title_casing(left, right):
    # Apply title casing of each word on the left to the right
    parts = []
    for left_word, right_word in zip(left.split(), right.split()):
        is_title = left_word[0] == left_word[0].upper()
        if is_title:
            right_word = right_word.title()
        parts.append(right_word)
    return " ".join(parts)


COMPANY_SUFFIXES = (
    "ehf.",
    "slhf.",
    "sf.",
    "hses.",
    "hf.",
)


def find_nominative_icelandic_companies(text) -> Set:
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

    found_company_names = set()

    for sentence in greynir.parse(text)["sentences"]:
        # Must reparse in lowercase to get inflection of names like Plúsarkitektar
        inflected_company_names = (
            parse_icelandic_companies(sentence.text) ^ found_company_names
        )

        if not inflected_company_names:
            continue

        # For companies named after persons we can just use node.canonical
        for node in sentence.terminal_nodes:
            if node.index == len(sentence.terminal_nodes) - 1:
                break
            next_node = sentence.terminal_nodes[node.index + 1]
            if node.kind == "PERSON" and next_node.text in COMPANY_SUFFIXES:
                inflected_company_names.remove(node.text + " {}".format(next_node.text))
                found_company_names.add(node.canonical + " {}".format(next_node.text))

        if not inflected_company_names:
            continue

        def _(matchobj):
            return matchobj.group(0).lower()

        sentence_text_with_lowercase_company_names = re.sub(
            ICELANDIC_COMPANY_RE, _, sentence.text
        )

        nodes = greynir.parse_single(
            sentence_text_with_lowercase_company_names
        ).terminal_nodes

        for inflected_name in inflected_company_names:
            for node in nodes:
                if node.text not in COMPANY_SUFFIXES:
                    continue
                name_part_nodes = [node]
                steps = 1
                while True:
                    previous_index = node.index - steps
                    if previous_index <= 0:
                        break
                    name_part_nodes.insert(0, nodes[previous_index])
                    lowercase_inflected = " ".join(
                        node.text for node in name_part_nodes
                    )
                    if lowercase_inflected == inflected_name.lower():
                        nominative_name = " ".join(
                            node.indefinite for node in name_part_nodes
                        )
                        found_company_names.add(
                            apply_title_casing(inflected_name, nominative_name)
                        )
                        break
                    steps += 1
                    if steps >= 5:  # Limit leftward matching to 4 extra words
                        break

    return found_company_names


def lookup_icelandic_company_in_entities(db, name):
    """ As described above, we may encounter similar looking inflections of company
    names. Instead of tokenizing and lemming words (which we could ...) we just use a
    simple Levenshtein distance calculation. This will also be useful for search.

    Here we use ascii folding and rely on the slug column which is also ascii folded.
    This is also useful for quick ranking of results for typing inputs that doesn’t
    require capital letters or accented characters.

    """

    folded = fold(name)
    col = func.levenshtein(Entity.slug, folded)
    return db.query(Entity, col).filter(col <= MAX_LEVENSHTEIN_DISTANCE).order_by(col)