import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailService:
    """
    Utility service to send emails with PDF attachments.
    """
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, sender_email=None, sender_password=None):
        """
        Initialize the email service.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            sender_email: Email address to send from
            sender_password: App password or email password (optional)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_invoice_email(self, recipient_email, subject, body, attachment_path):
        """
        Send an invoice email with a PDF attachment.
        
        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            body: Email body text
            attachment_path: Path to the PDF file to attach
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sender_email:
            print("Error: Sender email not configured.")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            # Attach PDF
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
            else:
                print(f"Warning: Attachment not found at {attachment_path}")

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                
                # Only login if password is provided
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
                server.send_message(msg)
            
            print(f"✓ Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False
