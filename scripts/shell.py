from pprint import pprint
import bpython

from planitor import models
from planitor.database import db_context


def main():

    locals_ = dict(
        [(name, cls) for name, cls in models.__dict__.items() if isinstance(cls, type)]
    )
    locals_["pprint"] = pprint
    with db_context() as db:
        locals_.update(db=db)
        bpython.embed(locals_=locals_)


if __name__ == "__main__":
    main()
