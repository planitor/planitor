from typing import List
import re
import datetime as dt
import scrapy
from scrapy.http import Response
from requests.utils import requote_uri

from planitor.geo import get_address_lookup_params, lookup_address


INDEX_URL = (
    "https://www.arborg.is/stjornsysla/stjornkerfi/fundargerdir/searchmeetings.aspx"
)
MEETING_URL = "https://www.arborg.is/stjornsysla/stjornkerfi/fundargerdir/DisplayMeeting.aspx?id={}&text="

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

data = {
    "__VIEWSTATE": "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",
    "__VIEWSTATEGENERATOR": "662119E5",
    "__EVENTVALIDATION": "GOJCeYqFLuJdmcuLH0X06Nh2N4GdZw/CrQKn/Dnu+oY8z0PyLHP9c4FqDgSfxpCLcC66obCXxRzckI6iJBDDarXvBZFmORiNhk3GVhGX9Whcj+M3VbRYd+COGbrFrxh/0MrngGVvFnJ15N8DfwjTRhIEOJt2JJw3DFKM16EOWCxHuW7DwVZTMwLgdHIMS4Ze0c5ksnB/HDJsAEnsUfRdmjp51FmqGQTCJtZc8Wt5IN1uq4E5hnwAVtrWR5AjZkY2T7uIXPtOJsVkl/tMpcspn7y9LVGpHnqhnEt0KkM1K58jRluabv6au6lXayNBnSVwSARvRjAks0jys7NxBEJgCXAZIYB2o8ygkemyJH5AgK/YRvumrDlxHjBn41y/PHySV82NDwLb3XOIXgVsXkUYiC//fWHlcmaVnSjrdsvZl1wq/b8VeVHqH2rXV/GoNTdH2Ux55l6KFgQyKFhSvZc4+/xYkHGkwVoJsyjRfbsd6s8=",
    "txtNumber": "",
    "txtText": "",
    "CommitButton": "",
}


council_form_values = {
    "Afgreiðslufundur byggingarfulltrúa": "byggingarfulltrui",
    "Afgreiðslunefnd byggingarfulltrúa": "byggingarfulltrui",
    "Skipulags og byggingarnefnd": "skipulagsrad",
    "Bæjarráð": "borgarrad",
    "Bæjarstjórn": "borgarstjorn",
}


PLACENAMES = (
    "Sandvík",
    "Stokkseyri",
    "Eyrarbakki",
    "Selfoss",
)

POSTCODES = (800, 801, 802, 820, 825)


def get_address(address):
    """Address is used in the headline. Attempt to extract it to create a clean
    address string (which will be parsed again) in the postprocessing
    pipeline."""

    def inner(address, placename):
        street, number, letter = get_address_lookup_params(address)
        iceaddr = lookup_address(street, number, letter, placename)
        if iceaddr is None:
            iceaddr = lookup_address(address.split()[0], None, None, placename)
        if iceaddr is not None:
            address = iceaddr["heiti_nf"]
            if iceaddr["husnr"]:
                address += " " + str(iceaddr["husnr"]) + (iceaddr["bokst"] or "")
            return address

    for placename in PLACENAMES:
        match = inner(address, placename)
        if match:
            return match


def take_responses(paragraphs: List[str]):

    indexes = []
    pattern = (
        r"(?:Áheyrnarfulltrúi|Fulltrúar|Fulltrúi) .+ (?:leggur|leggja) "
        r"fram svohljóðandi (?:gagn)?bókun:"
    )
    for i, segment in enumerate(paragraphs):
        if re.match(pattern, segment):
            indexes.append(i)

    for i in indexes:
        yield paragraphs[i : i + 2]

    for i in indexes[::-1]:
        paragraphs.pop(i + 1)
        paragraphs.pop(i)


def get_segment_with_linebreaks(node):
    string = ""
    for line in node.xpath("(.//br | .//text())").getall():
        string += line.replace("\n", "").replace("<br>", "\n")
    return string


