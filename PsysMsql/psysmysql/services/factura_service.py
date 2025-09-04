from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import date
from ..models import Clients
from ..services.search_orm import Search
from ..constants import IVA_RATE


class GetDataClientForBill:
    @staticmethod
    def get_data_client(email: str):
        client_list: list = []
        client = Search.filter(Clients, "email", email)
        for client_info in client:
            client_list.append(
                {
                    "name": client_info.name,
                    "direction": client_info.direction,
                }
            )
        return client_list


def create_bill(nombre_archivo, datos_factura):
    # Crear un documento PDF
    doc = SimpleDocTemplate(
        nombre_archivo,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    story = []

    # --- Encabezado de la factura ---

    # Estilo para el encabezado (negrita y centrado)
    estilo_encabezado = ParagraphStyle(
        "Encabezado",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        alignment=1,
    )
    # Título de la factura
    story.append(Paragraph("FACTURA", estilo_encabezado))
    story.append(Spacer(1, 0.5 * cm))

    # Información de la empresa
    estilo_info = ParagraphStyle("Info", parent=estilos["Normal"], fontSize=10)
    story.append(Paragraph("<b>Nombre de la Empresa:</b> Mi Empresa S.A.", estilo_info))
    story.append(Paragraph("<b>Dirección:</b> Calle Ficticia 123", estilo_info))
    story.append(Paragraph("<b>Ciudad:</b> Ciudad del Sol", estilo_info))
    story.append(
        Paragraph(f"<b>Fecha:</b> {date.today().strftime('%d/%m/%Y')}", estilo_info)
    )
    story.append(
        Paragraph(f"<b>Factura Nº:</b> {datos_factura['numero']}", estilo_info)
    )
    story.append(Spacer(1, 0.5 * cm))

    # Información del cliente
    story.append(Paragraph("<b>Cliente:</b>", estilo_info))
    story.append(
        Paragraph(f"<b>Nombre:</b> {datos_factura['cliente']['nombre']}", estilo_info)
    )
    story.append(
        Paragraph(
            f"<b>Dirección:</b> {datos_factura['cliente']['direccion']}", estilo_info
        )
    )
    story.append(Spacer(1, 1 * cm))

    # --- Tabla de productos ---

    # Datos de la tabla
    datos_tabla = [["Cantidad", "Descripción", "Precio Unitario", "Total"]]
    subtotal = 0
    for item in datos_factura["items"]:
        total_item = item["cantidad"] * item["precio"]
        subtotal += total_item
        datos_tabla.append(
            [
                item["cantidad"],
                f"{item['precio']:.2f}",
                f"{total_item:.2f}",
            ]
        )

    # Calcular IVA y total
    iva = float(subtotal) * float(IVA_RATE)  # Ejemplo con 16% de IVA
    total_final = float(subtotal) + iva

    datos_tabla.append(["", "", "Subtotal:", f"{subtotal:.2f}"])
    datos_tabla.append(["", "", "IVA (16%):", f"{iva:.2f}"])
    datos_tabla.append(["", "", "Total:", f"{total_final:.2f}"])

    # Crear la tabla y aplicar estilos
    tabla = Table(datos_tabla, colWidths=[2.5 * cm, 9 * cm, 3.5 * cm, 3.5 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT",
                ),  # Alinear a la derecha las columnas de precios y totales
                (
                    "BACKGROUND",
                    (2, -3),
                    (-1, -1),
                    colors.lightgrey,
                ),  # Fondo para los totales
                ("FONTNAME", (2, -3), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(tabla)
    story.append(Spacer(1, 1 * cm))

    # Pie de página o notas adicionales
    story.append(Paragraph("¡Gracias por su compra!", estilos["Normal"]))

    # Construir el documento
    doc.build(story)


# Datos de ejemplo para la factura
datos = {
    "numero": "2025-001",
    "cliente": {"nombre": "Juan Pérez", "direccion": "Avenida del Sol 456"},
    "items": [
        {"cantidad": 2, "descripcion": "Producto A", "precio": 150.00},
        {"cantidad": 1, "descripcion": "Servicio de Consultoría", "precio": 500.00},
        {"cantidad": 3, "descripcion": "Producto B", "precio": 75.50},
    ],
}

# Generar la factura

# create_bill("factura_ejemplo.pdf", datos)
print("Factura generada como factura_ejemplo.pdf")
