from planitor import config
from planitor.mail import send_email


def send_test_email(email_to: str):
    project_name = config("PROJECT_NAME")
    send_email(
        email_to=email_to,
        subject="Test email",
        html_template="test_email.html",
        context={"project_name": project_name, "email": email_to},
    )


def send_reset_password_email(email_to: str, link: str):
    send_email(
        email_to=email_to,
        subject="Leiðbeiningar fyrir nýtt lykilorð",
        html_template="reset_password.html",
        context={
            "project_name": config("PROJECT_NAME"),
            "email": email_to,
            "valid_hours": config("EMAILS_RESET_TOKEN_EXPIRE_HOURS", cast=int),
            "link": link,
        },
    )
