from planitor.utils.text import slugify


def test_slugify():
    assert slugify("Farfuglar ses.") == "farfuglar-ses"
    assert slugify("Sóltún 1-3, húsfélag") == "soltun-1-3-husfelag"
    assert slugify("Klettur - sala og þjónusta ehf.") == "klettur-sala-og-thjonusta-ehf"
    assert slugify("G&S ehf") == "g-s-ehf"
    assert slugify("Original Fish & Chips ehf.") == "original-fish-chips-ehf"
    assert slugify("S.Á.Á. fasteignir") == "s-a-a-fasteignir"
    assert slugify("Eign 00-11 ehf.") == "eign-00-11-ehf"
    assert slugify("S.K.Ó. ehf.") == "s-k-o-ehf"
