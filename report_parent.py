# report_parent.py
import os
import json
from datetime import datetime

from api_client import call_api
from api_config import API_FLOW_CONFIG
from excel_builder import build_excel
from email_sender import send_email
from error_handler import init_logger

from success_body import success_message
from failure_body import failure_message
from admin_body import admin_success_message, admin_failure_message

logger = init_logger()

def load_dynamic_api_flow():
    api_flow = []
    base_url = os.getenv("BASE_URL")

    if not base_url:
        raise RuntimeError("BASE_URL is missing in GitHub secrets")

    for cfg in API_FLOW_CONFIG:
        url = base_url.rstrip("/") + cfg["endpoint"]

        step = {
            "name": cfg["name"],
            "method": cfg["method"],
            "url": url,
            "body": cfg.get("body", {}),
            "params": cfg.get("params", {}),
            "headers": cfg.get("headers", {})
        }

        api_flow.append(step)

    return api_flow



def pick_recipients(all_rec, mode, emails):
    mode = (mode or "").lower()
    emails = (emails or "").strip()

    if mode in ("", "all"):
        return all_rec

    if mode == "one":
        if not emails:
            raise ValueError("For mode=one, email is required.")
        return [emails]

    if mode == "many":
        if not emails:
            raise ValueError("For mode=many, emails are required.")
        parts = [e.strip() for e in emails.split(",") if e.strip()]
        for p in parts:
            if p not in all_rec:
                raise ValueError(f"Invalid email: {p}")
        return parts

    raise ValueError("Invalid mode")


def execute_api_flow(api_flow):
    """
    Executes API steps one-by-one.
    Handles token extraction and placeholder replacement.
    This now lives in main layer (as boss required).
    """
    results = {}
    shared = {}
    userId = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")

    for step in api_flow:
        name = step["name"]
        method = step["method"]
        url = step["url"]
        params = step.get("params") or {}
        body = step.get("body") or {}
        headers = step.get("headers") or {}

        if isinstance(body, dict):
            body = {
                k: (
                    v.replace("{userId}", userId).replace("{password}", password)
                    if isinstance(v, str) else v
                )
                for k, v in body.items()
            }

        # ---- Token replacement moved here ----
        if "token" in shared:
            token = shared["token"]

            if isinstance(url, str):
                url = url.replace("{token}", token)

            headers = {
                k: (v.replace("{token}", token) if isinstance(v, str) else v)
                for k, v in headers.items()
            }

            params = {
                k: (v.replace("{token}", token) if isinstance(v, str) else v)
                for k, v in params.items()
            }

            if isinstance(body, dict):
                body = {
                    k: (v.replace("{token}", token) if isinstance(v, str) else v)
                    for k, v in body.items()
                }

        # ---- Call generic client ----
        resp = call_api(
            method=method,
            url=url,
            params=params,
            body=body,
            headers=headers
        )

        results[name] = resp
        
        if isinstance(resp, dict):
            if "accessToken" in resp:
                shared["token"] = resp["accessToken"]
            elif "access_token" in resp:
                shared["token"] = resp["access_token"]
            elif "token" in resp:
                shared["token"] = resp["token"]


        # If response is CSV text (string), save it to file
        # ---- If any API returned CSV text, save it to file ----
    for api_name, resp in results.items():
        if isinstance(resp, str) and "," in resp:
            csv_path = f"{api_name}.csv"
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(resp)
            results[api_name] = csv_path  # replace API data with file path

    return results


                
    return results


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
    try:
        all_recipients = json.loads(recipients_json)
    except Exception:
        logger.error("RECIPIENTS_JSON is missing or invalid")
        return

    mode = os.getenv("MODE", "")
    emails = os.getenv("EMAILS", "")
    try:
        recipients = pick_recipients(all_recipients, mode, emails)
    except Exception as e:
        logger.error(f"Recipient selection failed: {e}")
        return

    # ------------------ API FLOW --------------------
    failures = []
    api_results = {}
    try:
        api_flow = load_dynamic_api_flow()
        if not api_flow:
            raise RuntimeError("No API URLs found in environment. Add API_1_URL...")

        api_results = execute_api_flow(api_flow)


    except Exception as e:
        logger.exception("API flow failed")
        failures.append(("api_flow", str(e)))

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
        # Build a dictionary of datasets to pass to build_excel.
        # If your API steps are named "users", "posts", "todos" they will become sheet names.
        # Example: api_results == {"login": {...}, "users": [...], "transactions": [...]}
        excel_path = build_excel(api_results)  # our build_excel supports dict input
    except Exception as e:
        logger.exception(f"Excel build failed: {e}")

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

    # user_body: use counts of list-like datasets (sum of lengths of lists in api_results)
    total_items = 0
    for v in api_results.values():
        if isinstance(v, list):
            total_items += len(v)

    user_body = success_message(total_items, timestamp)
    admin_body = admin_success_message(timestamp)
    
    
    csv_files = [v for v in api_results.values() if isinstance(v, str) and v.endswith(".csv")]
    
    if recipients:
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            recipients,
            "REPORT SUCCESS",
            user_body,
            attachments=csv_files,
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
        attachments=csv_files + ["run.log"],
    )

    logger.info("==== RUN COMPLETE ====")


if __name__ == "__main__":
    main()
