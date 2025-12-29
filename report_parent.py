# report_parent.py
import os
import json
from datetime import datetime, date, timedelta

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

        return "Unexpected workflow failure. Check run.log for details."

    except Exception:
        return "Error analyzing log file."


def pick_recipients(all_rec, mode, emails):
    mode = (mode or "").lower()
    emails = (emails or "").strip()

    if mode == "all":
        return all_rec

    if mode == "custom":
        if not emails:
            raise ValueError("For mode=custom, emails are required.")
        return [e.strip() for e in emails.split(",") if e.strip()]

    raise ValueError("Invalid mode")


def execute_api_flow(api_flow):
    results = {}
    shared = {}

    userId = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    start_date = os.getenv("START_DATE")
    end_date = os.getenv("END_DATE")

    for step in api_flow:
        name = step["name"]
        method = step["method"]
        url = step["url"]
        params = step.get("params") or {}
        body = step.get("body") or {}
        headers = step.get("headers") or {}

        if isinstance(params, dict):
            params = {
                k: v.replace("{startDate}", start_date).replace("{endDate}", end_date)
                if isinstance(v, str) else v
                for k, v in params.items()
            }

        if isinstance(body, dict):
            body = {
                k: v.replace("{startDate}", start_date).replace("{endDate}", end_date)
                if isinstance(v, str) else v
                for k, v in body.items()
            }

        if isinstance(body, dict):
            body = {
                k: v.replace("{userId}", userId).replace("{password}", password)
                if isinstance(v, str) else v
                for k, v in body.items()
            }

        if "token" in shared:
            token = shared["token"]
            headers = {k: v.replace("{token}", token) if isinstance(v, str) else v for k, v in headers.items()}
            params = {k: v.replace("{token}", token) if isinstance(v, str) else v for k, v in params.items()}

        try:
            resp = call_api(method=method, url=url, params=params, body=body, headers=headers)
        except Exception:
            logger.error(f"[API ERROR] Step '{name}' failed while calling {url}", exc_info=True)
            raise

        results[name] = resp
        logger.info(f"[RESPONSE] Step '{name}' returned: {resp}")

        if isinstance(resp, dict):
            if "accessToken" in resp:
                shared["token"] = resp["accessToken"]
            elif "access_token" in resp:
                shared["token"] = resp["access_token"]
            elif "token" in resp:
                shared["token"] = resp["token"]
            elif "data" in resp and "tokens" in resp["data"]:
                shared["token"] = resp["data"]["tokens"]["accessToken"]

    for api_name, resp in results.items():
        if isinstance(resp, str) and "," in resp:
            path = f"{api_name}.csv"
            with open(path, "w", encoding="utf-8") as f:
                f.write(resp)
            results[api_name] = path

    return results
def resolve_date_range():
    """
    Resolves start_date and end_date based on REPORT_TYPE.
    Supports only: daily, weekly
    """

    report_type = os.getenv("REPORT_TYPE", "daily").lower()

    # If explicitly provided, respect them
    start_date = os.getenv("START_DATE")
    end_date = os.getenv("END_DATE")

    if start_date and end_date:
        return start_date, end_date

    today = date.today()

    if report_type == "daily":
        d = today - timedelta(days=1)
        return d.isoformat(), d.isoformat()

    if report_type == "weekly":
        end = today
        start = today - timedelta(days=6)
        return start.isoformat(), end.isoformat()

    raise ValueError("Only daily and weekly report types are supported")


def main():
    logger.info("==== RUN START ====")
    timestamp = datetime.utcnow().isoformat() + "Z"

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    if not ADMIN_EMAIL:
        logger.error("ADMIN_EMAIL is missing")
        return

    all_recipients = json.loads(os.getenv("RECIPIENTS_JSON"))
    recipients = pick_recipients(all_recipients, os.getenv("MODE"), os.getenv("EMAILS"))

  
    start_date, end_date = resolve_date_range()

    os.environ["START_DATE"] = start_date
    os.environ["END_DATE"] = end_date


    try:
        api_results = execute_api_flow(load_dynamic_api_flow())
    except Exception as e:
        summary = summarize_log_error()
        send_email(
            os.getenv("SMTP_HOST"),
            int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USER"),
            os.getenv("SMTP_PASS"),
            [ADMIN_EMAIL],
            "REPORT FAILED (ADMIN ALERT)",
            admin_failure_message([("api_flow", str(e))], timestamp, summary),
            attachments=["run.log"],
        )
        return

    excel_path = build_excel(api_results)

    send_email(
        os.getenv("SMTP_HOST"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASS"),
        recipients,
        "REPORT SUCCESS",
        success_message(0, timestamp),
        attachments=[excel_path],
    )

    logger.info("==== RUN COMPLETE ====")


if __name__ == "__main__":
    main()
