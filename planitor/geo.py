import re

from planitor.models import Geoname, Housenumber

""" The following regex matches street and house numbers like these:
Síðumúli 24-26
Prófgata 12b-14b
Sæmundargata 21
Tjarnargata 10D
Bauganes 3A
Vesturás 10 - 16
"""

ADDRESS_RE = re.compile(r"^([^\W\d]+) (\d+[A-Za-z]?(?: ?- ?)?(?:\d+[A-Za-z]?)?)?$")


def get_geoname_and_housenumber_from_address_and_city(db, address, city):
    match = re.match(ADDRESS_RE, address)
    if not match:
        return None, None

    street_name, number = match.groups()
    street = (
        db.query(Geoname)
        .filter_by(name=street_name, city=city)
        .order_by(Geoname.importance)
        .first()
    )

    if street is None:
        return None, None

    housenumber = (
        db.query(Housenumber)
        .filter_by(street=street, housenumber=number.replace(" ", ""))
        .first()
    )
    return street, housenumber
