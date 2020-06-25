SPIDER_MODULES = ["scrape.spiders"]
ITEM_PIPELINES = {
    "scrape.pipelines.DatabasePipeline": 100,
}

# reykjavik.is SSL needs this, see https://github.com/scrapy/scrapy/issues/2916
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
)
