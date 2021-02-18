import re
import asyncio
from zeep import Client
from email_normalize import Normalizer

from planitor import config
from planitor.database import db_context
from planitor.models.city import Applicant, Case


normalize = Normalizer().normalize

email_re = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

SERVICE_URL = (
    "https://ibuagatt.hafnarfjordur.is/meetingnotifications/outerws/services.asmx?WSDL"
)
AUTH_SERVICE_URL = (
    "https://ibuagatt.hafnarfjordur.is"
    "/meetingnotifications/oneauthentication/Authenticate.asmx?WSDL"
)

auth_client = Client(AUTH_SERVICE_URL)
client = Client(SERVICE_URL)

api_key = auth_client.service.CreateApiKey(
    "OneTest", config("ONESYSTEM_HAFNARFJORDUR_KEY")
)
token = auth_client.service.GetAuthenticationToken(api_key)


async def get_data():
    for item in client.service.GetData(token):
        if item["Email"]:
            for match in re.findall(email_re, item["Email"]):
                email = (await normalize(match)).normalized_address
                yield email, item["CaseNumber"].strip()


async def main(db):
    async for email, case_serial in get_data():
        applicant_exists = db.query(Applicant).filter(
            Applicant.serial == case_serial, Applicant.email == email
        )
        if applicant_exists.first():
            continue
        case = (
            db.query(Case)
            .filter(Case.municipality_id == 1400, Case.serial == case_serial)
            .first()
        )
        applicant = Applicant(
            case=case, email=email, serial=case_serial, municipality_id=1400
        )
        print(f"Adding {email} to {case_serial}")
        db.add(applicant)
    db.commit()


if __name__ == "__main__":
    with db_context() as db:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main(db))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
