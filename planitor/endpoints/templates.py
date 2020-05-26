import datetime as dt
from urllib.parse import urlparse

from starlette.templating import Jinja2Templates

from planitor import hashids, config
from planitor.utils.timeago import timeago


def human_date(date: dt.datetime) -> str:
    MONTHS = [
        u"janúar",
        u"febrúar",
        u"mars",
        u"apríl",
        u"maí",
        u"júní",
        u"júlí",
        u"ágúst",
        u"september",
        u"október",
        u"nóvember",
        u"desember",
    ]
    return "{}. {}, {}".format(date.day, MONTHS[date.month - 1], date.year)


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    {
        "h": hashids,
        "urlparse": urlparse,
        "timeago": timeago,
        "human_date": human_date,
        "DEBUG": config("DEBUG", cast=bool, default=False),
    }
)
