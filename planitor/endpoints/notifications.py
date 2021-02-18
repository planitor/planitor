from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from email_normalize import Normalizer

from planitor import hashids
from planitor.database import get_db
from planitor.templates import templates
from planitor.models.city import Applicant, Case


router = APIRouter()


@router.post("/unsubscribe/{case_id}", tags=["login"])
async def unsubscribe(
    request: Request, email: str, case_id: str, db: Session = Depends(get_db)
):
    try:
        case = db.query(Case).get(hashids.decode(case_id)[0])
    except IndexError:
        raise HTTPException(status_code=404, detail="Fundargerð fannst ekki")
    if not email or "@" not in email:
        return None
    normalizer = Normalizer()
    result = await normalizer.normalize(email)
    for applicant in db.query(Applicant).filter(
        Applicant.email == result.normalized_address, Applicant.case == case
    ):
        applicant.unsubscribed = True
        db.add(applicant)
    db.commit()
    return None


@router.get("/unsubscribe/{case_id}", tags=["login"])
def get_unsubscribe_page(request: Request, case_id: str, email: str):
    return templates.TemplateResponse(
        "unsubscribe.html", {"request": request, "email": email, "case_id": case_id}
    )
