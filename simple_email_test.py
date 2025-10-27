#!/usr/bin/env python3
"""
Simple email test using smtplib directly
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path

# Load environment from ../Media Feed Secrets/.env
env_file = Path(__file__).parent.parent / "Media Feed Secrets" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def send_simple_email():
    """Send a test email using simple SMTP"""
    print("Me Feed Simple Email Test")
    print("=" * 30)
    
    # Get config from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp-relay.brevo.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '9a1910001@smtp-brevo.com')
    smtp_password = os.getenv('SMTP_PASSWORD', 'HvZ6fn5jYpBJDaNL')
    from_email = os.getenv('FROM_EMAIL', 'rene.matis89@gmail.com')
    to_email = 'rene.matis89@gmail.com'
    
    print(f"SMTP Host: {smtp_host}")
    print(f"SMTP Port: {smtp_port}")
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    print()
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = '🧪 Me Feed - Test Email (Simple)'
        
        body = """
        <h1>Test Successful!</h1>
        <p>If you receive this email, your Brevo SMTP configuration is working correctly.</p>
        <p>This was sent using the simple test script.</p>
        <p>Sent from Me Feed application.</p>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect and send
        print("Connecting to SMTP server...")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            print("Starting TLS...")
            server.starttls()
            
            print("Authenticating...")
            server.login(smtp_user, smtp_password)
            
            print("Sending email...")
            server.send_message(msg)
            
        print("✅ Email sent successfully!")
        print("📧 Please check your inbox (and spam folder) for the test email.")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    success = send_simple_email()
    
    if success:
        print("\n🎉 Email test completed successfully!")
    else:
        print("\n⚠️ Email test failed")
