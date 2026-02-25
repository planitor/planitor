"""
Reykjavík HTML Spiders for Skipulagsfulltrúi and Skipulagsráð

Scrapes meeting minutes from reykjavik.is HTML pages.
- Skipulagsfulltrúi (2023+): planning officer meeting minutes
- Skipulagsráð (2024+): umhverfis- og skipulagsráð council meetings
"""

import datetime as dt
import re
from urllib.parse import urljoin

import scrapy
from scrapy.http import Request

BASE_URL = "https://reykjavik.is"

# Case serial pattern matching USK, MSS, SN, BN, US prefixes
CASE_SERIAL_RE = re.compile(r"((?:USK|MSS|SN|BN|US)\d{8,})")

# Listing page for skipulagsfulltrúi meetings
# field_rad_nefnd_tid=923 is "Afgreiðslufundir skipulagsfulltrúa"
INDEX_URL = "https://reykjavik.is/fundargerdir?field_rad_nefnd_tid=923"

MONTHS_IS = {
    "janúar": 1, "januar": 1,
    "febrúar": 2, "februar": 2,
    "mars": 3,
    "apríl": 4, "april": 4,
    "maí": 5, "mai": 5,
    "júní": 6, "juni": 6,
    "júlí": 7, "juli": 7,
    "ágúst": 8, "agust": 8,
    "september": 9,
    "október": 10, "oktober": 10,
    "nóvember": 11, "november": 11,
    "desember": 12,
}


def parse_icelandic_date(text: str):
    """Parse Icelandic date like 'þriðjudaginn 17. febrúar' with year context"""
    match = re.search(r"(\d{1,2})\.\s+(\w+),?\s+kl\.\s+(\d{1,2}):(\d{2})", text)
    if match:
        day, month_name, hour, minute = match.groups()
        month = MONTHS_IS.get(month_name.lower())
        if month:
            return int(day), month, int(hour), int(minute)
    return None


def extract_year_from_text(text: str):
    """Extract year from text like 'Ár 2026' or 'Árið 2026'"""
    match = re.search(r"Ár(?:ið)?\s+(\d{4})", text)
    if match:
        return int(match.group(1))
    return None


def extract_meeting_number(text: str):
    """Extract meeting number from text like '1049. embættisafgreiðslufund'"""
    match = re.search(r"(\d+)\.\s*(?:embættisafgreiðslufund|fund)", text)
    if match:
        return match.group(1)
    return None


def extract_attachments(item):
    """Extract attachments from <ul><li><a> elements in an agenda item"""
    attachments = []
    for link in item.css("ul li a"):
        href = link.attrib.get("href", "")
        label = link.css("::text").get("").strip()
        if href and label:
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            attachments.append({"url": href, "label": label})
    return attachments


