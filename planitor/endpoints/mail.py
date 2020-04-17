import logging
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

import emails
from emails.template import JinjaTemplate

from planitor import env


password_reset_jwt_subject = "preset"

jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "email-templates")
)


def send_email(email_to: str, subject: str, html_template: str, context: dict):
    context = context.copy()
    message = emails.Message(
        subject=JinjaTemplate(subject),
        html=jinja_env.get_template(html_template).render(context),
        mail_from=(env("EMAILS_FROM_NAME"), env("EMAILS_FROM_EMAIL")),
    )
    smtp_options = {"host": env("SMTP_HOST"), "port": env.int("SMTP_PORT")}
    smtp_options["tls"] = env.bool("SMTP_TLS", True)
    if env("SMTP_USER"):
        smtp_options["user"] = env("SMTP_USER")
    if env("SMTP_PASSWORD"):
        smtp_options["password"] = env("SMTP_PASSWORD")
    message.transform()
    response = message.send(to=email_to, render=context, smtp=smtp_options)
    logging.info(f"send email result: {response}")


def send_test_email(email_to: str):
    project_name = env("PROJECT_NAME")
    send_email(
        email_to=email_to,
        subject=f"{project_name} - Test email",
        html_template="test_email.html",
        context={"project_name": project_name, "email": email_to},
    )


def send_reset_password_email(email_to: str, email: str, token: str):
    project_name = env("PROJECT_NAME")
    subject = f"{project_name} - Nýtt lykilorð"
    if hasattr(token, "decode"):
        use_token = token.decode()
    else:
        use_token = token
    server_host = env("SERVER_HOST")
    link = f"http://{server_host}/notendur/reset-password?token={use_token}"
    send_email(
        email_to=email_to,
        subject=subject,
        html_template="reset_password.html",
        context={
            "project_name": env("PROJECT_NAME"),
            "username": email,
            "email": email_to,
            "valid_hours": env.int("EMAILS_RESET_TOKEN_EXPIRE_HOURS"),
            "link": link,
        },
    )
