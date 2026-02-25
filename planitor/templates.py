from pathlib import Path
import datetime as dt
from urllib.parse import urlparse

from markupsafe import Markup
from starlette.templating import Jinja2Templates

from planitor import config, hashids
from planitor.utils.timeago import timeago
from planitor.imgproxy import ImgProxy


# imgproxy URL builder for S3 attachments
_imgproxy_builder = ImgProxy.factory(
    proxy_host='https://imgproxy.plex.uno',
    key=config.get("IMGPROXY_KEY"),
    salt=config.get("IMGPROXY_SALT"),
)


class ImageProxy:
    """imgproxy wrapper for templates."""

    def __call__(self, path: str, params: dict = None):
        """Generate imgproxy URL for an S3 path or full URL.

        Args:
            path: S3 key (e.g., "production/attachments/123.pdf") or full URL
            params: Optional dict with w, h, page (1-based), dpr
        """
        if not path.startswith("http"):
            url = f"https://planitor.s3.eu-west-1.amazonaws.com/{path}"
        else:
            url = path

        width = int(params.get("w", 0)) if params else 0
        height = int(params.get("h", 0)) if params else 0

        advanced = []
        if params:
            if "page" in params:
                # imgproxy uses 0-based pages, templates use 1-based
                advanced.append(f"pg:{int(params['page']) - 1}")
            if "dpr" in params:
                advanced.append(f"dpr:{params['dpr']}")

        proxy = _imgproxy_builder(url, *advanced, width=width, height=height)
        return Markup(str(proxy))


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

if frontend_snippet_path.exists():
    with open(frontend_snippet_path) as fp:
        frontend_snippet = fp.read().replace(
            "/index", "http://localhost:1234/index" if DEBUG else "/dist/index"
        )
else:
    frontend_snippet = ""

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    {
        "h": hashids,
        "urlparse": urlparse,
        "timeago": timeago,
        "human_date": human_date,
        "imgproxy": ImageProxy(),
        "DEBUG": DEBUG,
        "FRONTEND": frontend_snippet,
    }
)
