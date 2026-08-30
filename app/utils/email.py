import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from flask import current_app

logger = logging.getLogger(__name__)

def _send_async_email(app, msg, mail_server, mail_port, mail_username, mail_password):
    with app.app_context():
        try:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
            server.quit()
            logger.info("Correo enviado correctamente")
        except Exception as e:
            logger.error("Error enviando correo: %s", e)

def enviar_correo(destinatario, asunto, cuerpo_html):
    """
    Envía un correo electrónico de forma asíncrona usando SMTP.
    Requiere que las variables de entorno MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD estén configuradas.
    """
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER') or mail_username

    if not mail_username or not mail_password:
        logger.warning("Credenciales SMTP no configuradas: no se envio el correo.")
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = asunto
    msg['From'] = mail_default_sender
    msg['To'] = destinatario

    part = MIMEText(cuerpo_html, 'html')
    msg.attach(part)

    app = current_app._get_current_object()
    thread = Thread(target=_send_async_email, args=(app, msg, mail_server, mail_port, mail_username, mail_password))
    thread.start()
    return True
