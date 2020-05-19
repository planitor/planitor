import sentry_sdk
from hashids import Hashids
from reynir import Greynir
from sentry_dramatiq import DramatiqIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.config import Config
from starlette.datastructures import Secret

greynir = Greynir()
hashids = Hashids(salt="planitor", min_length=4)

config = Config(".env")

sentry_dsn = config("SENTRY_DSN", cast=Secret)
if sentry_dsn is not None:
    sentry_sdk.init(
        str(sentry_dsn), integrations=[SqlalchemyIntegration(), DramatiqIntegration()]
    )
