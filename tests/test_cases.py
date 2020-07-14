from planitor.cases import get_case_status_from_remarks, CaseStatusEnum


def test_get_case_status_from_remarks():
    assert (
        get_case_status_from_remarks("Frestað. Vísað til athugasemda.")
        == CaseStatusEnum.delayed
    )
    assert (
        get_case_status_from_remarks(
            "Frestað. Málinu vísað til skipulagsfulltrúa í grenndarkynningu."
        )
        == CaseStatusEnum.notice
    )
    assert (
        get_case_status_from_remarks(
            "Frestað. Málinu vísað til umsagnar skipulagsfulltrúa."
        )
        == CaseStatusEnum.directed_to_skipulagsfulltrui
    )


def get(serial):


for m in db.query(Minute):
    if m.meeting.council.name == "Byggingarfulltrúi":
        if '">' in m.address:
            _, m.address = m.address.split('">', 1)
            print(address)
            db.add(m)
        if " " in serial:
            m.serial, stadgreinir = m.serial.split(" ", 1)
            m.stadgreinir = stadgreinir.strip("()").split()[0]
            db.add(m)

