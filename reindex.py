import typer

from planitor.postprocess import (
    update_minute_search_vector,
    _update_minute_search_vector,
)
from planitor.database import db_context
from planitor.models import Meeting, Minute


def main(last: int = 0, force: bool = False, worker: bool = False):
    """Reindex minutes from latest to oldest."""

    with db_context() as db:
        query = db.query(Minute).join(Meeting)

        if not force:
            query = query.filter(Minute.lemmas == None)  # noqa

        query = query.order_by(Meeting.start.desc())

        if last > 0:
            query = query.limit(last)

        for minute in query:
            try:
                if worker:
                    lemmas = []
                    update_minute_search_vector.send(minute.id)
                else:
                    _update_minute_search_vector(minute, db=db)
                    lemmas = minute.lemmas
            except KeyboardInterrupt:
                print("^C")
                break
            print(
                "Indexing Minute:{} → {}".format(
                    minute.id, ", ".join(list(lemmas)[:10])
                )
            )


if __name__ == "__main__":
    typer.run(main)
