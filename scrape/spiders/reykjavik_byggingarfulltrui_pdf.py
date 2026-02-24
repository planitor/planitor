"""
Reykjavík Byggingarfulltrúi PDF Spider

Scrapes building permit meeting minutes from PDF files on reykjavik.is
The new format (2021+) uses PDFs instead of the old gamli.rvk.is HTML pages.
"""

import datetime as dt
import io
import re
import tempfile
from pathlib import Path
from urllib.parse import urljoin

import pdfplumber
import scrapy
from scrapy.http import Request

BASE_URL = "https://reykjavik.is"
FUNDARGERDIR_URL = "https://reykjavik.is/byggingarmal/fundargerdir-byggingarfulltrua"

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


def parse_date_from_filename(filename: str):
    """Parse date from PDF filename like 'afgreidslufundur-byggingarfulltrua-3.-februar-2026.pdf'"""
    patterns = [
        r"(\d{1,2})[._-]\s*(\w+)[._-]\s*(\d{4})",
        r"(\d{1,2})[._\s]+(\w+)[._\s]+(\d{4})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename.lower())
        if match:
            day, month_name, year = match.groups()
            month_name = month_name.replace("_", "").replace("-", "")
            month = MONTHS_IS.get(month_name)
            if month:
                return dt.datetime(int(year), month, int(day))
    return None


def parse_date_from_text(text: str):
    """Parse date from PDF content like 'Árið 2026, þriðjudaginn 3. febrúar kl. 13:00'"""
    match = re.search(
        r"Árið\s+(\d{4}).*?(\d{1,2})\.\s+(\w+)\s+kl\.\s+(\d{1,2}):(\d{2})",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        year, day, month_name, hour, minute = match.groups()
        month = MONTHS_IS.get(month_name.lower())
        if month:
            return dt.datetime(int(year), month, int(day), int(hour), int(minute))
    return None


def extract_meeting_number(text: str):
    """Extract meeting number from text like '1242. fund'"""
    match = re.search(r"(\d+)\.\s*fund", text)
    if match:
        return match.group(1)
    return None


def extract_status(text: str):
    """Extract decision status from remarks text"""
    if not text:
        return None
    text_lower = text.lower()
    
    if re.search(r"\bsamþykkt\b", text_lower):
        return "samþykkt"
    if re.search(r"\bfrestað\b", text_lower):
        return "frestað"
    if re.search(r"\bsynjað\b", text_lower):
        return "synjað"
    if re.search(r"\bvísað til\b", text_lower):
        return "vísað"
    return None


def parse_pdf_content(pdf_bytes: bytes, url: str):
    """Parse PDF content and extract meeting data
    
    PDF format:
    1. Ármúli 17 (01.264.004) 103527 Mál nr. BN057410
    460616-0420 MAL ehf., Nökkvavogi 26, 104 Reykjavík
    Sótt er um leyfi til að breyta skrifstofuhúsnæði...
    Gjald kr. 11.200
    Frestað.
    Lagfæra skráningu.
    """
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    # Extract metadata
    date = parse_date_from_text(full_text) or parse_date_from_filename(url)
    meeting_num = extract_meeting_number(full_text)
    
    # Parse agenda items
    # Format: "1. Ármúli 17 (01.264.004) 103527 Mál nr. BN057410"
    # The pattern is: number. Address (property_id) case_number Mál nr. serial
    item_pattern = re.compile(
        r"^(\d+)\.\s+(.+?)\s+\(\d+\.\d+\.\d+\)\s+\d+\s+Mál\s+nr\.\s+(BN\d+)",
        re.MULTILINE
    )
    
    matches = list(item_pattern.finditer(full_text))
    minutes = []
    
    for i, match in enumerate(matches):
        item_num = int(match.group(1))
        address = match.group(2).strip()
        case_serial = match.group(3)
        
        # Get text until next item or end
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        item_text = full_text[start_pos:end_pos].strip()
        
        # Split into lines
        lines = [ln.strip() for ln in item_text.split("\n") if ln.strip()]
        
        # Parse the item content:
        # - First line is often the applicant (kennítala + name)
        # - Lines starting with "Sótt er um" are the inquiry
        # - "Gjald kr." is the fee line (skip)
        # - Status line: "Samþykkt." / "Frestað." / etc.
        # - Lines after status are additional remarks
        
        inquiry_parts = []
        remarks_parts = []
        found_status = False
        status_line = None
        
        for line in lines:
            # Skip fee line
            if line.startswith("Gjald kr."):
                continue
            
            # Skip page numbers
            if re.match(r"^\d+$", line):
                continue
                
            # Check for status line (standalone status word)
            if re.match(r"^(Samþykkt|Frestað|Synjað|Vísað)\b", line, re.IGNORECASE):
                found_status = True
                status_line = line
                continue
            
            if found_status:
                remarks_parts.append(line)
            else:
                inquiry_parts.append(line)
        
        # Build remarks from status line + additional text
        remarks = status_line or ""
        if remarks_parts:
            remarks = (remarks + "\n" + "\n".join(remarks_parts)).strip()
        
        inquiry = "\n".join(inquiry_parts) if inquiry_parts else ""
        
        minutes.append({
            "serial": str(item_num),
            "case_serial": case_serial,
            "case_address": address,
            "headline": address,  # Use address as headline
            "inquiry": inquiry,
            "remarks": remarks,
            "entities": [],  # No individual kennitalas in PDF (removed by source)
        })
    
    return {
        "url": url,
        "name": meeting_num,
        "start": date,
        "description": "",
        "minutes": minutes,
    }


class ReykjavikByggingarfulltruiPdfSpider(scrapy.Spider):
    """Spider for PDF-based byggingarfulltrúi meetings (2021+)"""
    
    municipality_slug = "reykjavik"
    council_type_slug = "byggingarfulltrui"
    
    name = "reykjavik_byggingarfulltrui_pdf"
    
    custom_settings = {
        "DOWNLOAD_MAXSIZE": 10485760,  # 10MB max for PDFs
        "DOWNLOAD_TIMEOUT": 60,
    }
    
    def __init__(self, year=None, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year_filter = int(year) if year else None
        self.limit = int(limit) if limit else None
        self.start_urls = [FUNDARGERDIR_URL]
    
    def parse(self, response):
        """Parse the fundargerdir page to find PDF links"""
        pdf_links = response.css('a[href*=".pdf"]::attr(href)').getall()
        
        # Filter to byggingarfulltrui PDFs
        pdf_links = [
            link for link in pdf_links 
            if "byggingarfulltr" in link.lower() or "afgreidslufund" in link.lower()
        ]
        
        count = 0
        for href in pdf_links:
            # Apply year filter if specified
            if self.year_filter:
                date = parse_date_from_filename(href)
                if date and date.year != self.year_filter:
                    continue
            
            full_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
            
            yield Request(
                full_url,
                callback=self.parse_pdf,
                meta={"pdf_url": full_url},
            )
            
            count += 1
            if self.limit and count >= self.limit:
                break
    
    def parse_pdf(self, response):
        """Parse a PDF response"""
        pdf_url = response.meta["pdf_url"]
        
        try:
            meeting_data = parse_pdf_content(response.body, pdf_url)
            yield meeting_data
        except Exception as e:
            self.logger.error(f"Failed to parse PDF {pdf_url}: {e}")
