"""
Email Sender

Sends digest emails using SendGrid API.
Free tier: 100 emails/day
"""
import os
from typing import Optional


class EmailSender:
    """Sends emails via SendGrid"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize email sender
        
        Args:
            api_key: SendGrid API key (defaults to SENDGRID_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.client = SendGridAPIClient(self.api_key)
            except ImportError:
                print("Warning: sendgrid package not installed. Email sending disabled.")
        else:
            print("Warning: No SENDGRID_API_KEY found. Email sending disabled.")
    
    def send_digest(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str = "",
        from_email: str = None
    ) -> bool:
        """
        Send a digest email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body
            plain_content: Plain text body (fallback)
            from_email: Sender email address
            
        Returns:
            True if sent successfully
        """
        if not self.client:
            print("Email client not configured. Skipping send.")
            self._save_locally(html_content, subject)
            return False
        
        from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL", "digest@research-digest.com")
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(from_email, "Research Digest"),
                to_emails=To(to_email),
                subject=subject
            )
            
            message.add_content(Content("text/plain", plain_content or "Please view in HTML."))
            message.add_content(Content("text/html", html_content))
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                print(f"✓ Email sent successfully to {to_email}")
                return True
            else:
                print(f"✗ Email failed with status {response.status_code}")
                self._save_locally(html_content, subject)
                return False
                
        except Exception as e:
            print(f"✗ Error sending email: {e}")
            self._save_locally(html_content, subject)
            return False
    
    def _save_locally(self, html_content: str, subject: str):
        """Save email locally when sending fails"""
        from datetime import datetime
        
        filename = f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(os.path.dirname(__file__), "..", "..", "data", filename)
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(html_content)
            print(f"  Digest saved locally to: {filepath}")
        except Exception as e:
            print(f"  Could not save locally: {e}")


def test_email_sender():
    """Test the email sender"""
    print("Testing email sender...")
    sender = EmailSender()
    
    test_html = """
    <html>
    <body>
        <h1>Test Digest</h1>
        <p>This is a test email.</p>
    </body>
    </html>
    """
    
    # This will save locally since we likely don't have API key configured
    sender.send_digest(
        to_email="test@example.com",
        subject="Test Research Digest",
        html_content=test_html,
        plain_content="This is a test email."
    )


if __name__ == "__main__":
    test_email_sender()
