from environs import Env
from hashids import Hashids
from reynir import Greynir
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

greynir = Greynir()
hashids = Hashids(salt="planitor", min_length=4)

env = Env()
env.read_env()

sentry_dsn = env("SENTRY_DSN", None)
if sentry_dsn is None:
    sentry_sdk.init(sentry_dsn, integrations=[SqlalchemyIntegration()])
