from planitor.models import *
from planitor.database import get_db

session_ctx = get_db()
db = next(session_ctx)

import bpython

bpython.embed(locals_=locals())
