# report_parent.py
import os
import json
from datetime import datetime
from datetime import date

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

def summarize_log_error():
    try:
        if not os.path.exists("run.log"):
            return "Run log missing."

        with open("run.log", "r", encoding="utf-8") as f:
            log = f.read()

        # PRIORITY-BASED ERROR DETECTION
        if "401" in log or "Unauthorized" in log:
            return "Authentication failed — invalid or expired token."

        if "ConnectionError" in log:
            return "API server unreachable — network or server down."

        if "JSONDecodeError" in log:
            return "Invalid API response — JSON parsing failed."

        if "SMTPAuthenticationError" in log:
            return "Email sending failed — SMTP authentication error."

        if "Timeout" in log:
            return "API timeout — server did not respond."

        if "FileNotFoundError" in log:
            return "Missing file — attachment or resource not found."

        if "KeyError" in log:
            return "Required field missing in API response."

        if "Token" in log and "WARNING" in log:
            return "Token missing in login API response."

        # Default fallback
        return "Unexpected workflow failure. Check run.log for details."

    except Exception:
        return "Error analyzing log file."

def pick_recipients(all_rec, mode, emails):
    mode = (mode or "").lower()
    emails = (emails or "").strip()

    # all = send to all recipients
    if mode == "all":
        return all_rec

    # custom = manually selected emails
    if mode == "custom":
        if not emails:
            raise ValueError("For mode=custom, emails are required.")

        parts = [e.strip() for e in emails.split(",") if e.strip()]
        return parts

    # fallback (should not happen)
    raise ValueError("Invalid mode")


def execute_api_flow(api_flow):
    """
    Executes API steps one-by-one.
    Handles token extraction and placeholder replacement.
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

        # ---- Username / password injection ----
        if isinstance(body, dict):
            body = {
                k: (
                    v.replace("{userId}", userId).replace("{password}", password)
                    if isinstance(v, str) else v
                )
                for k, v in body.items()
            }

        # ---- Token replacement ----
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

        # ---- Call API ----
        try:
            resp = call_api(
                method=method,
                url=url,
                params=params,
                body=body,
                headers=headers
            )
        except Exception:
            logger.error(
                f"[API ERROR] Step '{name}' failed while calling {url}",
                exc_info=True
            )
            raise

        results[name] = resp

        logger.info(f"[RESPONSE] Step '{name}' returned: {resp}")

        # ---- Token extraction ----
        try:
            if isinstance(resp, dict):
                if "accessToken" in resp:
                    shared["token"] = resp["accessToken"]
                    logger.info(f"[TOKEN] Extracted: {shared['token']}")
                elif "access_token" in resp:
                    shared["token"] = resp["access_token"]
                    logger.info(f"[TOKEN] Extracted: {shared['token']}")
                elif "token" in resp:
                    shared["token"] = resp["token"]
                    logger.info(f"[TOKEN] Extracted: {shared['token']}")
                elif "data" in resp and "tokens" in resp["data"]:
                    shared["token"] = resp["data"]["tokens"]["accessToken"]
                    logger.info(f"[TOKEN] Extracted: {shared['token']}")
                else:
                    logger.warning(
                        f"[TOKEN WARNING] No token found for step '{name}'. Response keys: {list(resp.keys())}"
                    )
        except Exception:
            logger.error(
                f"[TOKEN EXTRACTION ERROR] Failed to extract token in step '{name}'",
                exc_info=True
            )
            raise

    # ---- Save CSV files ----
    for api_name, resp in results.items():
        if isinstance(resp, str) and "," in resp:
            csv_path = f"{api_name}.csv"
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(resp)
            results[api_name] = csv_path

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
    
    start_date = os.getenv("START_DATE")
    end_date = os.getenv("END_DATE")

# If user did not provide dates → use today's date
    if not start_date or not end_date:
        today = date.today().isoformat()
        start_date = start_date or today
        end_date = end_date or today

    # ------------------ API FLOW --------------------
    failures = []
    api_results = {}
    try:
        api_flow = load_dynamic_api_flow()
        if not api_flow:
            raise RuntimeError("No API URLs found")

        api_results = execute_api_flow(api_flow)

    except Exception as e:
        logger.exception("API flow failed")
        failures.append(("api_flow", str(e)))

    # ------------------ FAILURE HANDLING ------------------
    if failures:
        logger.error("Errors occurred — sending failure email to ADMIN only")

        summary = summarize_log_error()
        message_admin = admin_failure_message(failures, timestamp, summary=summary)


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
        excel_path = build_excel(api_results)
    except Exception as e:
        logger.error("[EXCEL ERROR] Failed to generate Excel file", exc_info=True)

        message_admin = admin_failure_message([("excel", str(e))], timestamp)

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

    total_items = 0
    for v in api_results.values():
        if isinstance(v, list):
            total_items += len(v)

    user_body = success_message(total_items, timestamp)
    admin_body = admin_success_message(timestamp)

    csv_files = [v for v in api_results.values() if isinstance(v, str) and v.endswith(".csv")]

    # USER EMAIL
    if recipients:
        try:
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
        except Exception:
            logger.error("[EMAIL ERROR] Failed to send user email", exc_info=True)

    # ADMIN EMAIL
    try:
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
    except Exception:
        logger.error("[EMAIL ERROR] Failed to send admin email", exc_info=True)

    logger.info("==== RUN COMPLETE ====")


if __name__ == "__main__":
    main()
