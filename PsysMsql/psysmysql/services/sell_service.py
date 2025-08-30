from datetime import datetime, timezone
from itertools import starmap
from time import localtime
import json
from django.db.models import Q, FloatField, Count, Sum
from django.core.exceptions import ValidationError
from django.db.models.sql.query import count
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


class SearchByField:
    @staticmethod
    def filter(model: type, field: str, value):
        filter_kwargs = {field: value}
        return model.objects.filter(**filter_kwargs)


class Search:
    @staticmethod
    def search(model: type):
        return model.objects.all()


class RegisterSell:

    @staticmethod
    @log_execution_time(get_sell_logger())
    def register_sell(id_product, total_sell):
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Agregando producto {id_product} con cantidad {total_sell}", logger
            ):
                product = get_object_or_404(Products, pk=id_product.idproducts)

                register_sell = Sell(totalsell=total_sell, id_product=id_product)
                register_sell.save()
                if not register_sell.idsell:
                    logger.info(f"Fallo en la creacion del producto {product.name}")
                else:
                    logger.info(
                        f"Nuevo producto {product.name} agregado al carrito: {total_sell} unidades"
                    )
        except Products.DoesNotExist:
            logger.error(
                f"Intento de agregar producto inexistente: ID {id_product.idproducts}"
            )
            raise ValidationError("Producto no encontrado")
        except Exception as e:
            logger.error(f"Error agregando producto {id_product.idproducts}: {str(e)}")


class RegisterSellDetails:

    @staticmethod
    @log_execution_time(get_sell_logger())
    def register_detail(
        id_employed,
        total_sell,
        type_pay,
        state_sell,
        notes,
        detail_sell,
        quantity_pay,
    ):
        logger = get_sell_logger()
        try:
            with LogOperation(
                f"Creando registro de venta: total=${total_sell}", logger
            ):

                register_sell_detail = RegistersellDetail(
                    id_employed=id_employed,
                    total_sell=total_sell,
                    type_pay=type_pay,
                    state_sell=state_sell,
                    notes=notes,
                    detail_sell=detail_sell,
                    quantity_pay=quantity_pay,
                )
                register_sell_detail.save()
            logger.info(
                f"Venta registrada exitosamente: ID={detail_sell}, empleado={id_employed}, total=${total_sell}, tipo_pago={type_pay}"
            )
        except Exception as e:
            logger.error(
                f"Error creando registro de venta: empleado={id_employed}, total={total_sell}, error={e}"
            )
            raise


class GetStatistic:

    @staticmethod
    def get_register_sell_statistic():
        all_register_sells = RegistersellDetail.objects.all()
        registers: list = []
        for register in all_register_sells:
            registers.append(
                {
                    "id_register": int(register.idsell),
                    "date": str(register.date),
                    "id_employed": str(register.id_employed),
                    "total_sell": float(register.total_sell),
                    "type_pay": str(register.type_pay),
                    "state_sell": str(register.state_sell),
                    "notes": str(register.notes),
                    "detail_sell": str(register.detail_sell),
                }
            )
        print(registers)
        return json.dumps(registers)

    @staticmethod
    def quantity_total_sells():
        all_register_sells_count = RegistersellDetail.objects.all().count()
        return json.dumps(all_register_sells_count)

    @staticmethod
    def quantity_and_types_payment():
        all_type_payment = RegistersellDetail.objects.values("type_pay").annotate(
            count=Count("type_pay")
        )
        type_payments: list = []

        for item in all_type_payment:
            type_payments.append(
                {
                    "type_pay": str(item.get("type_pay")),
                    "count": int(item.get("count")),
                }
            )
        return json.dumps(type_payments)

    @staticmethod
    def total_money_sell():
        total_money: dict = {}
        total_money_sells = RegistersellDetail.objects.aggregate(
            total_sum=Sum("total_sell")
        )
        if not total_money_sells.get("total"):
            total_money = {}
        else:
            total_money = {"total": float(total_money_sells.get("total_sum"))}
        return json.dumps(total_money)


class GetIndividualtatistic:
    @staticmethod
    def get_individual_statistics(pk):
        return SearchByField.filter(RegistersellDetail, "idsell", pk)


class GetSellProductQueryset:

    @staticmethod
    def get_sell_product_queryset(pk):
        detail_sell_product_queryset = SearchByField.filter(
            SellProducts, "idproduct", pk
        )

        detail_list: list = []

        for detail in detail_sell_product_queryset:
            detail_list = [
                {
                    "idsell_product": detail.idsell_product,
                    "name": detail.idproduct.name,
                    "quantity": detail.quantity,
                    "priceunitary": float(detail.priceunitaty),
                    "pricexquantity": float(detail.quantity * detail.priceunitaty),
                }
            ]
        return detail_list


