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
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for path in attachments or []:
        if os.path.exists(path):
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(path, "rb").read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(path)}")
            msg.attach(part)

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    server.sendmail(user, recipients, msg.as_string())
    server.quit()
    logger.info(f"Email sent to {recipients}")
