from datetime import datetime
import json
from decimal import Decimal
from django.db.models import Q, FloatField
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


# Servicio para operaciones relacionadas con ventas"
class SellService:
    iva = float(const.IVA_RATE)  # 19% IVA

    @staticmethod
    @log_execution_time(get_sell_logger())
    def calculate_sell_totals(sell_products_queryset, quantity_pay):
        """
        Calcula todos los totales de una venta de manera optimizada

        Returns:
            dict: Diccionario con todos los cálculos
        """
        logger = get_sell_logger()
        items_count = sell_products_queryset.count()

        if not sell_products_queryset.exists():
            return {
                "list_items": [],
                "list_items_json": "[]",
                "quantity": 0,
                "subtotal": 0.0,
                "iva_calculated": 0.0,
                "price_iva": 0.0,
                "price_x_quantity": 0.0,
                "price_with_iva": 0.0,
                "quantity_pay": 0.0,
                "money_back": 0.0,
            }
        else:
            with LogOperation(
                f"Calculando totales para {items_count} productos", logger
            ):
                list_items = []
                total_quantity = 0
                subtotal = float("0.00")

                # Optimización: usar select_related para evitar consultas N+1
                for item in sell_products_queryset.select_related("idproduct"):

                    item_total = int(str(item.quantity)) * float(item.priceunitaty)
                    subtotal += item_total
                    total_quantity += item.quantity

                    # Cálculos de IVA
                    iva_amount = subtotal * SellService.iva
                    price_without_iva = subtotal - iva_amount

                    # Cálculos de cambio.
                    if quantity_pay is None:
                        pass
                    else:
                        money_back = subtotal - float(quantity_pay)

                        list_items.append(
                            {
                                "id_product": item.idproduct.pk,
                                "name": item.idproduct.name,
                                "quantity": item.quantity,
                                "price": float(item.priceunitaty),
                                "pricexquantity": float(item_total),
                                "iva_calculated": float(iva_amount),
                                "price_iva": float(price_without_iva),
                                "price_with_iva": float(price_without_iva),
                                "quantity_pay": float(str(quantity_pay)),
                                "money_back": float(str(money_back)),
                            }
                        )
                        logger.info(
                            f"Totales calculados: {items_count} productos, subtotal: {subtotal}, IVA: {iva_amount}"
                        )

                    return {
                        "results": list_items,
                        "list_items_json": json.dumps(list_items),
                        "quantity": item.quantity,
                        "price": float(item.priceunitaty),
                        "pricexquantity": float(item_total),
                        "iva_calculated": float(iva_amount),
                        "price_iva": float(price_without_iva),
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
                    logger.info(f"Fallo en la creacion del producto {product.name}")
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

    @staticmethod
    @log_function_call(get_sell_logger())
    def update_quantity_sell_item(product_id, quantity):

        logger = get_sell_logger()

        try:
            product_sell = get_object_or_404(SellProducts, id_product=product_id)

            new_product_sell = Sell(
                id_product=product_sell.id_product,
                totalsell=product_sell.totalsell + quantity,
            )
            new_product_sell.save()
            logger.info(
                f"Cantidad actualizada para producto {product_id}: {quantity} unidades"
            )

        except SellProducts.DoesNotExist:
            logger.error(f"Producto no encontrado en el carrito: ID {product_id}")
            raise ValidationError("Producto no encontrado en el carrito")
        except Exception as e:
            logger.error(
                f"Error actualizando cantidad del producto {product_id}: {str(e)}"
            )

    @staticmethod
    @log_function_call(get_sell_logger())
    def remove_sell_item(item_id):
        # Elimina un item del carrito de venta
        logger = get_sell_logger()

        try:
            with LogOperation(f"Eliminando item {item_id} del carrito", logger):
                item = get_object_or_404(SellProducts, idsell_product=item_id)
                item.delete()
                logger.info(
                    f"Item eliminado del carrito: {item.idproduct} ({item.quantity} unidades)"
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
    def calculate_change(quantity_pay, total_sell_calculated):
        # Calcula el cambio de una venta
        logger = get_sell_logger()

        total = total_sell_calculated
        payment = quantity_pay
        try:
            if payment < total:
                logger.warning(f"Pago insuficiente: total=${total}, pago=${payment}")
                raise ValidationError("El pago es insuficiente")

            change = float(payment) - float(total)
            logger.info(
                f"Cambio calculado: total=${total}, pago=${payment}, cambio=${change}"
            )

            return change

        except Exception as e:
            logger.error(
                f"Error calculando cambio: total={total}, pago={payment}, error={str(e)}"
            )
            raise

    @staticmethod
    @log_function_call(get_sell_logger())
    def create_sell_register(
        employed_id, total_sell, type_pay, state_sell, notes, quantity_pay
    ):
        # Crea un registro de venta completo
        logger = get_sell_logger()
        list_sell_products = SellProducts.objects.all()
        try:
            with LogOperation(
                f"Creando registro de venta: total=${total_sell}", logger
            ):

                list_items = SellService.calculate_sell_totals(
                    list_sell_products, quantity_pay
                )

                register_sell = RegistersellDetail.objects.create(
                    id_employed=employed_id,
                    total_sell=float(str(total_sell)),
                    type_pay=type_pay,
                    state_sell=state_sell,
                    notes=notes,
                    quantity_pay=float(str(quantity_pay)),
                    detail_sell=list_items.get("list_items_json"),
                )

                logger.info(
                    f"Venta registrada exitosamente: ID={register_sell.pk}, empleado={employed_id}, total=${total_sell}, tipo_pago={type_pay}"
                )
                return register_sell

        except Exception as e:
            logger.error(
                f"Error creando registro de venta: empleado={employed_id}, total={total_sell}, error={e}"
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

            # Obtener información de sesión
            money_back = request.session.pop("money_back", None)
            quantity_pay = request.session.pop("quantity_pay", None)
            # Calcular totales

            totals = SellService.calculate_sell_totals(list_sell_products, quantity_pay)

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
    def get_sales_statistics(date_from=None, date_to=None):
        """
        Obtiene estadísticas de ventas para un período específico
        """
        logger = get_sell_logger()

        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with LogOperation(
                f"Obteniendo estadísticas de ventas: {date_now} a {date_now}", logger
            ):
                queryset = RegistersellDetail.objects.all()

                if date_from:
                    queryset = queryset.filter(created_at__gte=date_from)
                if date_to:
                    queryset = queryset.filter(created_at__lte=date_to)

                from django.db.models import Sum, Count, Avg

                stats = queryset.aggregate(
                    total_sales=Count("idsell"),
                    total_revenue=Sum("total_sell", output_field=FloatField()),
                    average_sale=Avg("total_sell", output_field=FloatField()),
                )
                # Obtener tipos de pago.
                payment_types = (
                    queryset.values("type_pay")
                    .annotate(count=Count("type_pay"))
                    .order_by("-count")
                )

                stats["payment_types"] = list(payment_types)
                stats["period"] = f"{date_now or 'inicio'} - {date_to or 'fin'}"

                logger.info(
                    f'Estadísticas calculadas: {stats["total_sales"]} ventas, ingresos totales=${stats["total_revenue"]}'
                )

                return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de ventas: {str(e)}")
            raise
