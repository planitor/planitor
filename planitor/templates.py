from pathlib import Path
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


DEBUG = config("DEBUG", cast=bool, default=False)

frontend_snippet_path = Path(__file__).resolve().parent.parent / "dist" / "index.html"

with open(frontend_snippet_path) as fp:
    frontend_snippet = fp.read().replace(
        "/index", "http://localhost:1234/index" if DEBUG else "/dist/index"
    )

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    {
        "h": hashids,
        "urlparse": urlparse,
        "timeago": timeago,
        "human_date": human_date,
        "imgix": Imgix(),
        "DEBUG": DEBUG,
        "FRONTEND": frontend_snippet,
    }
)
