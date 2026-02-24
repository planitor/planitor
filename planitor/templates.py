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
    """imgproxy wrapper for templates - drop-in replacement for imgix."""

    def __call__(self, path: str, params: dict = None):
        """Generate imgproxy URL for an S3 path or full URL.
        
        Args:
            path: S3 key (e.g., "production/attachments/123.pdf") or full URL
            params: Optional params like width, height (mapped to imgproxy options)
        """
        # Build full S3 URL if just a path
        if not path.startswith("http"):
            # Assume S3 bucket URL
            url = f"https://planitor.s3.eu-west-1.amazonaws.com/{path}"
        else:
            url = path
        
        # Map common imgix params to imgproxy options
        width = params.get("w", 0) if params else 0
        height = params.get("h", 0) if params else 0
        
        proxy = _imgproxy_builder(url, width=width, height=height)
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
        "imgix": ImageProxy(),  # Legacy name kept for template compatibility
        "imgproxy": ImageProxy(),  # New name
        "DEBUG": DEBUG,
        "FRONTEND": frontend_snippet,
    }
)
