from pprint import pprint

import bpython

from planitor import greynir, models
from planitor.database import db_context


def main():

    locals_ = dict(
        [(name, cls) for name, cls in models.__dict__.items() if isinstance(cls, type)]
    )
    with db_context() as db:
        locals_.update(db=db, greynir=greynir, pprint=pprint)
        bpython.embed(locals_=locals_)


if __name__ == "__main__":
    main()
