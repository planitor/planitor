from planitor.cases import CaseStatusEnum, get_case_status_from_remarks


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

    assert get_case_status_from_remarks("Samþykkt.") == CaseStatusEnum.approved

    assert (
        get_case_status_from_remarks("Samþykkt, með fjórum greiddum atkvæðum.")
        == CaseStatusEnum.approved
    )

    assert (
        get_case_status_from_remarks(
            "Samþykkt, með fjórum greiddum atkvæðum, fulltrúa Samfylkingarinnar, "
            "Viðreisnar og Pírata, að synja beiðni um breytingu á deiliskipulagi "
            "með vísun til umsagnar skipulagsfulltrúa dags. 2. júlí 2020. Fulltrúar "
            "Sjálfstæðisflokksins sitja hjá.Vísað til borgarráðs."
        )
        == CaseStatusEnum.denied
    )