class ReykjavikSkipulagsfulltruiHtmlSpider(scrapy.Spider):
    """Spider for HTML-based skipulagsfulltrúi meetings (2023+)"""
    
    municipality_slug = "reykjavik"
    council_type_slug = "skipulagsfulltrui"
    
    name = "reykjavik_skipulagsfulltrui_html"
    
    def __init__(self, year=None, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year_filter = int(year) if year else None
        self.limit = int(limit) if limit else None
        self.start_urls = [INDEX_URL]
    
    def parse(self, response):
        """Parse the listing page to find meeting links"""
        # Find links to skipulagsfulltrua meetings
        links = response.css('a[href*="skipulagsfulltrua-fundur"]::attr(href)').getall()
        
        count = 0
        for href in links:
            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            
            yield Request(
                full_url,
                callback=self.parse_meeting,
            )
            
            count += 1
            if self.limit and count >= self.limit:
                break
        
        # Handle pagination if present
        if not self.limit or count < self.limit:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page:
                yield Request(urljoin(BASE_URL, next_page), callback=self.parse)
    
    def parse_meeting(self, response):
        """Parse a meeting page and extract minutes"""
        # Get page text for metadata
        text = response.css('.ContentArticle ::text').getall()
        full_text = ' '.join(t.strip() for t in text if t.strip())

        # Extract meeting metadata
        year = extract_year_from_text(full_text)
        meeting_num = extract_meeting_number(full_text)

        # Apply year filter
        if self.year_filter and year and year != self.year_filter:
            return
        
        # Parse date
        date_parts = parse_icelandic_date(full_text)
        start = None
        if date_parts and year:
            day, month, hour, minute = date_parts
            start = dt.datetime(year, month, day, hour, minute)
        
        # Extract description (attendees etc)
        desc_match = re.search(
            r"Fundinn sátu:(.+?)(?:Þetta gerðist|$)",
            full_text,
            re.DOTALL
        )
        description = desc_match.group(0).strip() if desc_match else ""
        
        minutes = []
        serial = 0
        
        # Parse agenda items from <ol><li> structure
        # Each <li id="agenda_XXX"> contains paragraphs
        for item in response.css('ol li[id^="agenda_"]'):
            paragraphs = item.css('p::text').getall()
            if not paragraphs:
                continue

            # First paragraph is headline with USK number
            headline_text = paragraphs[0].strip() if paragraphs else ""

            # Look for USK case number
            usk_match = re.search(r'(USK\d+)', headline_text)
            if not usk_match:
                continue

            serial += 1
            case_serial = usk_match.group(1)

            # Extract headline (text before USK, remove trailing dash)
            headline = headline_text[:usk_match.start()].strip()
            headline = re.sub(r'\s*-\s*$', '', headline).strip()

            # Remove leading number like "1. "
            headline = re.sub(r'^\d+\.\s*', '', headline).strip()

            # Extract address from headline segments separated by " - "
            # Preserves "Fiskislóð 15-21" (no spaces around dash)
            segments = re.split(r'\s+[-–]\s+', headline)
            address = segments[0].strip()  # default: first segment (location name)
            addr_pattern = re.compile(
                r'^[\w\s]+\d+(?:\w?(?:-\d+\w?)?)?\s*$'
            )
            for segment in segments:
                if addr_pattern.match(segment.strip()):
                    address = segment.strip()
                    break

            # Remaining paragraphs: inquiry and remarks
            # Filter out "Fylgigögn" header text
            remaining = [
                p for p in paragraphs[1:]
                if p.strip() and p.strip() != "Fylgigögn"
            ]

            attachments = extract_attachments(item)

            # Decision keywords that indicate remarks
            decision_keywords = [
                'Samþykkt', 'Frestað', 'Synjað', 'Vísað til',
                'Ekki eru gerðar', 'Umsögn skipulagsfulltrúa, dags',
                'Neikvætt',
            ]

            inquiry_parts = []
            remarks_parts = []
            found_decision = False

            for para in remaining:
                para = para.strip()
                if not para:
                    continue

                # Check if this paragraph starts with a decision keyword
                is_decision = any(para.startswith(kw) for kw in decision_keywords)

                if is_decision or found_decision:
                    found_decision = True
                    remarks_parts.append(para)
                else:
                    inquiry_parts.append(para)

            inquiry = '\n'.join(inquiry_parts)
            remarks = '\n'.join(remarks_parts)

            minutes.append({
                "serial": str(serial),
                "case_serial": case_serial,
                "case_address": address,
                "headline": headline,
                "inquiry": inquiry,
                "remarks": remarks,
                "entities": [],
                "attachments": attachments,
            })
        
        if not minutes:
            self.logger.warning(f"No minutes found in {response.url}")
            return
        
        yield {
            "url": response.url,
            "name": meeting_num,
            "start": start,
            "description": description,
            "minutes": minutes,
        }


class ReykjavikSkipulagsradHtmlSpider(scrapy.Spider):
    """Spider for HTML-based umhverfis- og skipulagsráð meetings (2024+)

    Merges with existing skipulagsrad council (formerly skipulags- og samgönguráð).
    Meetings start at #322 (Oct 2024). Uses same <li id="agenda_XXX"> DOM structure
    as skipulagsfulltrúa but with different text layout:
    - USK/MSS number at END of text, not in a headline
    - No clean headline paragraph - first <p> is full inquiry text
    - <br> separators within <p> for decisions
    - Bókunir (political statements) after decisions
    """

    name = "reykjavik_skipulagsrad_html"
    municipality_slug = "reykjavik"
    council_type_slug = "skipulagsrad"
    council_label = "Umhverfis- og skipulagsráð"

    INDEX_URL = "https://reykjavik.is/fundargerdir?field_committee_target_id=68"

    # Decision keywords that mark the boundary between inquiry and remarks
    DECISION_KEYWORDS = [
        "Samþykkt",
        "Frestað",
        "Synjað",
        "Vísað til",
        "Vísað frá",
        "Ekki eru gerðar",
        "Umsögn skipulagsfulltrúa, dags",
        "Neikvætt",
        "Jákvætt",
        "Afgreitt",
        "Tillögunni er vísað",
        "Hluti tillögunnar",
        "Lögð fram svohljóðandi bókun",
    ]

    def __init__(self, year=None, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year_filter = int(year) if year else None
        self.limit = int(limit) if limit else None
        self.start_urls = [self.INDEX_URL]

    def parse(self, response):
        """Parse listing page for meeting links"""
        links = response.css(
            'a[href*="umhverfis-og-skipulagsrad"]::attr(href)'
        ).getall()

        # Deduplicate while preserving order, filter to meeting pages only
        seen = set()
        unique_links = []
        for href in links:
            if href not in seen and "/fundargerdir/" in href:
                seen.add(href)
                unique_links.append(href)

        count = 0
        for href in unique_links:
            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            yield Request(full_url, callback=self.parse_meeting)
            count += 1
            if self.limit and count >= self.limit:
                break

        # Pagination
        if not self.limit or count < self.limit:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page:
                yield Request(urljoin(BASE_URL, next_page), callback=self.parse)

    def parse_meeting(self, response):
        """Parse a meeting page and extract minutes"""
        text = response.css(".ContentArticle ::text").getall()
        full_text = " ".join(t.strip() for t in text if t.strip())

        year = extract_year_from_text(full_text)
        meeting_num = extract_meeting_number(full_text)

        if self.year_filter and year and year != self.year_filter:
            return

        date_parts = parse_icelandic_date(full_text)
        start = None
        if date_parts and year:
            day, month, hour, minute = date_parts
            start = dt.datetime(year, month, day, hour, minute)

        # Extract description (attendees)
        desc_match = re.search(
            r"((?:Eftirtaldir|Fundinn sátu).+?)Þetta gerðist",
            full_text,
            re.DOTALL,
        )
        description = desc_match.group(0).strip() if desc_match else ""

        minutes = []
        serial = 0
        addr_pattern = re.compile(r"^[\w\s]+\d+(?:\w?(?:-\d+\w?)?)?\s*$")

        for item in response.css('ol li[id^="agenda_"]'):
            result = self._parse_agenda_item(item, addr_pattern)
            if result is None:
                continue
            serial += 1
            result["serial"] = str(serial)
            minutes.append(result)

        if not minutes:
            self.logger.warning(f"No minutes found in {response.url}")
            return

        yield {
            "url": response.url,
            "name": meeting_num,
            "start": start,
            "description": description,
            "minutes": minutes,
        }

    def _parse_agenda_item(self, item, addr_pattern):
        """Parse a single agenda item <li> and return a minute dict, or None."""
        # Collect all text segments from <p> elements, splitting on <br> via
        # XPath text nodes. Each text node boundary corresponds to a <br>.
        segments = []
        for p in item.css("p"):
            texts = p.xpath(".//text()").getall()
            for t in texts:
                t = t.strip()
                if t and t != "\xa0":
                    segments.append(t)

        if not segments:
            return None

        # Find case serial in any segment
        case_serial = None
        for seg in segments:
            match = CASE_SERIAL_RE.search(seg)
            if match:
                case_serial = match.group(1)
                break

        if not case_serial:
            return None

        attachments = extract_attachments(item)

        # Filter out non-content segments
        filtered = []
        for seg in segments:
            # Skip "Fylgigögn" header
            if seg == "Fylgigögn":
                continue
            # Skip procedural notes (someone joins/leaves the meeting)
            if re.search(r"(?:tekur|taka|tók)\s+sæti", seg):
                continue
            if re.search(r"víkur.*af fundi", seg):
                continue
            # Skip standalone time notations like "- Kl. 9:26..."
            if re.match(r"^[-–]?\s*Kl\.", seg):
                continue
            filtered.append(seg)

        # Strip case serial from segments
        cleaned = []
        for seg in filtered:
            seg = CASE_SERIAL_RE.sub("", seg).strip()
            # Collapse whitespace left by removal
            seg = re.sub(r"\s+", " ", seg).strip()
            if seg:
                cleaned.append(seg)

        if not cleaned:
            return None

        # Split into inquiry and remarks at first decision keyword
        inquiry_parts = []
        remarks_parts = []
        found_decision = False

        for seg in cleaned:
            is_decision = any(seg.startswith(kw) for kw in self.DECISION_KEYWORDS)
            if is_decision or found_decision:
                found_decision = True
                remarks_parts.append(seg)
            else:
                inquiry_parts.append(seg)

        inquiry = "\n".join(inquiry_parts)
        remarks = "\n".join(remarks_parts)

        # Derive headline from first attachment label or first inquiry segment
        headline = ""
        if attachments:
            headline = attachments[0]["label"]
        if not headline and inquiry_parts:
            first = inquiry_parts[0]
            sentence_end = re.search(r"[.!?]\s", first)
            if sentence_end and sentence_end.start() < 120:
                headline = first[: sentence_end.start() + 1]
            else:
                headline = first[:120] + ("..." if len(first) > 120 else "")

        # Extract address from attachment labels or headline
        address = ""
        for att in attachments:
            label_segments = re.split(r"\s+[-–]\s+", att["label"])
            for seg in label_segments:
                seg = seg.strip()
                # Skip case serials and overly long segments (not addresses)
                if CASE_SERIAL_RE.match(seg) or len(seg) > 50:
                    continue
                if addr_pattern.match(seg):
                    address = seg
                    break
            if address:
                break

        if not address and headline:
            headline_segments = re.split(r"\s+[-–]\s+", headline)
            for seg in headline_segments:
                seg = seg.strip()
                if CASE_SERIAL_RE.match(seg) or len(seg) > 50:
                    continue
                if addr_pattern.match(seg):
                    address = seg
                    break

        return {
            "case_serial": case_serial,
            "case_address": address,
            "headline": headline,
            "inquiry": inquiry,
            "remarks": remarks,
            "entities": [],
            "attachments": attachments,
        }
