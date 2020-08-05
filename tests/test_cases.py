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
