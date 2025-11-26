# report_parent.py

import os
import json
from api_client import fetch_json, API_USERS, API_POSTS, API_TODOS
from excel_builder import build_excel
from email_sender import send_email
from error_handler import init_logger

logger = init_logger()

def pick_recipients(all_rec, mode, emails):
    mode = (mode or "").lower()
    emails = (emails or "").strip()

    if mode in ("", "cron", "all"):
        return all_rec
    if mode == "one":
        return [emails]
    if mode == "many":
        parts = [e.strip() for e in emails.split(",") if e.strip()]
        for p in parts:
            if p not in all_rec:
                raise ValueError(f"Invalid email: {p}")
        return parts
    raise ValueError("Invalid mode")

def main():
    logger.info("Run started")

    # Recipients from secret
    recipients_json = os.getenv("RECIPIENTS_JSON")
    all_recipients = json.loads(recipients_json)

    mode = os.getenv("MODE", "")
    emails = os.getenv("EMAILS", "")
    recipients = pick_recipients(all_recipients, mode, emails)

    # Fetch APIs
    try:
        users = fetch_json(API_USERS)
        posts = fetch_json(API_POSTS)
        todos = fetch_json(API_TODOS)
    except Exception as e:
        logger.error(f"API failed: {e}")
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            recipients,
            "Daily Report — FAILED",
            f"Automation failed: {e}",
            attachments=[]
        )
        return

    # Build Excel
    try:
        excel_path = build_excel(users, posts, todos)
    except Exception as e:
        logger.error(f"Excel failed: {e}")
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            recipients,
            "Daily Report — FAILED",
            f"Excel creation failed: {e}",
            attachments=[]
        )
        return

    # Send email with Excel
    send_email(
        os.getenv("SMTP_HOST"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASS"),
        recipients,
        "Daily Report — SUCCESS",
        "Attached is your report.",
        attachments=[excel_path]
    )

    logger.info("Run complete")

if __name__ == "__main__":
    main()
