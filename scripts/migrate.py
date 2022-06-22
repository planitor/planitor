""" Purpose: Make it fast and easy to migrate dev database.

Compares two schemas

1. Temporary, random named and empty database based on the current
declarative models in the dev codebase.
2. Current dev schema.

Prints a migration script and offers to run it, if there is a diff.

"""

import os
from contextlib import contextmanager

import typer
from migra import Migration
from sqlbag import S
from sqlbag.createdrop import create_database, temporary_name, drop_database


@contextmanager
def temporary_database():
    """
    Args:
        dialect(str): Type of database to create (either 'postgresql', 'mysql', or 'sqlite').
        do_not_delete: Do not delete the database as this method usually would.
    Creates a temporary database for the duration of the context manager scope. Cleans it up when finished unless do_not_delete is specified.
    PostgreSQL, MySQL/MariaDB, and SQLite are supported. This method's mysql creation code uses the pymysql driver, so make sure you have that installed.
    """

    tempname = temporary_name()

    url = "postgresql://jokull@host.docker.internal/{}".format(tempname)

    try:
        create_database(url)
        yield url
    finally:
        drop_database(url)


def sync(
    DB_URL: str = os.environ.get(
        "DATABASE_URL", "postgresql://planitor:@localhost/planitor"
    )
):

    with temporary_database() as TEMP_DB_URL:
        os.environ["DATABASE_URL"] = TEMP_DB_URL
        from planitor.database import Base, engine
        from planitor.models import _all  # noqa, needed to register models
        from sqlalchemy_utils import register_composites

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
