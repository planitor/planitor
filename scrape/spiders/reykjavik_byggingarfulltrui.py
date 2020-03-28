import datetime as dt
import re

import scrapy
from bs4 import BeautifulSoup as bs

MEETING_URL = "http://gamli.rvk.is/vefur/owa/{}"
YEAR_URL = "http://gamli.rvk.is/vefur/owa/edutils.parse_page?nafn=BN2MEN{}"
YEARS = [
    "96",
    "97",
    "98",
    "99",
    "00",
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
]

MONTHS = [
    (u"Jan", u"janúar"),
    (u"Feb", u"febrúar"),
    (u"Mar", u"mars"),
    (u"Apr", u"apríl"),
    (u"maí", u"maí"),
    (u"jún", u"júní"),
    (u"júl", u"júlí"),
    (u"ágú", u"ágúst"),
    (u"sep", u"september"),
    (u"okt", u"október"),
    (u"nov", u"nóvember"),
    (u"des", u"desember"),
]


def get_minutes(response):
    soup = bs(response.text, "html5lib")
    links = soup.find_all(href=re.compile("edutils.parse_page"))
    for i, link in enumerate(links):
        data = {}
        els = link.parent.previous_sibling.text.split("\n")
        data["case_serial"] = els.pop(0).strip().replace("Umsókn nr. ", "")
        entities = [el for el in els[1:-1] if el]
        data["entities"] = []
        for i in range(0, len(entities), 3):
            kennitala, name, address = entities[i : i + 3]
            data["entities"].append(
                {
                    "kennitala": kennitala.replace("-", "").strip(),
                    "name": name.strip(),
                    "address": address.strip(),
                }
            )
        data["serial"] = link.get("href").split("=")[-1:][0]
        data["case_address"] = link.text.lstrip('">').strip()
        tegund = link.find_next("i")
        data["headline"] = tegund.text.strip()
        text = ""
        for el in tegund.find_next_siblings():
            if el.name == "i":
                break
            if not el.name == "i":
                try:
                    text = text + str(el.next_sibling)
                except AttributeError:
                    pass
        data["remarks"] = "\n".join(tegund.find_next("i").stripped_strings)
        data["inquiry"] = text.strip()
        yield data


class ReykjavikByggingarfulltruiSpider(scrapy.Spider):
    municipality_slug = "reykjavik"
    council_type_slug = "byggingarfulltrui"

    name = "{}_{}".format(municipality_slug, council_type_slug)

    # start_urls = [YEAR_URL.format(year) for year in YEARS]
    start_urls = [YEAR_URL.format("20")]

    def parse(self, response):
        for i, link in enumerate(response.css("menu a")):
            if i > 2:  # TODO remove limit of 2
                continue
            yield response.follow(link, self.parse_meeting)

    def parse_meeting(self, response):
        description = (
            response.xpath("//center[1]/following-sibling::text()[2]").get().strip("\r")
        )

        match = re.search(
            r"Árið (\d+), (\w+) (\d+)\. (\w+) kl\. (\d+):(\d+)", description
        )
        if match is not None:
            year, _, day, month, hour, minute = match.groups()
            for i, (short, long_) in enumerate(MONTHS, 1):
                if month.lower() == long_.lower():
                    month = i
                    break
        start = dt.datetime(*(int(i) for i in (year, month, day, hour, minute)))

        name, _ = re.match(
            r"(\d+)\. fundur (\d+)",
            (
                response.xpath("//center[1]/h2/following-sibling::text()[1]")
                .get()
                .strip("\r")
            ),
        ).groups()

        yield {
            "name": name,
            "start": start,
            "description": description,
            "minutes": list(get_minutes(response)),
        }
