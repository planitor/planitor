from typing import Tuple, List, Optional
import re

from iceaddr.addresses import _run_addr_query, _cap_first
from iceaddr.postcodes import postcodes_for_placename


def get_housenumber(string):
    # Zero in on the first house number in ranges like "12b-14b"
    if "-" in string:
        string, _ = string.split("-", 1)
    match = re.search(r"(\d{1,3})([A-Z]?)", string)
    if match is None:
        return string, None
    return int(match.group(1)), match.group(2)


def get_address_lookup_params(address) -> Tuple[str, Optional[int], Optional[str]]:

    if "/" in address:
        address, _ = address.split("/", 1)

    # Fix broken HTML in Reykjavík Lotus Notes
    if '">' in address:
        _, address = address.split('">', 1)

    # Remove an inconsistency, change "101 - 103" to "101-103"
    address = re.sub(r"(\d+) - (\d+)", r"\1-\2", address)

    # Remove staðnúmer and long digits
    address = re.sub(r" [\d\.]{4,10}", "", address)

    # Two times, take pick whatever comes before, or -
    for i in range(2):
        for split_token in (", ", " - "):
            if split_token in address:
                address, _ = address.split(split_token, 1)
                break

    # See if a house number looking thing is at the end of address
    match = re.search(r" (\d[\w-]*)$", address)
    if match:
        number, letter = get_housenumber(match.group(1))
        number = int(number)
    else:
        number, letter = (None, None)

    # Pick the street name, usually whatever comes before the first number
    try:
        address, _ = re.split(r" \d", address, 1)
    except ValueError:
        pass

    return address, number, letter or None


def iceaddr_lookup(
    street_name, number=None, letter=None, postcode=None, placename=None, limit=50
) -> List[dict]:
    """ Look up all addresses matching criterion """
    street_name = _cap_first(street_name.strip())

    pc = [postcode] if postcode else []

    # Look up postcodes for placename if no postcode is provided
    if placename and not postcode:
        pc = postcodes_for_placename(placename.strip())

    query = "SELECT * FROM stadfong WHERE"
    name_fields = ["heiti_nf=?", "heiti_tgf=?"]
    if not number:
        # Add lookup for churches and places of interest like Harpa
        name_fields.append("serheiti=?")
    query += "({})".format(" OR ".join(name_fields))
    args = [street_name] * len(name_fields)

    if number:
        query += " AND (husnr=? OR substr(vidsk, 0, instr(vidsk, '-')) = ?)"
        args.extend((number, str(number)))
        if letter:
            query += " AND bokst LIKE ? COLLATE NOCASE"
            args.append(letter)
    else:
        # If looking for streets only, and not place of interest, ensure
        # there are not filled husnr
        query += " AND (serheiti != '' OR (husnr is null AND vidsk = ''))"

    if pc:
        qp = " OR ".join([" postnr=?" for p in pc])
        args.extend(pc)
        query += " AND (%s) " % qp

    # Ordering by postcode may in fact be a reasonable proxy
    # for delivering by order of match likelihood since the
    # lowest postcodes are generally more densely populated
    query += " ORDER BY vidsk != '', postnr ASC, husnr ASC, bokst ASC LIMIT ?"
    args.append(limit)

    return _run_addr_query(query, args)


def lookup_address(
    address: str, number: Optional[int], letter: Optional[str], placename: str
) -> Optional[dict]:
    match = iceaddr_lookup(
        address, number=number, letter=letter, placename=placename, limit=1
    )
    if match:
        return match[0]
