# email_sender.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging

logger = logging.getLogger("automation")

def send_email(host, port, user, password, recipients, subject, body, attachments=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # ----- Attachments -----
        for path in attachments or []:
            if os.path.exists(path):
                try:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(open(path, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(path)}"
                    )
                    msg.attach(part)
                    logger.info(f"Attached file: {path}")
                except Exception:
                    logger.error(
                        f"[EMAIL ATTACHMENT ERROR] Failed to attach file: {path}",
                        exc_info=True
                    )
                    raise
            else:
                logger.warning(f"[ATTACHMENT MISSING] {path} does not exist")

        # ----- SMTP SEND -----
        try:
            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(user, password)
            server.sendmail(user, recipients, msg.as_string())
            server.quit()
            logger.info(f"Email sent to {recipients}")

        except Exception:
            logger.error(
                f"[EMAIL SEND ERROR] Failed sending email to {recipients}",
                exc_info=True
            )
            raise

    except Exception:
        logger.error(
            f"[EMAIL ERROR] Unexpected failure while preparing email to {recipients}",
            exc_info=True
        )
        raise
