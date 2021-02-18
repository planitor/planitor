import dramatiq
from sqlalchemy.orm import Session
from planitor import config, hashids
from planitor import mail
from planitor.database import db_context
from planitor.models.city import Minute, Applicant


def _send_applicant_notifications(db: Session, minute: Minute):
    municipality = minute.case.municipality
    applicants = db.query(Applicant).filter(
        Applicant.serial == minute.case.serial,
        Applicant.municipality_id == municipality.id,
    )
    for applicant in applicants:
        if applicant.case is None:
            applicant.case = minute.case
            db.add(applicant)
        if applicant.unsubscribed:
            continue
        mail.send_email(
            email_to=applicant.email,
            subject=" ".join(minute.headline.splitlines()),
            html_template="municipality_case_notification.html",
            context={
                "link": f"https://{config('SERVER_HOST')}/minutes/{minute.id}",
                "unsubscribe_link": (
                    f"https://{config('SERVER_HOST')}"
                    f"/tilkynningar/unsubscribe/{hashids.encode(minute.case.id)}"
                    f"?email={applicant.email}"
                ),
                "minute": minute,
            },
            from_name=municipality.name,
            from_email=municipality.contact_email,
        )


@dramatiq.actor
def send_applicant_notifications(minute_id):
    with db_context() as db:
        minute = db.query(Minute).get(minute_id)
        _send_applicant_notifications(db, minute)
