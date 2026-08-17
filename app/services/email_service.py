import logging
from email.message import EmailMessage
import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class EmailService:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_name = settings.smtp_from_name
        self.from_email = settings.smtp_from_email

    async def send_email(self, to_email: str, subject: str, html_content: str, attachment_path: str = None):
        """Send an email asynchronously, optionally with an attachment."""
        if not self.user or not self.password:
            logger.warning(f"Email sending disabled (no credentials). Would have sent to {to_email}: {subject}")
            return

        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(html_content, subtype="html")

        # Handle attachment if provided
        if attachment_path:
            import os
            if os.path.exists(attachment_path):
                import mimetypes
                ctype, encoding = mimetypes.guess_type(attachment_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                
                with open(attachment_path, "rb") as f:
                    file_data = f.read()
                    
                message.add_attachment(
                    file_data, 
                    maintype=maintype, 
                    subtype=subtype, 
                    filename=os.path.basename(attachment_path)
                )

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                start_tls=self.port == 587,
                use_tls=self.port == 465,
                username=self.user,
                password=self.password
            )
            logger.info(f"Email sent successfully to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)

    async def send_welcome_email(self, to_email: str, name: str, role: str = "client"):
        subject = "Welcome to Legal AI System!"

        if role == "advocate":
            role_message = (
                "You are now registered as a <b>Legal Advocate</b> on our platform. "
                "Once your profile is verified, you will start receiving case assignments, "
                "review AI-generated legal summaries, and provide expert legal opinions to clients."
            )
        else:
            role_message = (
                "You can now create cases, upload documents, and get automated legal opinions "
                "from our AI and expert advocates."
            )

        html_content = f"""
        <h2>Welcome, {name}!</h2>
        <p>Thank you for registering with the Legal AI System.</p>
        <p>{role_message}</p>
        <br/>
        <p>Best regards,<br/>The Legal AI Team</p>
        """
        await self.send_email(to_email, subject, html_content)

    async def send_payment_receipt(self, to_email: str, name: str, case_number: str, amount: float):
        subject = f"Payment Receipt for Case {case_number}"
        html_content = f"""
        <h2>Payment Successful</h2>
        <p>Dear {name},</p>
        <p>We have successfully received your payment of ₹{amount} for Case <b>{case_number}</b>.</p>
        <p>Your case is now unlocked and has been forwarded for expert review.</p>
        <br/>
        <p>Best regards,<br/>The Legal AI Team</p>
        """
        await self.send_email(to_email, subject, html_content)
        
    async def send_case_status_update(self, to_email: str, name: str, case_number: str, new_status: str):
        subject = f"Status Update for Case {case_number}"
        
        # Make the status human-readable
        display_status = new_status.replace("_", " ").title()
        
        html_content = f"""
        <h2>Case Status Updated</h2>
        <p>Dear {name},</p>
        <p>The status of your Case <b>{case_number}</b> has been updated to: <b>{display_status}</b>.</p>
        <p>Please log in to your dashboard to view the latest details and legal opinions.</p>
        <br/>
        <p>Best regards,<br/>The Legal AI Team</p>
        """
        await self.send_email(to_email, subject, html_content)
        
    async def send_final_report_email(self, to_email: str, name: str, case_number: str, pdf_path: str):
        subject = f"Official Legal Opinion Report: Case {case_number}"
        html_content = f"""
        <h2>Your Legal Opinion is Ready</h2>
        <p>Dear {name},</p>
        <p>The expert advocate assigned to your Case <b>{case_number}</b> has finalized their review.</p>
        <p>Please find your official Legal Opinion and Risk Assessment attached to this email as a PDF document.</p>
        <p>If you have any further questions, you can view the full details on your dashboard.</p>
        <br/>
        <p>Best regards,<br/>The Legal AI Team</p>
        """
        await self.send_email(to_email, subject, html_content, attachment_path=pdf_path)

email_service = EmailService()