class DeleteSellItem:
    @staticmethod
    def delete_sell(pk):
        item = SearchByField.filter(SellProducts, "idsell_product", pk)
        item.delete()


class Calculated_totals:
    iva_rate = const.IVA_RATE  # Ejemplo: 19% de IVA

    @staticmethod
    def calculated_totals():
        total_quantity = 0
        subtotal = 0.0

        sell_products = Search.search(SellProducts)

        for product in sell_products:
            total_quantity += product.quantity
            subtotal += product.quantity * float(product.priceunitaty)

        iva_amount = subtotal * Calculated_totals.iva_rate
        total_sell = subtotal

        totals = {
            "quantity": total_quantity,
            "subtotal": subtotal - iva_amount,
            "iva": iva_amount,
            "total_sell": total_sell,
        }
        return totals


"""class SellService:
    iva = float(const.IVA_RATE)  # 19% IVA

    @staticmethod
    @log_execution_time(get_sell_logger())
    def calculate_sell_totals(sell_products_queryset, quantity_pay):
        logger = get_sell_logger()
        items_count = float(sell_products_queryset.count())
        with LogOperation(f"Calculando totales para {items_count} productos", logger):
            list_items: list = []
            total_quantity: int = 0
            subtotal: float = 0.0
            iva_total: float = 0.0
            total: float = 0.0

        for item in sell_products_queryset.select_related("idproduct"):
            id_product = item.idproduct.pk
            name = item.idproduct.name
            quantity = item.quantity
            total_quantity += item.quantity
            price = float(item.priceunitaty)
            pricexquantity = float(item.priceunitaty * quantity)
            iva = float(pricexquantity * SellService.iva)
            iva_total += float(iva)
            subtotal += float(pricexquantity - iva_total)
            total += pricexquantity

            logger.info(
                f"Totales calculados: {items_count} productos, subtotal: {subtotal}, IVA: {iva_total}"
            )
            return {
                "id": id_product,
                "name": name,
                "quantity": quantity,
                "price": price,
                "iva": iva,
                "pricexquantity": pricexquantity,
                "quantity_total": total_quantity,
                "subtotal": subtotal,
                "iva_total": iva_total,
                "total": total,
            }

    @staticmethod
    @log_function_call(get_sell_logger())
    def add_product_to_sell(product_id, quantity):
        Agregar un producto al carrito de venta actual
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Agregando producto {product_id} con cantidad {quantity}", logger
            ):
                product = get_object_or_404(Products, pk=product_id)

                # Crear o actualizar el item en SellProducts
                sell_product = Sell(
                    id_product=product,
                    totalsell=quantity,
                )
                sell_product.save()
                if not sell_product:
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
        Busca clientes por email con optimizaciones
        if not query:
            return []

        return Clients.objects.filter(Q(email__icontains=query)).distinct()

    @staticmethod
    @log_function_call(get_sell_logger())
    def calculate_change(quantity_pay, total):
        # Calcula el cambio de una venta
        logger = get_sell_logger()

        try:
            if quantity_pay < total:
                logger.warning(
                    f"Pago insuficiente: total=${total}, pago=${quantity_pay}"
                )
                raise ValidationError("El pago es insuficiente")

            change = float(quantity_pay) - float(total)
            logger.info(
                f"Cambio calculado: total=${total}, pago=${quantity_pay}, cambio=${change}"
            )

            return change

        except Exception as e:
            logger.error(
                f"Error calculando cambio: total={total}, pago={quantity_pay}, error={str(e)}"
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
                    total_sell=total_sell,
                    type_pay=type_pay,
                    state_sell=state_sell,
                    notes=notes,
                    quantity_pay=float(str(quantity_pay)),
                    detail_sell=list_items,
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
        Obtiene resumen completo para mostrar en template de venta
        Método principal que unifica toda la lógica del contexto
        logger = get_sell_logger()

        with LogOperation("Obteniendo resumen de venta para template", logger):
            # Obtener productos en el carrito
            list_sell_products = SellProducts.objects.all()
            products_count = list_sell_products.count()

            # Obtener información de sesión
            quantity_pay = request.session.pop("quantity_pay", None)

            totals = SellService.calculate_sell_totals(list_sell_products, quantity_pay)
            # Combinar toda la información

            money_back = quantity_pay - totals
            context = {
                "totals": totals,
                "list_sell_products": list_sell_products,
                "quantity_pay": quantity_pay,
            }

            logger.info(
                f"Resumen de venta: cantidad de productos={products_count} , detalles={context.get("totals")}"
            )

            logger.info(f"Cambio devuelto: ${money_back}")
            logger.info(f"Cantidad pagada: ${quantity_pay}")

            return context

    @staticmethod
    @log_function_call(get_sell_logger())
    def clear_sell_cache():
        Limpia el cache relacionado con ventas
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
        Obtiene estadísticas de ventas para un período específico
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
            raise"""
