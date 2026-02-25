from typing import Dict, Iterable, List, Tuple

from reynir.reynir import _Sentence

from planitor import greynir
from .companies import COMPANY_SUFFIXES


def extract_person_names(
    text: str, sentences: Iterable[_Sentence] = None
) -> Dict[str, List[Tuple[int, int]]]:
    """Extract person names from text using Greynir NLP parsing.

    Returns a dict mapping canonical (nominative) names to lists of (start, end)
    character positions in the original text.

    Skips person nodes that are followed by a company suffix (those are handled
    by extract_company_names).
    """
    if sentences is None:
        sentences = greynir.parse(text)["sentences"]

    matched_names: Dict[str, List[Tuple[int, int]]] = {}

    # Track where we are in the text to find correct positions for each sentence
    search_from = 0

    for sentence in sentences:
        if not sentence.terminal_nodes:
            continue

        nodes = sentence.terminal_nodes

        # Find approximate start of this sentence in the source text
        sent_text = sentence.text
        sent_start = text.find(sent_text, search_from)
        if sent_start == -1:
            # Greynir may normalize whitespace; try from current position anyway
            sent_start = search_from
        else:
            search_from = sent_start + len(sent_text)

        # Track position within this sentence for progressive searching
        node_search_from = sent_start

        for i, node in enumerate(nodes):
            if node.kind != "PERSON":
                continue

            # Skip person nodes followed by company suffix — those belong to
            # company extraction (e.g. "Sigurjóns ehf.")
            if i < len(nodes) - 1 and nodes[i + 1].text in COMPANY_SUFFIXES:
                continue

            canonical = node.canonical
            if not canonical:
                continue

            # Find position of the original inflected text
            original_text = node.text
            start = text.find(original_text, node_search_from)
            if start == -1:
                continue

            end = start + len(original_text)
            node_search_from = end
            span = (start, end)

            if canonical in matched_names:
                if span not in matched_names[canonical]:
                    matched_names[canonical].append(span)
            else:
                matched_names[canonical] = [span]

    return matched_names
