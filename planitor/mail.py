import logging
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

import emails
from emails.template import JinjaTemplate

from planitor.templates import human_date, timeago
from planitor import config


password_reset_jwt_subject = "preset"

jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "email-templates")
)

jinja_env.globals.update({"human_date": human_date, "timeago": timeago})


def get_html(template, context):
    return jinja_env.get_template(template).render(context)


def send_email(email_to: str, subject: str, html_template: str, context: dict):
    context = context.copy()
    message = emails.Message(
        subject=JinjaTemplate(subject),
        html=get_html(html_template, dict(email_to=email_to, **context)),
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
    return response
