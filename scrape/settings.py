import logging

SPIDER_MODULES = ["scrape.spiders"]
ITEM_PIPELINES = {
    "scrape.pipelines.DatabasePipeline": 100,
}

LOG_LEVEL = "INFO"

# pdfminer/pdfplumber emit per-token DEBUG logs during PDF parsing — silence them
# to keep launchd stderr log from ballooning (multi-GB per run otherwise).
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)

# reykjavik.is SSL needs this, see https://github.com/scrapy/scrapy/issues/2916
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
)
