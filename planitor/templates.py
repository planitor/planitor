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
    proxy_host=config.get("IMGPROXY_HOST", default="https://imgproxy.solberg.club"),
    key=config.get("IMGPROXY_KEY", default=""),
    salt=config.get("IMGPROXY_SALT", default=""),
)


MINIO_PUBLIC_BASE = config.get("PAGES_PUBLIC_BASE", default="https://planitor-pages.solberg.club")


class ImageProxy:
    """imgproxy wrapper for templates."""

    def __call__(self, path: str, params: dict = None):
        """Generate imgproxy URL for an S3 path, MinIO page key, or full URL.

        Args:
            path: S3 key, MinIO page key (e.g., "123-page-0.jpg"), or full URL
            params: Optional dict with w, h, dpr
        """
        if not path.startswith("http") and not path.startswith("s3://"):
            if path.endswith(".jpg") and "-page-" in path:
                # MinIO page image — use public URL
                url = f"{MINIO_PUBLIC_BASE}/{path}"
            else:
                url = f"s3://planitor/{path}"
        else:
            url = path

        width = int(params.get("w", 0)) if params else 0
        height = int(params.get("h", 0)) if params else 0

        advanced = []
        if params:
            if "dpr" in params:
                advanced.append(f"dpr:{params['dpr']}")

        proxy = _imgproxy_builder(url, *advanced, width=width, height=height)
        return Markup(str(proxy))


def format_isk(amount) -> str:
    """Format ISK amount with dot thousands separator: 57.000.000 kr."""
    if amount is None:
        return ""
    amount = int(amount)
    s = f"{amount:,}".replace(",", ".")
    return f"{s} kr."


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
        "format_isk": format_isk,
        "DEBUG": DEBUG,
        "FRONTEND": frontend_snippet,
    }
)
