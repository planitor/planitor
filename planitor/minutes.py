from typing import List
from .language import search


IGNORE = ("dags.", "kr.", "nr.")
REPLACE = (("Málinu vísað", "Málinu er vísað"),)


def get_minute_document(minute) -> str:
    parts = [
        minute.headline,
        minute.inquiry,
        minute.remarks,
    ]
    parts += [r.contents for r in (minute.responses or [])]
    return "\n".join(part.rstrip(". ") + "." for part in parts if part)


def get_minute_lemmas(minute) -> List[str]:
    _lemmas = []
    text = get_minute_document(minute)
    for replace in REPLACE:
        text = text.replace(*replace)
    _lemmas += [minute.case.address, minute.case.serial]
    _lemmas += [e.entity.name for e in (minute.case.entities or [])]
    _lemmas += list(search.get_lemmas(text=text, ignore=IGNORE))
    return _lemmas
