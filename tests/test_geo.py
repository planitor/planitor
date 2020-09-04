from planitor.geo import get_address_lookup_params, lookup_address


def test_get_address_lookup_params():
    assert get_address_lookup_params("Barmahlíð 44B") == ("Barmahlíð", 44, "B")


def test_get_address_lookup_params_dashed_numbers():
    assert get_address_lookup_params("Laugavegur 151-155") == ("Laugavegur", 151, None)


def test_get_address_lookup_params_dashed_chooses_first():
    assert get_address_lookup_params("Dragháls 6-12/Fossháls 5-11") == (
        "Dragháls",
        6,
        None,
    )


def test_get_address_lookup_params_street_only():
    assert get_address_lookup_params("Laugavegur") == (
        "Laugavegur",
        None,
        None,
    )


def test_lookup_address_street_only():
    match = lookup_address("Laugavegur", None, None, "Reykjavík")
    assert not match


def test_lookup_address_house_number_is_hidden_in_vidsk_column():
    # Staðfangaskrá has a few instances of no house number but a range string like '6-8'
    # in the `vidsk` column
    match = lookup_address("Vesturgata", 6, None, "Reykjavík")
    assert match
    assert match["vidsk"] == "6-8"


def test_lookup_address_house_number_with_range_result():
    match = lookup_address("Laugavegur", 151, None, "Reykjavík")
    assert match
    assert match["vidsk"] == "151-155"


def test_lookup_address_matches_sernafn():
    match = lookup_address("Harpa", None, None, "Reykjavík")
    assert match
    assert match["heiti_nf"] == "Austurbakki"
    assert match["husnr"]
