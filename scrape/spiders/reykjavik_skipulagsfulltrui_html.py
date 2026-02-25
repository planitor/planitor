"""
Reykjavík Skipulagsfulltrúi HTML Spider

Scrapes planning officer meeting minutes from reykjavik.is HTML pages.
The new format (2023+) uses HTML pages instead of the old gamli.rvk.is format.
"""

import datetime as dt
import re
from urllib.parse import urljoin

import scrapy
from scrapy.http import Request

BASE_URL = "https://reykjavik.is"

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
    match = re.search(r"(\d{1,2})\.\s+(\w+)\s+kl\.\s+(\d{1,2}):(\d{2})", text)
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

            # Extract attachments from <ul><li><a> elements
            attachments = []
            for link in item.css('ul li a'):
                href = link.attrib.get("href", "")
                label = link.css("::text").get("").strip()
                if href and label:
                    if not href.startswith("http"):
                        href = urljoin(BASE_URL, href)
                    attachments.append({"url": href, "label": label})

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
