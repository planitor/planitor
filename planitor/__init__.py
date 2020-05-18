from starlette.config import Config
from starlette.datastructures import Secret
from hashids import Hashids
from reynir import Greynir
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

greynir = Greynir()
hashids = Hashids(salt="planitor", min_length=4)

config = Config(".env")

sentry_dsn = config("SENTRY_DSN", cast=Secret)
if sentry_dsn is None:
    sentry_sdk.init(sentry_dsn, integrations=[SqlalchemyIntegration()])
