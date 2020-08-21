import logging
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

import emails
from emails.template import JinjaTemplate

from planitor import config


password_reset_jwt_subject = "preset"

jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "email-templates")
)


def send_email(email_to: str, subject: str, html_template: str, context: dict):
    context = context.copy()
    message = emails.Message(
        subject=JinjaTemplate(subject),
        html=jinja_env.get_template(html_template).render(context),
        mail_from=(config("EMAILS_FROM_NAME"), config("EMAILS_FROM_EMAIL")),
        headers={"X-SES-CONFIGURATION-SET": "planitor-ses-configuration"},
    )
    smtp_options = {"host": config("SMTP_HOST"), "port": config("SMTP_PORT", cast=int)}
    smtp_options["tls"] = config("SMTP_TLS", cast=bool, default=True)
    if config("SMTP_USER"):
        smtp_options["user"] = config("SMTP_USER")
    if config("SMTP_PASSWORD"):
        smtp_options["password"] = config("SMTP_PASSWORD")
    message.transform()
    response = message.send(to=email_to, render=context, smtp=smtp_options)
    logging.info(f"send email result: {response}")
