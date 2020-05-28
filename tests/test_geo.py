import re
import iceaddr

from planitor.geo import get_geoname_and_housenumber_from_address_and_city

ADDRESS_RE = re.compile(
    r"^(?:\d+\">)([^\W\d]+) (\d+[A-Za-z]?(?: ?- ?)?(?:\d+[A-Za-z]?)?)?$"
)


def clean(address):
    match = re.match(ADDRESS_RE, address)
    if match is None:
        return address
    return match.group(0)


def get_housenumber(string):
    if "-" in string:
        string, _ = string.split("-", 1)
    match = re.search(r"(\d{1,3})([A-Z]?)", string)
    if match is None:
        return string, None
    return match.group(1), match.group(2)


def lookup(address):
    if '">' in address:
        _, address = address.split('">', 1)

    address = re.sub(r"(\d+) - (\d+)", r"\1-\2", address)
    address = re.sub(r" [\d\.]{4,10}", "", address)

    for i in range(1):
        for split_token in (", ", " - "):
            if split_token in address:
                address, _ = address.split(split_token, 1)
                break

    match = re.search(r" (\d[\w-]*)$", address)

    if match:
        number, letter = get_housenumber(match.group(1))
    else:
        number, letter = (None, None)

    try:
        address, _ = re.split(r" \d", address, 1)
    except ValueError:
        pass

    match = iceaddr.iceaddr_lookup(address, number=number, letter=letter, placename=CITY)
    if match:
        return (
            match[0]["heiti_nf"],
            "{husnr}{bokst}".format(**match[0]),
            (address, number, letter),
        )
    else:
        match = iceaddr.iceaddr_suggest(f"{address}, {CITY}")
        if match:
            return (
                match[0]["heiti_nf"],
                "{husnr}{bokst}".format(**{k: v or "" for k, v in match[0].items()}),
                ("suggest",),
            )
    return None, None, (address, number, letter)


def tests_geo(db):
    print()
    for address in ADDRESSES[:50]:
        # for address in ("Lindargata 42, 46 og 46A",):
        geoname, housenumber = get_geoname_and_housenumber_from_address_and_city(
            db, address, CITY
        )
        old_s, old_n = (
            geoname.name if geoname else "",
            housenumber.housenumber if housenumber else "",
        )
        old = old_s + (" {}".format(old_n) if old_n else "")

        new_s, new_n, params = lookup(address)
        new_s, new_n = (new_s or ""), (new_n or "")
        new = new_s + (" {}".format(new_n) if new_n else "")

        print(f"{address[:30]: <30} | {old: <20} | {new: <20}", params)


