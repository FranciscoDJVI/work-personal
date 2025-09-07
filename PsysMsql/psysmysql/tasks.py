# myapp/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings


@shared_task
def send_sell_confirmation_email(recipient_email, subject, body, pdf_data):
    """
    Tarea Celery para enviar un correo de confirmación de venta con un PDF adjunto.

    Args:
        recipient_email (str): Correo del destinatario.
        subject (str): Asunto del correo.
        body (str): Cuerpo del mensaje (texto simple o HTML).
        pdf_data (bytes): Contenido del PDF como una cadena de bytes.
    """
    try:
        # Crear objeto EmailMessage
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )

        # Adjuntar  PDF.
        # El primer argumento es el nombre del archivo, el segundo es el contenido en bytes,
        # y el tercero es el tipo MIME del archivo.
        email.attach("factura.pdf", pdf_data, "application/pdf")

        # Envíar correo usando el método .send() de la clase EmailMessage
        email.send(fail_silently=False)
        print(f"Correo de confirmación enviado exitosamente a {recipient_email}")
        return "Email sent successfully"

    except Exception as e:
        print(f"Error al enviar el correo a {recipient_email}: {e}")
        raise  # Vuelve a lanzar la excepción
