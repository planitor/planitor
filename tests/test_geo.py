from planitor.geo import get_address_lookup_params


def test_get_address_lookup_params():
    assert get_address_lookup_params("Barmahlíð 44B") == ("Barmahlíð", 44, "B")