ADDRESSES = [
    "Urriðakvísl 18",
    "Óðinsgata",
    "Akrasel 17",
    "Hádegismóar",
    "Njarðargata 43 og 45",
    "Gvendargeisli 60",
    "Vesturgata 57A",
    "Brautarholt 5 173345",
    "Baldursgata 11",
    "Hólmasel 1",
    "Lindargata 42, 46 og 46A",
    "Grandagarður 18",
    "Tunguháls 8",
    "Vatnsmýrarvegur 30",
    "Haukdælabraut 18",
    "Hverfisgata 54",
    "Döllugata 2",
    "Yrjar við Elliðavatn",
    "Þengilsbás 3",
    "Skeifan",
    "Flugvöllur 106643",
    "Kirkjustræti 2",
    "Kleppsvegur 92",
    "Skerplugata 4",
    "Færsla Hringbrautar",
    "Lokastígur 25",
    "Tindstaðir Innri 125758",
    "Freyjugata 34",
    "Lágmúli 4",
    "Seljabraut 36-52",
    "Skipholt 44",
    "Fiskislóð 11-13",
    "Flugvöllur 106746",
    "Reitur 1.181.4, Lokastígsreitur 4",
    "Landspilda 125736",
    "Engjateigur 17 - 19",
    "Klettagarðar 7A",
    "Frostafold 101-131",
    "Álfaland 6",
    '1">Efstaleiti 19',
    "Smiðshöfði 21",
    "Þingvað 29",
    "Bleikjukvísl 2",
    "Nesjavallaleið 9 - fangelsi",
    "Grenimelur 9",
    "Klettháls 15A",
    "Haukdælabraut 94",
    "Háskóli Íslands, lóðamál",
    "Bólstaðarhlíð 25",
    "Faxaflóahafnir - Gamla höfnin og Sundahöfn",
    "Kambsvegur 1",
    "Grensásvegur",
    "Útivistarsvæði",
    "Miklabraut 82",
    "Hátún 6B",
    "Eyjarslóð 7",
    "Austurbrún 33",
    "Grjótháls 8",
    "Skipasund 1",
    "Lokastígur 28A",
    "Óðinsgata 15",
    "Akurgerði 38",
    "Frakkastígur 7",
    "Bræðraborgarst 39-41",
    "Hæðargarður 38",
    "Álfheimar 25",
    "Bergþórugata 7",
    "Öldugata 12",
    "Fellsmúli 10A",
    "Ásvallagata 13",
    "Sæviðarsund 84",
    "Saltvík 3",
    "Blöndubakki 1-15",
    "Ægisgarður 3",
    "Reynimelur 44",
    "Granaskjól 23",
    "Hamravík 10",
    "Bitruháls 1",
    "Bjarkargata 6",
    "Skeljanes",
    "Auðarstræti 15",
    "Blönduhlíð 25",
    "Grófin",
    "Bústaðavegur 59",
    "Bæjarflöt 8",
    "Vesturgata 59",
    "Stigahlíð 68",
    "Hólmsheiði fjárb.",
    "Laugavegur 6",
    "Skarfagarðar 4",
    "Dalbraut 3",
    "Fellsvegur",
    "Grundarstígur 2A",
    "Bankastræti 12",
    "Gylfaflöt 10-12",
    "Suðurlandsbraut 2",
    "Vatnsstígur 9a",
    "Laugavegur 4",
    "Safamýri 5",
    "Álfabakki 2d",
    "Grandagarður 11",
    '5">Hagamelur 47',
    "Borgartún 28",
    "Dragháls 14-16",
    "Fjölnisvegur 14",
    "Rekagrandi 14 - Leikskólinn Gullborg",
    "Búðagerði  1-7",
    "Ármúli 34",
    "Sólvallagata 47",
    "Lindargata 57-66",
    "Meistari- dúkalagningameistari",
    "Lautarvegur 34",
    "Rangársel 10-14",
    "Blikastaðavegur 2-8",
    "Laugavegur 34A",
    "Ægisíða 102",
    "Sogavegur 172",
    "Vesturhús 2",
    "Haukdælabraut 20",
    "Keilufell 15",
    "Efstaleiti 2C",
    "Skaftahlíð 24",
    "Reynihlíð",
    "Skeljagrandi 15",
    "Dalhús 44, 46, 48, 50 og 52",
    "Suðurhlíð 36",
    "Skerplugata 3",
    "Vegamótastígur 4",
    "Maríubaugur 5-11",
    "Tryggvagata 12",
    "Bakkastaðir 113",
    "Skipholt 33",
    "Ystasel 37",
    "Skildinganes 26",
    "Ránargata 29A",
    "Kleppsvegur 104",
    "Skútuvogur 2",
    "Dúfnahólar 2-6",
    "Kleifarvegur 6",
    "Öldugata 53",
    "Kleifarsel 28",
    "Reynimelur 38",
    "Haukdælabraut 5-9",
    "Bústaðavegur 145",
    "Hverfisgata 90",
    "Rauðalækur 21",
    "Arnarholt",
    "Norðurgrafarvegur 3",
    "Baldursgata 25B",
    "Óðinstorg reitur 1.181.0",
    "Garðsstaðir 2-10, nr. 6",
    "Fannafold 144-150",
    "Melbær 31-43",
    "Miðtún 20",
    "Gylfaflöt 14",
    '63">Vatnagarðar 8',
    "Silfratjörn 26-32",
    "Gissurargata 2",
    "Langholtsvegur 87",
    "Kjalarnes, Esjuberg",
    "Mávahlíð 9",
    "Háaleitisbraut 66",
    "Barmahlíð 38",
    "Hringbraut  35-49",
    "Fjólugata 19",
    "Álftamýri 1 - 5",
    "Barmahlíð 36",
    "Grensásvegur 52-60",
    "Hlíðarendi 14",
    "Bolholt 5-5a",
    "Gufunesvegur 4",
    "Gylfaflöt 16-18",
    "Bergþórugata 6A",
    "Ránargata 46",
    "Hverfisgata 66A",
    "Ljárskógar 29",
    "Réttarháls 2",
    "Kjalarvogur 10A",
    "Hverfisgata 58",
    "Skúlatún 4",
    "Eiríksgata 2",
    "Kistumelur 16",
    "Sólheimar 23",
    "Neshagi 4",
    "Nóatún 17",
    "Maríubaugur 15",
    "Sóleyjargata 25",
    "Laugavegur 8",
    "Karfavogur 25",
    "Grettisgata 9A og 9B",
    "Sörlaskjól 66",
    "Túngata 26",
    '33">Stakkahlíð 1',
    "Fiskislóð 2-8",
    "Gvendargeisli 118-126",
    "Tryggvagata 19",
    "Kleppsvegur 90",
    "Haukahlíð 2",
    "Kvisthagi 1",
    "Austurgerði 11",
]

CITY = "Reykjavík"


if __name__ == "__main__":
    from planitor.database import db_context

    with db_context() as db:
        tests_geo(db)
