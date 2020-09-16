""" Purpose: Make it fast and easy to migrate dev database.

Compares two schemas

1. Temporary, random named and empty database based on the current
declarative models in the dev codebase.
2. Current dev schema.

Prints a migration script and offers to run it, if there is a diff.

"""

import os

import typer
from migra import Migration


def sync(DB_URL: str = "postgresql://planitor:@localhost/planitor"):
    from sqlbag import S
    from sqlbag import temporary_database as temporary_db

    with temporary_db() as TEMP_DB_URL:
        os.environ["DATABASE_URL"] = TEMP_DB_URL
        from sqlalchemy_utils import register_composites

        from planitor.database import Base, engine
        from planitor.models import _all  # noqa, needed to register models

        engine.execute("CREATE EXTENSION IF NOT EXISTS earthdistance CASCADE;")
        engine.execute(
            "CREATE TYPE entity_mention_type AS "
            "(entity_id VARCHAR, start INTEGER, end_ INTEGER);"
        )
        with engine.connect() as connection:
            register_composites(connection)
        Base.metadata.create_all(engine)

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
    typer.run(sync)
