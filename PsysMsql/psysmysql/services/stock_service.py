"""
Servicio para manejar la lógica de negocio de stock/inventario
Optimiza consultas y centraliza validaciones
"""

from django.db.models import Q, F, Sum
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ..models import Stock, Products
from ..logging_config import get_logger, log_execution_time, LogOperation


class StockService:
    """Servicio para operaciones relacionadas con stock"""

    @staticmethod
    @log_execution_time()
    def search_item_in_stock(id_product):

        logger = get_logger("stock")

        with LogOperation(f"Buscando item en stock: {id_product}", logger):
            result_item_stock = Stock.objects.filter(id_products=id_product)
        return result_item_stock

    @staticmethod
    @log_execution_time()
    def get_stock_summary():
        """
        Obtener resumen completo de stock optimizado
        """
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

    @staticmethod
    @log_execution_time()
    def update_stock(product_id, quantity, operation="set"):
        """
        Actualizar el stock de un producto de manera segura

        Args:
            product_id: ID del producto
            quantity: Cantidad a agregar/reducir/establecer
            operation: 'add', 'subtract', 'set'
        """
        logger = get_logger("stock")

        with LogOperation(
            f"Actualizando stock producto {product_id}: {operation} {quantity}", logger
        ):
            try:
                product = Products.objects.get(pk=product_id)
            except Products.DoesNotExist:
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

    @staticmethod
    def check_stock_availability(product_id, required_quantity):
        """
        Verificar si hay stock suficiente para una venta
        """
        logger = get_logger("stock")

        try:
            stock = Stock.objects.get(id_products_id=product_id)
            available = stock.quantitystock >= required_quantity

            if not available:
                logger.warning(
                    f"Stock insuficiente para producto {product_id}: disponible {stock.quantitystock}, requerido {required_quantity}"
                )

            return {
                "available": available,
                "current_stock": stock.quantitystock,
                "required": required_quantity,
                "remaining_after": (
                    stock.quantitystock - required_quantity if available else None
                ),
            }
        except Stock.DoesNotExist:
            logger.error(f"No hay registro de stock para producto {product_id}")
            return {
                "available": False,
                "current_stock": 0,
                "required": required_quantity,
                "remaining_after": None,
            }

    @staticmethod
    def get_stock_alerts():
        """
        Obtener alertas de stock para dashboard
        """
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

    @staticmethod
    def bulk_update_stock(stock_updates):
        """
        Actualizar múltiples productos en lote de manera eficiente

        Args:
            stock_updates: Lista de diccionarios con {product_id, quantity, operation}
        """
        logger = get_logger("stock")

        with LogOperation(
            f"Actualización masiva de stock: {len(stock_updates)} productos", logger
        ):
            results = []
            errors = []

            for update in stock_updates:
                try:
                    result = StockService.update_stock(
                        update["product_id"],
                        update["quantity"],
                        update.get("operation", "set"),
                    )
                    results.append(result)
                except Exception as e:
                    error_msg = (
                        f"Error actualizando producto {update['product_id']}: {str(e)}"
                    )
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(
                f"Actualización masiva completada: {len(results)} exitosos, {len(errors)} errores"
            )

            return {
                "successful": results,
                "errors": errors,
                "total_processed": len(stock_updates),
            }

    @staticmethod
    def get_stock_movements_report(days=30):
        """
        Genera reporte de movimientos de stock
        """
        from django.utils import timezone
        from datetime import timedelta

        logger = get_logger("stock")

        with LogOperation(f"Generando reporte de movimientos ({days} días)", logger):
            # Por ahora básico, se puede expandir con tabla de movimientos
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            # Obtener productos con cambios recientes (basado en SellProducts)
            from ..models import SellProducts

            recent_movements = (
                SellProducts.objects.select_related("idproduct")
                .filter(
                    # Filtrar por fecha cuando esté disponible
                )
                .values("idproduct__name", "idproduct__idproducts")
                .annotate(total_sold=Sum("quantity"))
                .order_by("-total_sold")[:20]
            )

            return {
                "period": f"{days} días",
                "start_date": start_date,
                "end_date": end_date,
                "top_movements": list(recent_movements),
            }

    @staticmethod
    def suggest_restock_quantities():
        """
        Sugiere cantidades de reposición basadas en histórico
        """
        logger = get_logger("stock")

        with LogOperation("Generando sugerencias de reposición", logger):
            # Algoritmo simple: productos con stock bajo
            suggestions = []

            low_stock_items = (
                Stock.objects.select_related("id_products")
                .filter(quantitystock__lt=10)
                .order_by("quantitystock")
            )

            for item in low_stock_items:
                # Sugerencia simple: mínimo 20 unidades
                suggested_quantity = max(20, item.quantitystock * 3)

                suggestions.append(
                    {
                        "product_id": item.id_products.idproducts,
                        "product_name": item.id_products.name,
                        "current_stock": item.quantitystock,
                        "suggested_order": suggested_quantity,
                        "priority": "high" if item.quantitystock == 0 else "medium",
                    }
                )

            logger.info(f"Generadas {len(suggestions)} sugerencias de reposición")
            return suggestions[:10]  # Top 10
