from planitor.notifications import _send_applicant_notifications


def test_send_applicant_notifications(db, minute, applicant, emails_message_send):
    minute.inquiry = "Foo\nBar"
    minute.remarks = "Cheese\nShop"
    assert minute.case.serial == applicant.serial
    _send_applicant_notifications(db, minute)
    assert emails_message_send.called


def test_send_applicant_notifications_unsubscribed(
    db, minute, applicant, emails_message_send
):
    applicant.unsubscribed = True
    _send_applicant_notifications(db, minute)
    assert not emails_message_send.called


def test_send_applicant_notifications_no_serial_matched(
    db, minute, applicant, emails_message_send
):
    minute.case.serial = "bar"
    assert applicant.serial != minute.case.serial
    _send_applicant_notifications(db, minute)
    assert not emails_message_send.called
