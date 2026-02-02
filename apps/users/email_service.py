"""
Email service for sending verification emails.
Uses Gmail SMTP for sending emails.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def get_verification_url(token: str) -> str:
    """Build the verification URL for a given token."""
    # Use BACKEND_URL for the verification endpoint (renders HTML directly)
    base_url = settings.BACKEND_URL.rstrip('/')
    return f"{base_url}/api/auth/verify/{token}/"


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
        
        sent = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if sent:
            logger.info(f'[Email] SUCCESS - Verification email sent to {user.email}')
            return True
        else:
            logger.warning(f'[Email] FAILED - send_mail returned 0 for {user.email}')
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
