import re
from typing import Optional, Tuple

from iceaddr import iceaddr_lookup
from iceaddr.addresses import _cap_first


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


def lookup_address(
    address: str, number: Optional[int], letter: Optional[str], placename: str
) -> Optional[dict]:
    address = _cap_first(address.strip())
    match = iceaddr_lookup(
        address, number=number, letter=letter, placename=placename, limit=1
    )
    if match:
        addr = match[0]
        if number is None and addr["husnr"] and addr["serheiti"] != address:
            # Do not match street name lookups without number unless the match was
            # because of a serheiti lookup like "Harpa"
            return None
        return match[0]
