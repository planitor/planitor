from planitor.geo import lookup_address, get_address_lookup_params
from planitor.crud.city import get_or_create_address
from planitor.models import Address, Case


def re_match(db, case: Case) -> int:
    # Returns 0 for no modification, 1 for nullification, 2 for modified match
    # and 3 for modified match and new address
    old_address = case.iceaddr
    street, number, letter = get_address_lookup_params(case.address)
    iceaddr_match = lookup_address(street, number, letter, "Reykjavík")
    created = False
    if iceaddr_match:
        address, created = get_or_create_address(db, iceaddr_match)
        if created:
            db.commit()
        case.iceaddr = address
    else:
        case.iceaddr = None
    if old_address != case.iceaddr:
        db.add(case)
        if not case.iceaddr:
            return 1
        return 3 if created else 2
    return 0


def re_match_and_update_case_addresses(db):
    query = (
        db.query(Case)
        .join(Address)
        .filter(Case.address != None)  # noqa
        .filter(Case.address_id != None)  # noqa
        .order_by(Case.updated.desc())
        .offset(4000)
    )
    print(f"Starting re-matching of {query.count()} items")
    modified = 0
    nullified = 0
    modified_and_created = 0
    for i, case in enumerate(query):
        code = re_match(db, case)
        if code == 2:
            modified += 1
        if code == 1:
            nullified += 1
        if code == 3:
            modified_and_created += 1
        if i % 400 == 0:
            print(
                f"{modified} modified, {nullified} nullified, "
                f"{modified_and_created} created, {i} scanned"
            )
            db.commit()
    db.commit()


if __name__ == "__main__":
    from planitor.database import db_context

    with db_context() as db:
        re_match_and_update_case_addresses(db)
