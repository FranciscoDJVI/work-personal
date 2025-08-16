"""
Servicio para manejar la lógica de negocio de ventas
Calcula precios, IVA, maneja el carrito de compras, etc.
"""

import json
from decimal import Decimal
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ..models import SellProducts, Products, Clients, RegistersellDetail, Sell
from django.core.cache import cache
from ..logging_config import (
    get_sell_logger,
    log_execution_time,
    log_function_call,
    LogOperation,
)
import psysmysql.constants as const


class SellService:
    """Servicio para operaciones relacionadas con ventas"""

    # Constantes de negocio centralizadas
    iva = Decimal(const.IVA_RATE)  # 19% IVA

    @staticmethod
    @log_execution_time(get_sell_logger())
    def calculate_sell_totals(sell_products_queryset):
        """
        Calcula todos los totales de una venta de manera optimizada

        Returns:
            dict: Diccionario con todos los cálculos
        """
        logger = get_sell_logger()
        items_count = sell_products_queryset.count()

        with LogOperation(f"Calculando totales para {items_count} productos", logger):
            list_items = []
            total_quantity = 0
            subtotal = Decimal("0.00")

            # Optimización: usar select_related para evitar consultas N+1
            for item in sell_products_queryset.select_related("idproduct"):
                item_total = Decimal(str(item.quantity)) * item.priceunitaty
                subtotal += item_total
                total_quantity += item.quantity

                list_items.append(
                    {
                        "id_product": item.idproduct.pk,
                        "name": item.idproduct.name,
                        "quantity": item.quantity,
                        "price": float(item.priceunitaty),
                        "pricexquantity": float(item_total),
                    }
                )

            # Cálculos de IVA
            iva_amount = subtotal * SellService.iva
            price_without_iva = subtotal - iva_amount

            logger.info(
                f"Totales calculados: {items_count} productos, subtotal: {subtotal}, IVA: {iva_amount}"
            )

            return {
                "list_items": list_items,
                "list_items_json": json.dumps(list_items),
                "quantity": total_quantity,
                "subtotal": float(subtotal),
                "iva_calculated": float(iva_amount),
                "price_iva": float(price_without_iva),
                "price_x_quantity": float(subtotal),
                "price_with_iva": float(price_without_iva),
            }

    @staticmethod
    @log_function_call(get_sell_logger())
    def add_product_to_sell(product_id, quantity):
        """
        Agrega un producto al carrito de venta actual
        """
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Agregando producto {product_id} con cantidad {quantity}", logger
            ):
                product = get_object_or_404(Products, pk=product_id)

                # Crear o actualizar el item en SellProducts
                sell_product, created = Sell.objects.get_or_create(
                    id_product=product,
                    totalsell=quantity,
                )

                if not created:
                    # Si ya existe, actualizar cantidad
                    old_quantity = sell_product.totalsell
                    sell_product.totalsell += old_quantity
                    sell_product.save()
                    logger.info(
                        f"Producto {product.name} actualizado: cantidad nueva -> {sell_product.totalsell}"
                    )
                else:
                    logger.info(
                        f"Nuevo producto {product.name} agregado al carrito: {quantity} unidades"
                    )

                return sell_product

        except Products.DoesNotExist:
            logger.error(f"Intento de agregar producto inexistente: ID {product_id}")
            raise ValidationError("Producto no encontrado")
        except Exception as e:
            logger.error(f"Error agregando producto {product_id}: {str(e)}")
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def remove_sell_item(item_id):
        """
        Elimina un item del carrito de venta
        """
        logger = get_sell_logger()

        try:
            with LogOperation(f"Eliminando item {item_id} del carrito", logger):
                item = SellProducts.objects.get(pk=item_id)
                product_name = item.idproduct.name
                quantity = item.quantity
                item.delete()

                logger.info(
                    f"Item eliminado del carrito: {product_name} ({quantity} unidades)"
                )
                return True

        except SellProducts.DoesNotExist:
            logger.error(f"Intento de eliminar item inexistente: ID {item_id}")
            raise ValidationError("Item no encontrado")
        except Exception as e:
            logger.error(f"Error eliminando item {item_id}: {str(e)}")
            raise

    @staticmethod
    def search_clients_by_email(query):
        """
        Busca clientes por email con optimizaciones
        """
        if not query:
            return []

        return Clients.objects.filter(Q(email__icontains=query)).distinct()

    @staticmethod
    @log_function_call(get_sell_logger())
    def calculate_change(total_amount, payment_amount):
        """
        Calcula el cambio de una venta
        """
        logger = get_sell_logger()

        try:
            total = Decimal(str(total_amount))
            payment = Decimal(str(payment_amount))

            if payment < total:
                logger.warning(f"Pago insuficiente: total=${total}, pago=${payment}")
                raise ValidationError("El pago es insuficiente")

            change = float(payment - total)
            logger.info(
                f"Cambio calculado: total=${total}, pago=${payment}, cambio=${change}"
            )

            return change

        except Exception as e:
            logger.error(
                f"Error calculando cambio: total={total_amount}, pago={payment_amount}, error={str(e)}"
            )
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def create_sell_register(
        employee_id, total_sell, type_pay, state_sell, notes, quantity_pay, detail_sell
    ):
        """
        Crea un registro de venta completo
        """
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Creando registro de venta: total=${total_sell}", logger
            ):
                sell_register = RegistersellDetail.objects.create(
                    id_employed=employee_id,
                    total_sell=Decimal(str(total_sell)),
                    type_pay=type_pay,
                    state_sell=state_sell,
                    notes=notes,
                    quantity_pay=Decimal(str(quantity_pay)) if quantity_pay else None,
                    detail_sell=detail_sell,
                )

                logger.info(
                    f"Venta registrada exitosamente: ID={sell_register.pk}, empleado={employee_id}, total=${total_sell}, tipo_pago={type_pay}"
                )
                return sell_register

        except Exception as e:
            logger.error(
                f"Error creando registro de venta: empleado={employee_id}, total={total_sell}, error={str(e)}"
            )
            raise

    @staticmethod
    @log_execution_time(get_sell_logger())
    def get_sell_summary_for_template(request):
        """
        Obtiene resumen completo para mostrar en template de venta
        Método principal que unifica toda la lógica del contexto
        """
        logger = get_sell_logger()

        with LogOperation("Obteniendo resumen de venta para template", logger):
            # Obtener productos en el carrito
            list_sell_products = SellProducts.objects.all()
            products_count = list_sell_products.count()

            # Calcular totales
            totals = SellService.calculate_sell_totals(list_sell_products)

            # Obtener información de sesión
            money_back = request.session.pop("money_back", None)
            quantity_pay = request.session.pop("quantity_pay", None)

            # Combinar toda la información
            context = {
                **totals,
                "list_sell_products": list_sell_products,
                "quantity_pay": quantity_pay,
                "money_back": money_back,
            }

            logger.info(
                f'Resumen de venta preparado: {products_count} productos, subtotal={totals.get("subtotal", 0)}'
            )

            if money_back:
                logger.info(f"Cambio devuelto: ${money_back}")
            if quantity_pay:
                logger.info(f"Cantidad pagada: ${quantity_pay}")

            return context

    @staticmethod
    def validate_sell_data(product_id, quantity):
        """
        Valida los datos de una venta antes de procesarla
        """
        errors = []

        if not product_id:
            errors.append("Debe seleccionar un producto")

        if not quantity or quantity <= 0:
            errors.append("La cantidad debe ser mayor a 0")

        # Validar que el producto existe
        if product_id:
            try:
                product = Products.objects.get(pk=product_id)
                return product
                # Aquí podrías validar stock disponible
            except Products.DoesNotExist:
                errors.append("El producto seleccionado no existe")

        return errors

    @staticmethod
    @log_function_call(get_sell_logger())
    def clear_sell_cache():
        """
        Limpia el cache relacionado con ventas
        """
        logger = get_sell_logger()

        try:
            cache.delete("current_sell_products")
            cache.delete("sell_totals")
            logger.info("Cache de ventas limpiado exitosamente")
        except Exception as e:
            logger.error(f"Error limpiando cache de ventas: {str(e)}")
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def process_complete_sale(
        employee_id, payment_amount, payment_type="efectivo", notes="", clear_cart=True
    ):
        """
        Procesa una venta completa desde el carrito hasta el registro final
        Método principal para completar transacciones de venta
        """
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Procesando venta completa: empleado={employee_id}, pago=${payment_amount}",
                logger,
            ):
                # 1. Obtener productos del carrito
                sell_products = SellProducts.objects.all()
                if not sell_products.exists():
                    logger.warning("Intento de procesar venta con carrito vacío")
                    raise ValidationError("No hay productos en el carrito")

                # 2. Calcular totales
                totals = SellService.calculate_sell_totals(sell_products)
                total_amount = totals["subtotal"]

                # 3. Validar pago
                if payment_amount < total_amount:
                    logger.error(
                        f"Pago insuficiente: necesario=${total_amount}, recibido=${payment_amount}"
                    )
                    raise ValidationError("Pago insuficiente")

                # 4. Calcular cambio
                change = SellService.calculate_change(total_amount, payment_amount)

                # 5. Crear registro de venta
                sell_register = SellService.create_sell_register(
                    employee_id=employee_id,
                    total_sell=total_amount,
                    type_pay=payment_type,
                    state_sell="completada",
                    notes=notes,
                    quantity_pay=payment_amount,
                    detail_sell=totals["list_items_json"],
                )

                # 6. Limpiar carrito si se solicita
                if clear_cart:
                    sell_products.delete()
                    SellService.clear_sell_cache()
                    logger.info("Carrito limpiado después de venta exitosa")

                logger.info(
                    f"Venta procesada exitosamente: ID={sell_register.pk}, cambio=${change}"
                )

                return {
                    "sell_register": sell_register,
                    "change": change,
                    "total": total_amount,
                    "products_sold": totals["quantity"],
                }

        except Exception as e:
            logger.error(f"Error procesando venta completa: {str(e)}")
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def get_sales_statistics(date_from=None, date_to=None):
        """
        Obtiene estadísticas de ventas para un período específico
        """
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Obteniendo estadísticas de ventas: {date_from} a {date_to}", logger
            ):
                queryset = RegistersellDetail.objects.all()

                if date_from:
                    queryset = queryset.filter(created_at__gte=date_from)
                if date_to:
                    queryset = queryset.filter(created_at__lte=date_to)

                from django.db.models import Sum, Count, Avg

                stats = queryset.aggregate(
                    total_sales=Count("id"),
                    total_revenue=Sum("total_sell"),
                    average_sale=Avg("total_sell"),
                )

                # Obtener tipos de pago más comunes
                payment_types = (
                    queryset.values("type_pay")
                    .annotate(count=Count("type_pay"))
                    .order_by("-count")
                )

                stats["payment_types"] = list(payment_types)
                stats["period"] = f"{date_from or 'inicio'} - {date_to or 'fin'}"

                logger.info(
                    f'Estadísticas calculadas: {stats["total_sales"]} ventas, ingresos totales=${stats["total_revenue"]}'
                )

                return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de ventas: {str(e)}")
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def validate_cart_before_checkout():
        """
        Valida el carrito antes del checkout
        Verifica stock, precios, y otros requisitos de negocio
        """
        logger = get_sell_logger()

        try:
            with LogOperation("Validando carrito antes del checkout", logger):
                sell_products = SellProducts.objects.select_related("idproduct").all()

                if not sell_products.exists():
                    return {"valid": False, "errors": ["Carrito vacío"]}

                errors = []
                warnings = []

                for item in sell_products:
                    # Validar que el producto aún existe
                    if not item.idproduct:
                        errors.append(f"Producto eliminado en el carrito")
                        continue

                    # Validar precio actualizado
                    current_price = item.idproduct.price
                    if abs(float(current_price - item.priceunitaty)) > 0.01:
                        warnings.append(
                            f"Precio de {item.idproduct.name} ha cambiado: ${item.priceunitaty} -> ${current_price}"
                        )

                    # Aquí podrías validar stock si tienes esa funcionalidad
                    # if item.quantity > item.idproduct.stock:
                    #     errors.append(f'Stock insuficiente para {item.idproduct.name}')

                result = {
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings,
                    "products_count": sell_products.count(),
                }

                if result["valid"]:
                    logger.info(
                        f'Carrito validado exitosamente: {result["products_count"]} productos'
                    )
                else:
                    logger.warning(
                        f"Carrito inválido: {len(errors)} errores, {len(warnings)} advertencias"
                    )

                return result

        except Exception as e:
            logger.error(f"Error validando carrito: {str(e)}")
            raise
