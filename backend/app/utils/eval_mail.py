# This file contains the logic for sending emails to the user about evlaution completion
from ..services.mongo import get_evaluation_by_evaluation_id, get_email_by_user_id, get_asset_by_evaluation_id
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings

def send_email(email: str, subject: str, body: str):
    """Send an email via SMTP using settings from environment variables.
    If SMTP is not configured, logs to console.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not settings.SMTP_FROM_EMAIL:
        print(f"Email sent to: {email}\nSubject: {subject}\n\n{body}")
        return

    message = MIMEMultipart()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [email], message.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                if settings.SMTP_USE_TLS:
                    server.starttls()
                    server.ehlo()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [email], message.as_string())
    except Exception as e:
        print(f"[EMAIL-ERROR] Failed to send email to {email}: {str(e)}")

def send_eval_completion_email(evaluation_id: str, user_id: str):
    evaluation = get_evaluation_by_evaluation_id(evaluation_id)
    user_email = get_email_by_user_id(user_id)
    if not user_email:
        print(f"[EMAIL-WARN] No email found for user_id={user_id}; skipping email.")
        return
    
    # Get the asset name for this evaluation
    asset = get_asset_by_evaluation_id(evaluation_id)
    asset_name = asset.get("asset_name", "Unnamed Evaluation") if asset else "Unnamed Evaluation"
    
    subject = "Evaluation Completed"
    body = f"""
Dear User,

Your evaluation "{asset_name}" has been successfully completed.
You can view the results on the evaluation card of the course.

Regards,
ACAD
"""
    send_email(user_email, subject, body)

def send_eval_error_email(evaluation_id: str, user_id: str, error_message: str = ""):
    """Send an error email to the user when evaluation processing fails"""
    user_email = get_email_by_user_id(user_id)
    if not user_email:
        print(f"[EMAIL-WARN] No email found for user_id={user_id}; skipping error email.")
        return
    
    # Get the asset name for this evaluation
    asset = get_asset_by_evaluation_id(evaluation_id)
    asset_name = asset.get("asset_name", "Unnamed Evaluation") if asset else "Unnamed Evaluation"
    
    subject = "Evaluation Processing Error"
    body = f"""
Dear User,

We encountered an error while processing your evaluation "{asset_name}".

Please try uploading your files again. If the problem persists, please contact our support team for assistance.

Error Details: {error_message}

Regards,
ACAD Support Team
"""
    send_email(user_email, subject, body)