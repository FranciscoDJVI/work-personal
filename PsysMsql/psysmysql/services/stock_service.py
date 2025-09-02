from django.db.models import Q, ObjectDoesNotExist, F, Sum
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ..models import Stock, Products
from ..logging_config import get_logger, log_execution_time, LogOperation
from ..services.search_orm import Search


class SearchItemInStock:
    @staticmethod
    @log_execution_time()
    def search_item(id_product):

        logger = get_logger("stock")

        with LogOperation(f"Buscando item en stock: {id_product}", logger):
            result_item_stock = Search.filter(Stock, "id_products", id_product)
        return result_item_stock


class CreateStock:

    @staticmethod
    @log_execution_time()
    def create_or_update_stock(product_id, quantity, operation="set"):

        logger = get_logger("stock")

        with LogOperation(
            f"Actualizando stock producto {product_id}: {operation} {quantity}", logger
        ):
            try:
                product = Search.get(Products, "pk", product_id)
            except ObjectDoesNotExist:
                logger.error(f"Producto {product_id} no existe")
                raise ValidationError(f"Producto con ID {product_id} no encontrado")

            # Obtener o crear stock
            stock, created = Stock.objects.get_or_create(
                id_products=product, defaults={"quantitystock": 0}
            )

            # Aplicar operación
            if operation == "add":
                stock.quantitystock = F("quantitystock") + quantity
            elif operation == "subtract":
                # Validar que no quede negativo
                if stock.quantitystock < quantity:
                    logger.warning(
                        f"Intento de reducir stock por debajo de 0 para producto {product_id}"
                    )
                    raise ValidationError(
                        f"Stock insuficiente. Disponible: {stock.quantitystock}, Solicitado: {quantity}"
                    )
                stock.quantitystock = F("quantitystock") - quantity
            elif operation == "set":
                stock.quantitystock = quantity
            else:
                raise ValidationError(
                    "Operación inválida. Use 'add', 'subtract' o 'set'"
                )

            stock.save(update_fields=["quantitystock"])

            # Refrescar desde DB para obtener valor actualizado
            stock.refresh_from_db()

            logger.info(
                f"Stock actualizado para producto {product.name}: {stock.quantitystock}"
            )

            return stock


class GetStcokSummaty:
    @staticmethod
    @log_execution_time()
    def get_stock_summary():
        logger = get_logger("stock")

        with LogOperation("Generando resumen de stock", logger):
            # Query optimizada con agregaciones
            stock_data = Stock.objects.select_related("id_products").aggregate(
                total_products=Sum("quantitystock"),
                low_stock_count=Sum(1, filter=Q(quantitystock__lt=10)),
                out_of_stock_count=Sum(1, filter=Q(quantitystock=0)),
            )

            # Productos con stock bajo
            low_stock_products = (
                Stock.objects.select_related("id_products")
                .filter(quantitystock__lt=10, quantitystock__gt=0)
                .order_by("quantitystock")[:10]
            )

            # Productos sin stock
            out_of_stock_products = (
                Stock.objects.select_related("id_products")
                .filter(quantitystock=0)
                .order_by("id_products__name")[:10]
            )

            summary = {
                "total_products_in_stock": stock_data.get("total_products", 0) or 0,
                "low_stock_count": stock_data.get("low_stock_count", 0) or 0,
                "out_of_stock_count": stock_data.get("out_of_stock_count", 0) or 0,
                "low_stock_products": list(low_stock_products),
                "out_of_stock_products": list(out_of_stock_products),
            }

            logger.info(
                f"Resumen de stock generado: {summary['total_products_in_stock']} productos"
            )
            return summary


class GetStockAlerts:
    @staticmethod
    def get_stock_alerts():
        logger = get_logger("stock")

        with LogOperation("Generando alertas de stock", logger):
            alerts = []

            # Productos sin stock
            out_of_stock = (
                Stock.objects.select_related("id_products")
                .filter(quantitystock=0)
                .count()
            )

            if out_of_stock > 0:
                alerts.append(
                    {
                        "type": "error",
                        "message": f"{out_of_stock} productos sin stock",
                        "count": out_of_stock,
                    }
                )

            # Productos con stock bajo (menos de 10)
            low_stock = (
                Stock.objects.select_related("id_products")
                .filter(quantitystock__gt=0, quantitystock__lt=10)
                .count()
            )

            if low_stock > 0:
                alerts.append(
                    {
                        "type": "warning",
                        "message": f"{low_stock} productos con stock bajo",
                        "count": low_stock,
                    }
                )

            logger.info(f"Alertas generadas: {len(alerts)}")
            return alerts
