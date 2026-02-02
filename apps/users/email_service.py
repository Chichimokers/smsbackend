"""
Email service for sending verification emails.
Uses Gmail SMTP for sending emails.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

logger = logging.getLogger(__name__)


def get_verification_url(token: str) -> str:
    """Build the verification URL for a given token."""
    # Use BACKEND_URL for the verification endpoint (renders HTML directly)
    base_url = settings.BACKEND_URL.rstrip('/')
    return f"{base_url}/api/v1/users/verify/{token}/"


def send_verification_email(user) -> bool:
    """
    Send a verification email to the user.
    
    Args:
        user: User instance with email and verification_token
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    verification_url = get_verification_url(str(user.verification_token))
    
    subject = 'Verifica tu cuenta - SMS Rental'
    
    # HTML email content
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SMS Rental</h1>
        </div>
        <div class="content">
            <h2>¡Hola{' ' + user.first_name if user.first_name else ''}!</h2>
            <p>Gracias por registrarte en SMS Rental. Para completar tu registro, necesitas verificar tu dirección de email.</p>
            <p>Haz clic en el siguiente botón para verificar tu cuenta:</p>
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verificar mi cuenta</a>
            </p>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p style="word-break: break-all; background: #e9e9e9; padding: 10px; border-radius: 5px;">
                {verification_url}
            </p>
            <p>Si no creaste una cuenta en SMS Rental, puedes ignorar este email.</p>
        </div>
        <div class="footer">
            <p>Este email fue enviado automáticamente. Por favor no respondas a este mensaje.</p>
            <p>&copy; 2024 SMS Rental. Todos los derechos reservados.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = f"""
¡Hola{' ' + user.first_name if user.first_name else ''}!

Gracias por registrarte en SMS Rental. Para completar tu registro, necesitas verificar tu dirección de email.

Haz clic en el siguiente enlace para verificar tu cuenta:
{verification_url}

Si no creaste una cuenta en SMS Rental, puedes ignorar este email.

---
Este email fue enviado automáticamente. Por favor no respondas a este mensaje.
© 2024 SMS Rental. Todos los derechos reservados.
    """
    
    try:
        logger.info(f'[Email] Attempting to send verification email to {user.email}')
        logger.info(f'[Email] SMTP Config - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, User: {settings.EMAIL_HOST_USER}')
        logger.info(f'[Email] Verification URL: {verification_url}')
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = user.email
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        logger.info(f'[Email] Connecting to SMTP server...')
        
        # Connect to SMTP server with timeout
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
        server.set_debuglevel(0)  # Set to 1 for debug output
        
        logger.info(f'[Email] Starting TLS...')
        server.starttls()
        
        logger.info(f'[Email] Logging in...')
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        
        logger.info(f'[Email] Sending message...')
        server.sendmail(settings.EMAIL_HOST_USER, [user.email], msg.as_string())
        
        logger.info(f'[Email] Closing connection...')
        server.quit()
        
        logger.info(f'[Email] SUCCESS - Verification email sent to {user.email}')
        return True
            
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f'[Email] AUTH ERROR - Invalid credentials for {settings.EMAIL_HOST_USER}')
        logger.error(f'[Email] ERROR details: {e}')
        return False
    except smtplib.SMTPException as e:
        logger.error(f'[Email] SMTP ERROR - Failed to send email to {user.email}')
        logger.error(f'[Email] ERROR details: {type(e).__name__}: {e}')
        return False
    except Exception as e:
        logger.error(f'[Email] ERROR - Failed to send verification email to {user.email}')
        logger.error(f'[Email] ERROR details: {type(e).__name__}: {e}')
        return False


def send_resend_verification_email(user) -> bool:
    """
    Regenerate token and send a new verification email.
    
    Args:
        user: User instance
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    logger.info(f'[Email] Regenerating verification token for {user.email}')
    user.regenerate_verification_token()
    logger.info(f'[Email] New token generated for {user.email}')
    return send_verification_email(user)
