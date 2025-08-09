# myapp/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_sell_confirmation_email(recipient_email, subject, message):
    """
    Tarea Celery para enviar un correo de confirmación de venta.
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL, # Remitente
            [recipient_email], # Lista de destinatarios
            fail_silently=False, # Si es True, no levanta excepciones en caso de error
        )
        print(f"Correo de confirmación enviado exitosamente a {recipient_email}")
        return "Email sent successfully"
    except Exception as e:
        print(f"Error al enviar el correo a {recipient_email}: {e}")
        raise # Vuelve a lanzar la excepción para que Celery la marque como fallida