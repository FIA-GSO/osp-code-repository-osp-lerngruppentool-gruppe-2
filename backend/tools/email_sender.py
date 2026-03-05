import json
import os
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_FILE)

TEMPLATE_FILE = Path(__file__).resolve().parent / "email_templates" / "templates.json"


def _load_templates() -> dict:
	if not TEMPLATE_FILE.exists():
		raise FileNotFoundError(f"Template file not found: {TEMPLATE_FILE}")

	with open(TEMPLATE_FILE, "r", encoding="utf-8") as file:
		return json.load(file)


def _is_valid_email(address: str | None) -> bool:
	if not address:
		return False
	_, parsed_email = parseaddr(address)
	return "@" in parsed_email and "." in parsed_email.split("@")[-1]


class _SafeTemplateDict(dict):
	def __missing__(self, key):
		return "{" + key + "}"


def _render_template_text(text: str, placeholders: dict | None) -> str:
	if not text:
		return ""
	if not placeholders:
		return text
	return text.format_map(_SafeTemplateDict(placeholders))


def send_template_email(email_address: str, template_type: str, placeholders: dict | None = None) -> bool:
	"""
	Sends an email to `email_address` based on `template_type`.

	Required environment variables:
	- SMTP_HOST
	- SMTP_PORT
	- SMTP_USER
	- SMTP_PASSWORD
	- SMTP_FROM (valid sender email, e.g. noreply@yourdomain.tld)
	Optional environment variable:
	- SMTP_USE_TLS (default: true)
	"""
	templates = _load_templates()
	template = templates.get(template_type)
	if template is None:
		raise ValueError(f"Unknown template type: {template_type}")

	smtp_host = os.getenv("SMTP_HOST")
	smtp_port = int(os.getenv("SMTP_PORT", "587"))
	smtp_user = os.getenv("SMTP_USER")
	smtp_password = os.getenv("SMTP_PASSWORD")
	smtp_from = os.getenv("SMTP_FROM") or template.get("from")
	smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

	smtp_host = "pro.turbo-smtp.com"
	smtp_port = "587"
	smtp_user = "e8c09df812b0eca95fb9"
	smtp_password = "HYBg14wh7mRNbjpMEUyt"
	smtp_from = "Lerngruppentool <gsolerngruppentoolxfarian67@gmail.com>"

	if not smtp_host or not smtp_user or not smtp_password:
		raise ValueError("Missing SMTP configuration in environment variables")
	if not _is_valid_email(smtp_from):
		raise ValueError(
			"Missing or invalid SMTP_FROM. Set SMTP_FROM to a real sender email address "
			"(for example: noreply@yourdomain.tld)."
		)
	if not _is_valid_email(email_address):
		raise ValueError(f"Invalid recipient email address: {email_address}")

	message = EmailMessage()
	message["From"] = smtp_from
	message["To"] = email_address
	message["Subject"] = _render_template_text(template.get("subject", ""), placeholders)
	message.set_content(_render_template_text(template.get("body", ""), placeholders))

	with smtplib.SMTP(smtp_host, smtp_port) as server:
		if smtp_use_tls:
			server.starttls()
		server.login(smtp_user, smtp_password)
		server.send_message(message)

	return True
