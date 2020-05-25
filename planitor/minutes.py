from typing import List
from .language import search


IGNORE = ("dags.", "kr.", "nr.")
REPLACE = (("Málinu vísað", "Málinu er vísað"),)


def get_minute_document(minute) -> str:
    parts = [minute.headline, minute.inquiry, minute.remarks, minute.case.address]
    parts += [e.entity.name for e in (minute.case.entities or [])]
    return "\n".join(part for part in parts if part)


def get_minute_lemmas(minute) -> List[str]:
    text = get_minute_document(minute)
    for replace in REPLACE:
        text = text.replace(*replace)
    return list(search.get_lemmas(text=text, ignore=IGNORE))
