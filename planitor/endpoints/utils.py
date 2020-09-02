from sqlalchemy.orm import Session
from fastapi import HTTPException

from planitor.models import Entity


def _get_entity(db: Session, kennitala: str, slug: str = None) -> Entity:
    entity = db.query(Entity).filter(Entity.kennitala == kennitala).first()
    if entity is None or (slug is not None and entity.slug != slug):
        raise HTTPException(status_code=404, detail="Kennitala fannst ekki")
    return entity
