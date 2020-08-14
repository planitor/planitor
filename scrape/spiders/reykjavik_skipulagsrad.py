from typing import List
import json
import datetime as dt
import re

from bs4 import BeautifulSoup as bs
import scrapy

from planitor.geo import lookup_address, get_address_lookup_params


def parse_entities(string: str) -> dict:
    """
    Turn a flat list into a list of dicts

    >>> parse_entities('660504-2060 Plúsarkitektar ehf, Fiskislóð 31, 101 Reykjavík')
    {'kennitala': '6605042060', 'name': 'Plúsarkitektar ehf', 'address': 'Fiskislóð 31, 101 Reykjavík'}
    """
    assert re.match(r"(\d{6}-\d{4}) ", string)
    _, kennitala, string = re.split(r"(\d{6}-\d{4}) ", string)
    name, *address = string.rsplit(", ", 2)
    return {
        "kennitala": kennitala.replace("-", ""),
        "name": name,
        "address": ", ".join(address),
    }


CASE_SERIAL_RE = re.compile(r"Mál nr\. ((?:[A-Z]{2})\d+)")


def parse_minute_first_line(string: str):
    """
    >>> parse_minute_first_line("Ártúnshöfði, austurhluti, breyting á deiliskipulagi"
    ... "\xa0\xa0 \xa0 (04.071)\xa0\xa0 \xa0Mál nr. SN200134")
    ('Ártúnshöfði, austurhluti, breyting á deiliskipulagi', '(04.071)', 'SN200134')
    >>> parse_minute_first_line("Sumargötur 2020\xa0\xa0 \xa0 \xa0\xa0 \xa0Mál nr. "
    ... "US200121")
    ('Sumargötur 2020', None, 'US200121')
    >>> parse_minute_first_line("Laugavegur, Bolholt, Skipholt, nýtt deiliskipulag"
    ... "\xa0\xa0 \xa0 (01.251.1)\xa0\xa0 \xa0Mál nr. SN190527")
    ('Laugavegur, Bolholt, Skipholt, nýtt deiliskipulag', '(01.251.1)', 'SN190527')
    >>> parse_minute_first_line("Fulltrúar Sjálfstæðisflokksins leggja fram svohljóðandi"
    ... " tillögu. Mál nr. US200136")
    ('Fulltrúar Sjálfstæðisflokksins leggja fram svohljóðandi tillögu.', None, 'US200136')
    """

    stadgreinir, serial = None, None

    pattern = CASE_SERIAL_RE

    match = re.search(pattern, string)
    if match is not None:
        serial = match.group(1)
        string = re.sub(pattern, "", string)

    pattern = r"\([\d\.]{2,}\)"
    match = re.search(pattern, string)
    if match is not None:
        stadgreinir = "{}".format(match.group(0))
        string = re.sub(pattern, "", string)

    headline = re.sub(r" +", " ", string.replace("\xa0", " ")).strip()

    return headline, (stadgreinir or None), (serial or None)


def take_category(paragraphs: List[List[str]]):
    """
    >>> paragraphs = [[''], ['(A) Skipulagsmál']]
    >>> take_category(paragraphs)
    'A'
    >>> assert paragraphs == [['']]
    """
    categories = (
        ("A", "(A) Skipulagsmál"),
        ("B", "(B) Byggingarmál"),
        ("D", "(D) Ýmis mál"),
        ("E", "(E) Samgöngumál"),
        ("E", "(E) Umhverfis- og samgöngumál"),
    )
    text = "".join(paragraphs[-1])  # It’s always the last thing
    for letter, category in categories:
        if category == text:
            paragraphs.pop()
            return letter


def take_entrants_and_leavers(paragraphs: List[List[str]]):
    """
    >>> paragraphs = [
    ... ['Frestað.\xa0'],
    ... ['Erna Bára Hreinsdóttir og Rúna Ásmundsdóttir frá Vegagerðinni taka sæti á fundinum undir þessum lið.\xa0'],
    ... ['-\xa0\xa0 \xa0Kl. 10:53 víkur Kristín Soffía Jónsdóttir af fundi.\xa0',
    ... '-\xa0\xa0 \xa0Kl. 10:53 tekur Sara Björg Sigurðardóttir sæti á fundinum.']]
    >>> list(take_entrants_and_leavers(paragraphs))
    ['- Kl. 10:53 víkur Kristín Soffía Jónsdóttir af fundi.', '- Kl. 10:53 tekur Sara Björg Sigurðardóttir sæti á fundinum.']
    >>> assert len(paragraphs) == 2
    """

    indexes = set()
    pattern = r"-\xa0\xa0 \xa0Kl\.? \d{1,2}:\d{2} .+"

    for i, segments in enumerate(paragraphs):
        for segment in segments:
            if re.match(pattern, segment):
                yield re.sub(
                    r" +", " ", segment.replace("\xa0", "")
                )  # Cleanup the string
                indexes.add(i)

    for i in sorted(indexes, reverse=True):
        paragraphs.pop(i)


