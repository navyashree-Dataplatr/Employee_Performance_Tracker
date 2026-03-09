import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailService:
    """
    Utility service to send emails with PDF attachments.
    """
    
    # This section initializes the email service with SMTP server details and sender credentials. It allows for default values for Gmail's SMTP server and port, but also accepts custom configurations. The sender email and password can be provided directly or loaded from environment variables, making it flexible for different deployment environments. This setup is essential for enabling the functionality to send invoice emails with PDF attachments to clients or internal stakeholders. 
    # The constructor takes in the SMTP server address, port number, sender email, and sender password. If the sender email or password is not provided, it will rely on environment variables to load these values, ensuring that sensitive information is not hardcoded in the codebase. This design allows for secure and configurable email sending capabilities within the application.    

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


        # If sender email or password is not provided, attempt to load from environment variables 
        # This allows for secure configuration without hardcoding sensitive information in the codebase. It also provides flexibility for different deployment environments, where environment variables can be set up to manage credentials securely. If the sender email or password is not found in the environment variables, it will print a warning message, which can help with debugging email configuration issues. This approach ensures that the email service can function properly while keeping sensitive information secure and configurable.

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
            
            print(f" Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False
