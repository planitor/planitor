from typing import List
import re
import datetime as dt
import scrapy
from scrapy.http import Response
from requests.utils import requote_uri

from planitor.geo import get_address_lookup_params, lookup_address


INDEX_URL = "https://www.hafnarfjordur.is/stjornsysla/fundargerdir/SearchMeetings.aspx"
MEETING_URL = (
    "https://www.hafnarfjordur.is/stjornsysla/fundargerdir/DisplayMeeting.aspx?id={}"
)

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

data = {
    "__VIEWSTATE": "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",
    "__VIEWSTATEGENERATOR": "662119E5",
    "__EVENTVALIDATION": "1zsB4OvMJoIhgD/cSvlNmbp6TTTpzUmgTXXOxg9UW7uHAdJh+DV8K5IorGmPyggyUAtgJlsxSXm5RxysoSUFtOb+nyi+zN7YbB0g+2D8HkWGTAcwFZX9qUmBocCoR7PYSVjOIt5H2VBtKfnEkRNBztLMqBcVSfbywYT/Kw02uhtqj0o/coi1pp+n6BVtvO1YwAzU7cSJwIjZGRXxoQCiyElvUWCWFlCMRRyn68+HbUrVdVSftgUg131+yc6Et7G/Cf7WGakrqutx5tgkYbgy3lkZTrdIAxmoAT/+l4H+pAbfIP1sWwIPjxhh5oSnIk5Lz56A8GHCRykSwRrwZ1oT7jX0pnTosOjw2E7J1t3JWWAcRbPdx5R3r0jG4hyRMkhkwpi3QhfQLz4Ct0QYH/asmF4Y4pEEqE+SOivWLf3ZpOsDEyj3PgY0QDHyr6YUZJFJwjD2qE9bZdRHSfCWvAsS/ziCS8r6saZPFVYTLZH8M49/PtksnU/UZRxmSKsT5QqA1Zu9VfbU4yH/Goj0hWNiTOKMzauuGdfgItq17t/aebIVYyUbbqdAZZxhx08Ddl1Kv8RTW3+M81ZxSmnPEKZamvqSq5uck6dXMrwC8ldkr7OxkU+Dd9dCEdxUhpuyH5+pK0bQfeCYoNTKANjq6PGSpw==",
    "txtNumber": "",
    "txtText": "",
    "CommitButton": "Hefja leit",
}


council_form_values = {
    "Afgrei\xF0slufundur skipulags- og byggingarfulltr\xFAa": "byggingarfulltrui",
    "Skipulags- og byggingarráð": "skipulagsrad",
    "Bæjarráð": "borgarrad",
    "Bæjarstjórn": "borgarstjorn",
}


def get_address(address):
    """Address is used in the headline. Attempt to extract it to create a clean
    address string (which will be parsed again) in the postprocessing
    pipeline."""

    street, number, letter = get_address_lookup_params(address)
    iceaddr = lookup_address(street, number, letter, "Hafnarfjörður")
    if iceaddr is None:
        iceaddr = lookup_address(address.split()[0], None, None, "Hafnarfjörður")
    if iceaddr is not None:
        address = iceaddr["heiti_nf"]
        if iceaddr["husnr"]:
            address += " " + str(iceaddr["husnr"]) + (iceaddr["bokst"] or "")
        return address


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


def get_minutes(response):
    subcategory = None
    for el in response.css("#table2>tbody>tr:nth-child(8) table.bodyclass tr"):
        if el.css("td.underline"):
            subcategory = el.css("td::text").get()
        row = el.css("table.bodyclass")
        if not row:
            continue
        header = row.css("tr.plainrow ::text")[1].get().strip()
        case_serial, headline = header.split(" - ", 1)
        serial, case_serial = case_serial.split(". ")
        if ", " in headline:
            address, _ = headline.split(", ", 1)
            case_address = get_address(address)
        else:
            address = None
            case_address = None
        paragraphs = []
        for tr in row.css("tr")[1:]:
            for line in tr.css("td").xpath("(.//br | .//text())").getall():
                paragraphs.append(line.replace("<br>", "\n"))
        attachments = []
        for el in row.css("a"):
            # attachment URL’s are obfuscated for some reason, with whitespace characters
            url = "".join(el.css("::attr(href)").re(r"\S"))
            url = url.replace("&amp;", "&")
            attachments.append(
                {
                    "type": "application/pdf",
                    "url": requote_uri(url),
                    "length": 0,
                    "label": el.css("::text").get(),
                }
            )

        remarks, inquiry, responses = None, None, []
        if paragraphs:
            responses = list(take_responses(paragraphs))
            remarks = "\n".join(paragraphs).strip("\n")
        yield {
            "case_serial": case_serial,
            "case_address": case_address,
            "headline": headline,
            "inquiry": inquiry or None,
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


class HafnarfjordurSpider(scrapy.Spider):
    name = "hafnarfjordur"
    municipality_slug = name

    def start_requests(self):
        for council_form_value in council_form_values:
            yield get_index_request(dt.date.today().year, council_form_value)

    def parse(self, response: Response, year: int, council_form_value: str):
        meeting_links = response.css("#l_Content table td a")
        council_type_slug = council_form_values[council_form_value]
        for el in meeting_links:
            yield response.follow(
                el,
                callback=self.parse_meeting,
                cb_kwargs={"council_type_slug": council_type_slug},
            )
        # Add this back if you want to scrape the whole history ... removing after
        # initial import
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

        # Get timing from this format of string: ' 02.09.2020 og hófst hann kl. 13:00'
        date, month, year, hour, minute = [int(i) for i in re.findall(r"\d+", timing)]
        start = dt.datetime(year, month, date, hour, minute)

        minutes = [m for m in get_minutes(response)]

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
