import datetime as dt
from urllib.parse import urlparse

import imgix
from markupsafe import Markup
from starlette.templating import Jinja2Templates

from planitor import config, hashids
from planitor.utils.timeago import timeago


class Imgix:
    builder = imgix.UrlBuilder("planitor.imgix.net", sign_key=config.get("IMGIX_TOKEN"))

    def __call__(self, path: str, params: dict = None):
        return Markup(self.builder.create_url(path, params))


def human_date(date: dt.datetime) -> str:
    MONTHS = [
        "janúar",
        "febrúar",
        "mars",
        "apríl",
        "maí",
        "júní",
        "júlí",
        "ágúst",
        "september",
        "október",
        "nóvember",
        "desember",
    ]
    return "{}. {}, {}".format(date.day, MONTHS[date.month - 1], date.year)


templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    {
        "h": hashids,
        "urlparse": urlparse,
        "timeago": timeago,
        "human_date": human_date,
        "imgix": Imgix(),
        "DEBUG": config("DEBUG", cast=bool, default=False),
    }
)
