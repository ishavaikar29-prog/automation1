# report_parent.py

import os
import json
from datetime import datetime

from api_client import fetch_json, API_USERS, API_POSTS, API_TODOS
from excel_builder import build_excel
from email_sender import send_email
from error_handler import init_logger

from success_body import success_message
from failure_body import failure_message

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
    logger.info("==== RUN START ====")

    timestamp = datetime.utcnow().isoformat() + "Z"

    # -------------- ADMIN EMAIL --------------
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    if not ADMIN_EMAIL:
        logger.error("ADMIN_EMAIL is missing")
        return

    # Recipients from secret
    recipients_json = os.getenv("RECIPIENTS_JSON")
    all_recipients = json.loads(recipients_json)

    mode = os.getenv("MODE", "")
    emails = os.getenv("EMAILS", "")
    recipients = pick_recipients(all_recipients, mode, emails)

    # Fetch APIs
    failures = []
    try:
        users = fetch_json(API_USERS)
    except Exception as e:
        failures.append(("users", str(e)))

    try:
        posts = fetch_json(API_POSTS)
    except Exception as e:
        failures.append(("posts", str(e)))

    try:
        todos = fetch_json(API_TODOS)
    except Exception as e:
        failures.append(("todos", str(e)))

    # -------- FAILURE HANDLING (send only to admin) --------
    if failures:
        logger.error("Errors occurred — sending failure email to admin")

        message = failure_message(failures, timestamp)

        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            [ADMIN_EMAIL],
            "Report FAILED",
            message,
            attachments=[],
        )
        return

    # -------- EXCEL CREATION --------
    try:
        excel_path = build_excel(users, posts, todos)
    except Exception as e:
        logger.error(f"Excel build failed: {e}")

        message = failure_message([("excel", str(e))], timestamp)

        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            [ADMIN_EMAIL],
            "Report FAILED",
            message,
            attachments=[],
        )
        return

    # -------- SUCCESS EMAIL --------
    logger.info("Report success — sending Excel")

    body = success_message(len(users), len(posts), len(todos), timestamp)

    # Admin receives ALWAYS
    all_targets = list(set(recipients + [ADMIN_EMAIL]))

    send_email(
        os.getenv("SMTP_HOST"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASS"),
        all_targets,
        "Report SUCCESS",
        body,
        attachments=[excel_path],
    )

    logger.info("==== RUN COMPLETE ====")

if __name__ == "__main__":
    main()
