"""Migrate minutes.entity_mentions composite arrays into minute_entity_mentions rows."""

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planitor.database import engine


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS minute_entity_mentions (
    id SERIAL PRIMARY KEY,
    minute_id INTEGER NOT NULL REFERENCES minutes(id),
    entity_id VARCHAR NOT NULL REFERENCES entities(kennitala),
    start INTEGER NOT NULL,
    end_ INTEGER NOT NULL,
    UNIQUE (minute_id, entity_id, start, end_)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS ix_minute_entity_mentions_id
ON minute_entity_mentions (id);
CREATE INDEX IF NOT EXISTS ix_minute_entity_mentions_minute_id
ON minute_entity_mentions (minute_id);
CREATE INDEX IF NOT EXISTS ix_minute_entity_mentions_entity_id
ON minute_entity_mentions (entity_id);
"""

COPY_COMPOSITE_ARRAY_SQL = """
INSERT INTO minute_entity_mentions (minute_id, entity_id, start, end_)
SELECT
    minutes.id,
    mention.entity_id,
    mention.start,
    mention.end_
FROM minutes
CROSS JOIN LATERAL unnest(minutes.entity_mentions) AS mention
WHERE minutes.entity_mentions IS NOT NULL
ON CONFLICT (minute_id, entity_id, start, end_) DO NOTHING;
"""

HAS_OLD_COLUMN_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'minutes'
    AND column_name = 'entity_mentions'
);
"""


def main():
    with engine.begin() as connection:
        connection.execute(text(CREATE_TABLE_SQL))
        connection.execute(text(CREATE_INDEX_SQL))
        has_old_column = connection.execute(text(HAS_OLD_COLUMN_SQL)).scalar()
        if has_old_column:
            connection.execute(text(COPY_COMPOSITE_ARRAY_SQL))


if __name__ == "__main__":
    main()
