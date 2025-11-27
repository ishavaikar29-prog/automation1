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
from admin_body import admin_success_message, admin_failure_message

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

    # ------------------ ADMIN EMAIL ------------------
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    if not ADMIN_EMAIL:
        logger.error("ADMIN_EMAIL is missing")
        return

    # ------------------ RECIPIENTS -------------------
    recipients_json = os.getenv("RECIPIENTS_JSON")
    all_recipients = json.loads(recipients_json)

    mode = os.getenv("MODE", "")
    emails = os.getenv("EMAILS", "")
    recipients = pick_recipients(all_recipients, mode, emails)

    # ------------------ API FETCH --------------------
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

    # ------------------ FAILURE HANDLING ------------------
    if failures:
        logger.error("Errors occurred — sending failure email to ADMIN only")

        message_user = failure_message(failures, timestamp)         # normal error body (not used)
        message_admin = admin_failure_message(failures, timestamp)  # admin-specific error body

        # ADMIN gets log file always
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            [ADMIN_EMAIL],
            "REPORT FAILED (ADMIN ALERT)",
            message_admin,
            attachments=["run.log"],
        )
        return

    # ------------------ EXCEL CREATION ------------------
    try:
        excel_path = build_excel(users, posts, todos)
    except Exception as e:
        logger.error(f"Excel build failed: {e}")

        message_admin = admin_failure_message([("excel", str(e))], timestamp)

        # On excel failure → admin gets ONLY log file
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            [ADMIN_EMAIL],
            "REPORT FAILED (ADMIN ALERT)",
            message_admin,
            attachments=["run.log"],
        )
        return

    # ------------------ SUCCESS EMAILS ------------------
    logger.info("Report success — sending Excel")

    # BODY FOR USERS (simple)
    user_body = success_message(len(users), len(posts), len(todos), timestamp)

    # BODY FOR ADMIN (special)
    admin_body = admin_success_message(timestamp)

    # -------- SEND TO NORMAL USERS (Excel ONLY) --------
    if recipients:
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            recipients,
            "REPORT SUCCESS",
            user_body,
            attachments=[excel_path],
        )

    # -------- SEND TO ADMIN (Excel + log) --------
    send_email(
        os.getenv("SMTP_HOST"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASS"),
        [ADMIN_EMAIL],
        "REPORT SUCCESS (ADMIN COPY)",
        admin_body,
        attachments=[excel_path, "run.log"],
    )

    logger.info("==== RUN COMPLETE ====")


if __name__ == "__main__":
    main()
