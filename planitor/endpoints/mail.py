import logging
from pathlib import Path

import emails
from emails.template import JinjaTemplate

from planitor import env

password_reset_jwt_subject = "preset"


def send_email(email_to: str, subject_template="", html_template="", environment=None):
    assert env("EMAILS_ENABLED"), "no provided config for email variables"
    if environment is None:
        environment = {}
    message = emails.Message(
        subject=JinjaTemplate(subject_template),
        html=JinjaTemplate(html_template),
        mail_from=(env("EMAILS_FROM_NAME"), env("EMAILS_FROM_EMAIL")),
    )
    smtp_options = {"host": env("SMTP_HOST"), "port": env.int("SMTP_PORT")}
    smtp_options["tls"] = env.bool("SMTP_TLS", True)
    if env("SMTP_USER"):
        smtp_options["user"] = env("SMTP_USER")
    if env("SMTP_PASSWORD"):
        smtp_options["password"] = env("SMTP_PASSWORD")
    message.transform()
    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f"send email result: {response}")


def send_test_email(email_to: str):
    project_name = env("PROJECT_NAME")
    subject = f"{project_name} - Test email"
    with open(
        Path(__file__).resolve().parent / "email-templates" / "test_email.html"
    ) as f:
        template_str = f.read()
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={"project_name": env("PROJECT_NAME"), "email": email_to},
    )


def send_reset_password_email(email_to: str, email: str, token: str):
    project_name = env("PROJECT_NAME")
    subject = f"{project_name} - Password recovery for user {email}"
    with open(
        Path(__file__).resolve().parent / "email-templates" / "reset_password.html"
    ) as f:
        template_str = f.read()
    if hasattr(token, "decode"):
        use_token = token.decode()
    else:
        use_token = token
    server_host = env("SERVER_HOST")
    link = f"{server_host}/reset-password?token={use_token}"
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            "project_name": env("PROJECT_NAME"),
            "username": email,
            "email": email_to,
            "valid_hours": env.int("EMAILS_RESET_TOKEN_EXPIRE_HOURS"),
            "link": link,
        },
    )


def send_new_account_email(email_to: str, username: str, password: str):
    project_name = env("PROJECT_NAME")
    subject = f"{project_name} - New account for user {username}"
    with open(
        Path(__file__).resolve().parent / "email-templates" / "new_account.html"
    ) as f:
        template_str = f.read()
    link = env("SERVER_HOST")
    send_email(
        email_to=email_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            "project_name": env("PROJECT_NAME"),
            "username": username,
            "password": password,
            "email": email_to,
            "link": link,
        },
    )
