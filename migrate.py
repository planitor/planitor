""" Purpose: Make it fast and easy to migrate dev database.

Compares two schemas

1. Temporary, random named and empty database based on the current
declarative models in the dev codebase.
2. Current dev schema.

Prints a migration script and offers to run it, if there is a diff.

"""

import os
from pathlib import Path
from sqlalchemy import text as sa_text
from migra import Migration


def sync():
    from sqlbag import S, temporary_database as temporary_db

    DB_URL = "postgresql://planitor:@localhost/planitor"

    with temporary_db() as TEMP_DB_URL:
        os.environ["DATABASE_URL"] = TEMP_DB_URL
        from planitor.database import engine, Base
        from planitor.models import _all  # noqa, needed to register models
        from sqlalchemy_utils import register_composites

        engine.execute("create extension fuzzystrmatch;")
        engine.execute(
            "CREATE TYPE entity_mention_type AS "
            "(entity_id VARCHAR, start INTEGER, end_ INTEGER);"
        )
        with engine.connect() as connection:
            register_composites(connection)
        Base.metadata.create_all(engine)

        project_dir = Path(__file__).parent.parent

        with open(project_dir.absolute() / "sql" / "dramatiq.sql") as fp:
            escaped_sql = sa_text(fp.read())
            engine.execute(escaped_sql)

        with S(DB_URL) as s_current, S(TEMP_DB_URL) as s_target:
            m = Migration(s_current, s_target)
            m.set_safety(False)
            m.add_all_changes()

            if m.statements:
                print("THE FOLLOWING CHANGES ARE PENDING:", end="\n\n")
                print(m.sql)
                print()
                if input("Apply these changes?") == "yes":
                    print("Applying...")
                    m.apply()
                else:
                    print("Not applying.")
            else:
                print("Already synced.")


if __name__ == "__main__":
    sync()