def take_participants(paragraphs: List[List[str]]):
    """
    >>> paragraphs = [
    ... ['Frestað.\xa0'],
    ... ['Erna Bára Hreinsdóttir og Rúna Ásmundsdóttir frá Vegagerðinni taka sæti á fundinum undir þessum lið.\xa0'],
    ... [
    ...     '-\xa0\xa0 \xa0Kl. 10:53 víkur Kristín Soffía Jónsdóttir af fundi.\xa0',
    ...     '-\xa0\xa0 \xa0Kl. 10:53 tekur Sara Björg Sigurðardóttir sæti á fundinum.'
    ... ]
    ... ]
    >>> take_participants(paragraphs)
    'Erna Bára Hreinsdóttir og Rúna Ásmundsdóttir frá Vegagerðinni taka sæti á fundinum undir þessum lið.\xa0'
    >>> assert len(paragraphs) == 2
    """

    indexes = set()
    pattern = r"(?:tekur|taka) sæti á fundinum undir þessum lið."
    participant = None

    for i, segments in enumerate(paragraphs):
        segment = "".join(segments)
        if re.search(pattern, segment):
            participant = segment
            indexes.add(i)

    for i in sorted(indexes, reverse=True):
        paragraphs.pop(i)

    return participant


def take_responses(paragraphs: List[List[str]]):
    """
    >>> s = 'Áheyrnarfulltrúi Flokks fólksins leggur fram svohljóðandi bókun:'
    >>> paragraphs = [[''], [s], ['-']]
    >>> list(take_responses(paragraphs))
    [['Áheyrnarfulltrúi Flokks fólksins leggur fram svohljóðandi bókun:', '-']]
    >>> assert paragraphs == [['']]
    """

    indexes = []
    pattern = (
        r"(?:Áheyrnarfulltrúi|Fulltrúar) .+ (?:leggur|leggja) "
        r"fram svohljóðandi (?:gagn)?bókun:"
    )
    for i, segments in enumerate(paragraphs):
        if re.match(pattern, "".join(segments)):
            indexes.append(i)

    for i in indexes:
        yield ["\n".join(_) for _ in paragraphs[i : i + 2]]

    for i in indexes[::-1]:
        paragraphs.pop(i + 1)
        paragraphs.pop(i)


def take_remarks(paragraphs: List[List[str]]):
    remarks = "".join(paragraphs.pop(0))
    return remarks


def get_address(headline):
    """ In skipulagsráð address is not a field per se, but is often used in the headline.
    Attempt to extract it to create a clean address string (which will be parsed again)
    in the postprocessing pipeline. """

    street, number, letter = get_address_lookup_params(headline)
    iceaddr = lookup_address(street, number, letter, "Reykjavík")
    if iceaddr is None:
        iceaddr = lookup_address(headline.split()[0], None, None, "Reykjavík")
    if iceaddr is not None:
        address = iceaddr["heiti_nf"]
        if iceaddr["husnr"]:
            address += " " + str(iceaddr["husnr"]) + (iceaddr["bokst"] or "")
        return address


def process_first_paragraph(paragraph):
    """ Corrects for instances where the title is crudely formatted like this:

    > Umhverfis- og skipulagssvið,&nbsp;
    > ellefu mánaða uppgjör&nbsp;&nbsp; &nbsp; &nbsp;&nbsp; &nbsp;Mál nr. US200038

    This rejoins lines not beginning with kennitala

    We can also encountered orphan lines that should be in the next paragraph.

    """

    first_line = paragraph.pop(0)
    entity_lines = []
    orphan_lines = []
    if "\xa0" in first_line:
        insert_point = first_line.index("\xa0")
    else:
        insert_point = len(first_line)

    for line in paragraph:
        if re.match(r"^\d{6}", line):
            entity_lines.append(line)
        elif len(line) > 80 and not re.search(CASE_SERIAL_RE, line):
            orphan_lines.append([line])
        else:
            first_line = first_line[:insert_point] + line + first_line[insert_point:]

    return first_line, entity_lines, orphan_lines


