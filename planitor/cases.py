import re
from typing import Optional
from collections import defaultdict

from tokenizer import tokenize, split_into_sentences, TOK

from planitor.models import Minute, Meeting, CaseStatusEnum


# Catches "umhverfis-og skipulagsráð" which should be "umhverfis- og skipulagsráð"
COMPOUND_ENTITY_DASH_TYPO = re.compile(r"(?:([^\ ])(?:\ ?-\ ?og))")


PATTERNS = {
    CaseStatusEnum.approved: (
        r"^samþykkt\.",
        r"^umsögn skipulagsfulltrúa samþykkt\.",
        r"^samþykkt með vísan",
        r"^samþykkt að gefa út framkvæmdaleyfi með vísan til",
        r"^umsögn deildarstjóra aðalskipulags samþykkt\.",
        r"^jákvætt\.",
        r"^jákvætt með vísan til umsagnar",
    ),
    CaseStatusEnum.delayed: (r"^frestað\.",),
    CaseStatusEnum.denied: (
        r"^neikvætt\.",
        r"^neikvætt með vísan",
        r"^synjað\.",
        r"nei\.",
    ),
    CaseStatusEnum.directed_to_adalskipulag: (
        r"^vísað til umsagnar deildarstjóra aðalskipulags\.",
    ),
    CaseStatusEnum.directed_to_skipulagsrad: (
        r"^vísað til umhverfis- og skipulagsráðs",
        r"^vísað til skipulags- og samgönguráðs",
    ),
    CaseStatusEnum.assigned_project_manager: (
        r"^vísað til umsagnar verkefnisstjóra\.",
        r"^vísað til umsagnar hjá verkefnisstjóra\.",
        r"^vísað til meðferðar verkefnisstjóra\.",
        r"^vísað til meðferðar hjá verkefnisstjóra\.",
    ),
    CaseStatusEnum.no_comment: (
        r"^ekki eru gerðar skipulagslegar athugasemdir við erindið",
        r"^ekki er gerð athugasemd við erindið",
        r"^ekki gerð athugasemd við erindið",
    ),
    CaseStatusEnum.notice: (r"^samþykkt að grenndarkynna", r"^grenndarkynning samþykkt",),
}


def clean_first_sentence(text):
    """ This is written to clean up and consolidate as many remarks as possible.
    They are hand written and when initially analyzing it was very useful to count
    instances of certain sentence structures. Therefore date tokens are being
    removed and such.

    """

    text = next(split_into_sentences(text))
    text = text.lower()
    text = re.sub(COMPOUND_ENTITY_DASH_TYPO, lambda m: "{}- og".format(m.group(1)), text)

    def tokens(sentence):
        for token in tokenize(sentence):
            if token.txt and token.kind == TOK.WORD and token.txt != "dags.":
                yield token.txt

    text = " ".join(tokens(text)) + "."
    return text


def get_case_status_from_remarks(remarks) -> Optional[CaseStatusEnum]:
    if not remarks:
        return None
    remarks = clean_first_sentence(remarks)
    for case_status, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, remarks) is not None:
                return case_status
    return None


def _print_statistics(db) -> None:
    """ Usage

    >>> from planitor.cases import _print_statistics
    >>> from planitor.database import get_db
    >>> _print_statistics(next(get_db()))

    """

    total = db.query(Minute).count()
    _counter = defaultdict(int)

    for minute in db.query(Minute).join(Meeting).filter(Meeting.council_id == 4):
        status = get_case_status_from_remarks(minute.remarks)
        _counter[status] += 1

    for status, count in sorted(_counter.items(), key=lambda kv: kv[1]):
        print(
            "{}".format(count).rjust(6),
            "{0:.0%}".format((count / total)).rjust(4),
            status.value.label if status is not None else "Engin staða fannst",
        )
