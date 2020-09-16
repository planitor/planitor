from typing import List

from planitor.models import Address, Minute

from .language import search

IGNORE = ("dags.", "kr.", "nr.")
REPLACE = (("Málinu vísað", "Málinu er vísað"),)


def get_address_parts(address: Address) -> List[str]:
    parts = []
    for _part in [
        address.heiti_nf,
        address.heiti_tgf,
        f"{address.husnr}{address.bokst}",
        str(address.husnr),
        address.vidsk,
    ]:
        if _part and _part not in parts:
            parts.append(_part)
    return parts


def get_minute_document(minute: Minute) -> str:
    parts = [
        minute.headline,
        minute.inquiry,
        minute.remarks,
    ]
    parts += [r.contents for r in (minute.responses or [])]
    return "\n".join(part.rstrip(". ") + "." for part in parts if part)


def get_minute_lemmas(minute: Minute) -> List[str]:
    _lemmas = []
    text = get_minute_document(minute)
    for replace in REPLACE:
        text = text.replace(*replace)
    _lemmas += list(search.get_lemmas(text=text, ignore=IGNORE))
    if minute.case.address:
        _lemmas.append(minute.case.address)
    if minute.case.iceaddr:
        _lemmas.extend(sorted(get_address_parts(minute.case.iceaddr)))
    if minute.case.serial:
        _lemmas.append(minute.case.serial)
    _lemmas += [e.entity.name for e in (minute.case.entities or [])]
    return _lemmas