def parse_minute_el(index: int, el: scrapy.selector.unified.Selector):
    """ From a high level the structure is like this

    **********************************************************************

    {number}. {address or title}, {title} Mál nr {caseid}
    {optional list of entities}

    {inquiry}

    {optional remark}

    {optional list of remarks from politicians, as intro-remarks paragraph pairs}

    {optional list of representatives present for this minute}
        ex: ['Erna Bára Hreinsdóttir og Rúna Ásmundsdóttir frá Vegagerðinni taka sæti á fundinum undir þessum lið.\xa0']
        ex: ['Hjalti Brynjarsson og Grétar Snorrason frá Arkþing - Nordic ehf. taka sæti á fundinum undir þessum lið.']

    {optional list of politicians leaving or entering for this minute, newlines separated}
        ex: [
                '-\xa0\xa0 \xa0Kl. 10:53 víkur Kristín Soffía Jónsdóttir af fundi.\xa0',
                '-\xa0\xa0 \xa0Kl. 10:53 tekur Sara Björg Sigurðardóttir sæti á fundinum.',
            ]

    {optional sub-classification designated by letters in paranthesis}

    **********************************************************************

    There are examples of completely fucked up and unparsable meetings like this one
    https://reykjavik.is/fundargerdir/dagskra-fundar-7-november-2018

    It will result in each minute to not be parsed.

    """

    paragraphs = [
        "".join(p.css("::text").getall()).split("\n")
        # `::text` will remove tags, including <br>, but the markup has \n characters so
        # we can use this to create segment parts
        for p in el.css(".field-name-field-heiti-dagskrarlidar p")
    ]

    first_paragraph = paragraphs.pop(0)
    first_line, entity_lines, orphan_lines = process_first_paragraph(first_paragraph)

    # Sometimes there is no paragraph split and the first paragraph
    # includes the inquiry, which is normally the second paragraph
    # so we move it back
    paragraphs = orphan_lines + paragraphs

    headline, stadgreinir, serial = parse_minute_first_line(first_line)
    if serial is None:
        return None

    entities = [parse_entities(s) for s in entity_lines]

    inquiry = "\n".join(paragraphs.pop(0))

    if paragraphs and paragraphs[0] == ["Tillögunni fylgir greinargerð."]:
        inquiry += "\n\n" + paragraphs.pop(0)[0]

    # We have now treated the first paragraph which is special. The rest is even more
    # unstructured. In short, we have an inquiry, an optional response, then an optional
    # series of minute bookings from  political parties or áheyrnarfulltrúar

    attachments = []
    for _el in el.css("ul>li"):
        attachments.append(
            {
                "type": _el.css("img::attr(title)").get(),
                "url": _el.css("a::attr(href)").get(),
                "length": _el.css("a::attr(type)").get().split("length=")[1],
                "label": _el.css("a::text").get(),
            }
        )

    # Treat lines with <br> as separate
    # lines = sum([line.split("<br>") for line in lines], start=[])

    subcategory = None
    responses = []
    remarks = None
    entrants_and_leavers = []
    participants = None

    if paragraphs:
        responses = list(take_responses(paragraphs))
    if paragraphs:
        subcategory = take_category(paragraphs)
    if paragraphs:
        entrants_and_leavers = list(take_entrants_and_leavers(paragraphs))
    if paragraphs:
        participants = take_participants(paragraphs) or None
    if paragraphs:
        remarks = take_remarks(paragraphs)

    return {
        "headline": headline,
        "inquiry": inquiry,
        "serial": f"{index}. fundarliður",
        "case_serial": serial,
        "case_address": get_address(headline),
        "case_stadgreinir": stadgreinir,
        "entities": entities,
        "subcategory": subcategory,
        "responses": responses,
        "remarks": remarks,
        "entrants_and_leavers": entrants_and_leavers,
        "participants": participants,
        "attachments": attachments,
    }


def get_minutes(response):
    for i, el in enumerate(response.css(".agenda-items>ol>li")):
        yield parse_minute_el(i + 1, el)


"""
Until 2018 it was Umhverfis- og skipulagsráð:
https://reykjavik.is/fundargerdir?field_rad_nefnd_tid=68

From then Skipulags- og samgönguráð:
https://reykjavik.is/fundargerdir?field_rad_nefnd_tid=924

"""

URL = (
    "https://reykjavik.is/views/ajax?field_rad_nefnd_tid={}"
    "&view_name=fundargerdir&view_display_id=block_1"
)


def get_url(page=0):
    url = URL.format(924)  # id for Skipulags- og samgönguráð
    return f"{url}&page={page}"


class ReykjavikSkipulagsradSpider(scrapy.Spider):
    municipality_slug = "reykjavik"
    council_type_slug = "skipulagsrad"
    council_label = "Skipulags- og samgönguráð"
    name = "{}_{}".format(municipality_slug, council_type_slug)
    start_urls = [get_url(page=0)]

    def parse(self, response, page=0):
        soup = bs(json.loads(response.text)[1]["data"], "html5lib")
        count = len(soup.select(".filter-bl-item"))

        for el in soup.select(".filter-bl-item"):
            isodate, _ = el.select_one(".date-display-single").get("content").split("T")
            date = dt.date.fromisoformat(isodate)
            href = el.select_one("a").get("href")
            yield response.follow(href, self.parse_meeting, cb_kwargs={"start": date})

        if count == 20:
            # Keep paginating if we have full pages
            yield response.follow(
                get_url(page=page + 1), self.parse, cb_kwargs={"page": page + 1}
            )

    def parse_meeting(self, response, start):
        name = response.css(".page-header::text").re_first(r"\d+")
        description = ""
        for part in response.css(
            ".field-name-field-inngangur-fyrir-fundargerd p::text"
        ).getall():
            part = part.replace("\xa0", " ")
            if part.strip():
                description += f"{part}\n"
        description = re.sub(
            r"(\n)+", "\n", description
        )  # normalize multiple \n to a single linebreak

        minutes = [m for m in get_minutes(response) if m]  # filter out unparsable minutes

        yield {
            "url": response.url,
            "name": name,
            "start": start,
            "description": description,
            "minutes": minutes,
        }
