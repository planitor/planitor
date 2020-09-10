import dramatiq
import sentry_sdk
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.results import Results
from dramatiq.middleware import GroupCallbacks
from dramatiq.results.backends import RedisBackend, StubBackend
from dramatiq.rate_limits.backends.redis import RedisBackend as RateLimiterRedisBackend
from hashids import Hashids
from reynir import Greynir
from sentry_dramatiq import DramatiqIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.config import Config
from starlette.datastructures import Secret

greynir = Greynir()
hashids = Hashids(salt="planitor", min_length=4)

config = Config(".env")
DEBUG = config("DEBUG", cast=bool, default=False)
ENV = config("ENV", default="production")
SENTRY_DSN = config("SENTRY_DSN", cast=Secret)

if not DEBUG and SENTRY_DSN:
    sentry_sdk.init(
        str(SENTRY_DSN),
        integrations=[SqlalchemyIntegration(), DramatiqIntegration()],
        release=config("RENDER_GIT_COMMIT", default=None),
    )


if config("REDIS_URL", default=False):
    broker = RedisBroker(url=config("REDIS_URL"))
    broker.add_middleware(Results(backend=RedisBackend(url=config("REDIS_URL"))))
    broker.add_middleware(
        GroupCallbacks(
            rate_limiter_backend=RateLimiterRedisBackend(url=config("REDIS_URL"))
        )
    )
else:
    backend = StubBackend()
    broker = StubBroker()

dramatiq.set_broker(broker)