def get_minutes(response):
    subcategory = None
    for el in response.css("#table2>tbody>tr:nth-child(9)>.tdborder>table>tbody>tr"):
        if el.css("td.underline"):
            subcategory = el.css("td::text").get()
        row = el.css("table.bodyclass")
        if not row:
            continue
        header = row.css("tr.plainrow ::text")[1].get().strip()
        case_serial, headline = header.split(" - ", 1)
        serial, case_serial = case_serial.split(". ")
        address = None
        case_address = None
        if " - " in headline:
            address, headline = headline.split(" - ", 1)
            case_address = get_address(address)
            if not case_address:
                case_address = get_address(headline)  # Sometimes it's flipped around
                if case_address:
                    headline = address  # flip it!
                    address = case_address
        paragraphs = []
        attachments = []
        remarks, inquiry, responses = None, None, []

        # Extremely fucked up way to find the position of the headline, sometimes its
        # preceded by some event <tr> like "Magnús Gíslason víkur við afgreiðslu
        # erindisins." ... skip this and count <tr> from the headline
        index_of_headline_tr = list([r.get() for r in row.css("tr")]).index(
            row.css("tr.plainrow")[0].get()
        )
        rows = list(row.css("tr")[index_of_headline_tr + 1 :])
        if rows[0].css("i"):
            inquiry = get_segment_with_linebreaks(rows.pop(0).css("i"))

        for tr in rows:
            links = tr.css("a")
            for link in links:
                # attachment URL’s are obfuscated for some reason, with
                # whitespace characters
                url = "".join(link.css("::attr(href)").re(r"\S"))
                if not url.startswith(
                    "https://ibuagatt.arborg.is/meetingsearch/displaydocument.aspx?"
                ):
                    continue
                url = url.replace("&amp;", "&")
                print(
                    {
                        "type": "application/pdf",
                        "url": requote_uri(url),
                        "length": 0,
                        "label": link.css("::text").get(),
                    }
                )
            else:
                paragraphs.append(get_segment_with_linebreaks(tr.css("td")))

        if paragraphs:
            responses = list(take_responses(paragraphs))
            remarks = "".join(paragraphs)

        yield {
            "case_serial": case_serial,
            "case_address": case_address,
            "headline": headline,
            "inquiry": inquiry,
            "remarks": remarks,
            "serial": serial,
            "subcategory": subcategory,
            "attachments": attachments,
            "responses": responses,
        }


def get_index_request(year: int, council_form_value: str):
    formdata = dict(
        txtDateFrom=f"1.1.{year}",
        txtDateTo=f"31.12.{year}",
        comCommittee=council_form_value,
        **data,
    )
    return scrapy.FormRequest(
        url=INDEX_URL,
        headers=headers,
        formdata=formdata,
        cb_kwargs={"year": year, "council_form_value": council_form_value},
    )


class ArborgSpider(scrapy.Spider):
    name = "arborg"
    municipality_slug = name

    def start_requests(self):
        for council_form_value in list(council_form_values):
            yield get_index_request(dt.date.today().year, council_form_value)

    def parse(self, response: Response, year: int, council_form_value: str):
        meeting_links = response.css("#l_Content table td a")
        council_type_slug = council_form_values[council_form_value]
        for el in meeting_links[:1]:
            yield response.follow(
                el,
                callback=self.parse_meeting,
                cb_kwargs={"council_type_slug": council_type_slug},
            )

        # Add this back if you want to scrape the whole history ... removing after
        # initial import
        return
        if meeting_links:
            request = get_index_request(year - 1, council_form_value)
            yield request

    def parse_meeting(self, response: Response, council_type_slug: str):
        title, name = (
            response.css("#table2>tbody>tr:nth-child(1) td ::text")
            .getall()[0]
            .split(" - ")
        )
        _, location, timing = response.css(
            "#table2>tbody>tr:nth-child(2) td ::text"
        ).getall()

        timing_components = re.findall(r"\d+", timing)

        # Get timing from this format of string: ' 02.09.2020 og hófst hann kl. 13:00'
        if len(timing_components) == 3:
            date, month, year = [int(i) for i in timing_components]
            hour, minute = 0, 0
        else:
            date, month, year, hour, minute = [int(i) for i in timing_components]

        start = dt.datetime(year, month, date, hour, minute)

        minutes = list(get_minutes(response))

        attendant_names = [
            i.strip(" ,").split("\xa0")[0]
            for i in (response.css("#table2>tbody>tr:nth-child(3) td ::text").getall())[
                1:-1
            ]
        ]

        description = "\n".join(
            response.css("#table2>tbody>tr:nth-child(5) td ::text").getall()
        )

        return {
            "url": response.url,
            "name": name,
            "start": start,
            "description": description,
            "attendant_names": attendant_names,
            "minutes": minutes,
            "council_type_slug": council_type_slug,
        }
