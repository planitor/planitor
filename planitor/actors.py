import dramatiq
from .database import db_context
from .postprocess import update_minute_with_entity_mentions, update_minute_search_vector
from .attachments import update_pdf_attachment


@dramatiq.actor
def test_actor(num):
    with db_context() as db:
        result = db.execute("select 1;").scalar()
        return result


__all__ = [
    "update_minute_with_entity_mentions",
    "update_minute_search_vector",
    "update_pdf_attachment",
]
