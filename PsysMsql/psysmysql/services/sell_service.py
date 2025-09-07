from datetime import datetime
import json
from django.db.models import Count, Sum
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from psysmysql import  models
from django.core.cache import cache
from ..logging_config import (
    get_sell_logger,
    log_execution_time,
    LogOperation,
)
import psysmysql.constants as const

from ..services.search_orm import Search


class RegisterSell:

    @staticmethod
    @log_execution_time(get_sell_logger())
    def register_sell(id_product, total_sell):
        logger = get_sell_logger()

        try:
            with LogOperation(
                f"Agregando producto {id_product} con cantidad {total_sell}", logger
            ):
                product = get_object_or_404(models.Products, pk=id_product.idproducts)

                register_sell = models.Sell(totalsell=total_sell, id_product=id_product)
                register_sell.save()
                if not register_sell.idsell:
                    logger.info(f"Fallo en la creacion del producto {product.name}")
                else:
                    logger.info(
                        f"Nuevo producto {product.name} agregado al carrito: {total_sell} unidades"
                    )
        except ObjectDoesNotExist:
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

                register_sell_detail = models.RegistersellDetail(
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
        all_register_sells = Search.search_default(models.RegistersellDetail)
        registers: list = []
        for register in all_register_sells:
            registers.append(
                {
                    "id_register": int(register.idsell),
                    "date": str(
                        datetime.astimezone(register.date).strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    "id_employed": str(register.id_employed),
                    "total_sell": float(register.total_sell),
                    "type_pay": str(register.type_pay),
                    "state_sell": str(register.state_sell),
                    "notes": str(register.notes),
                    "detail_sell": str(register.detail_sell),
                }
            )
        return json.dumps(registers)

    @staticmethod
    def get_change_statistics(quantity_pay: float):

        total_sell = GetStatistic.get_register_sell_statistic()
        total_sell_dict = json.loads(total_sell)
        print(total_sell_dict[0]["total_sell"])
        change_dict: dict = {}
        try:
            if not quantity_pay:
                change_dict = {}
                return change_dict
            elif quantity_pay < total_sell_dict[0]["total_sell"]:
                raise ValidationError("El pago es insuficiente")
            else:
                change = float(quantity_pay) - total_sell_dict[0]["total_sell"]
                change_dict = {"quantity_pay": float(quantity_pay), "change": change}
                return change_dict
        except Exception as e:
            raise ValidationError(f"Error calculando cambio: {str(e)}")

    @staticmethod
    def quantity_total_sells():
        all_register_sells_count = Search.search_default(models.RegistersellDetail).count()
        return json.dumps(all_register_sells_count)

    @staticmethod
    def quantity_and_types_payment():
        all_type_payment = Search.values(models.RegistersellDetail, "type_pay").annotate(
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
        total_money_sells = models.RegistersellDetail.objects.aggregate(
            total_sum=Sum("total_sell")
        )
        if not total_money_sells:
            total_money = {}
        else:
            total_money = {"total": float(total_money_sells.get("total_sum"))}
        return json.dumps(total_money)


class GetIndividualtatistic:
    @staticmethod
    def get_individual_statistics(pk):
        return Search.filter(models.RegistersellDetail, "idsell", pk)


class GetSellProductQueryset:

    @staticmethod
    def get_sell_product_queryset(pk):
        detail_sell_product_queryset = Search.filter(models.SellProducts, "idproduct", pk)

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
        item = Search.filter(models.SellProducts, "idsell_product", pk)
        item.delete()


class CalculatedTotals:
    iva_rate = const.IVA_RATE  # Ejemplo: 19% de IVA

    @staticmethod
    def calculated_totals():
        total_quantity = 0
        subtotal = 0.0

        sell_products = Search.search_default(models.SellProducts)

        for product in sell_products:
            total_quantity += product.quantity
            subtotal += product.quantity * float(product.priceunitaty)

        iva_amount = subtotal * CalculatedTotals.iva_rate
        total_sell = subtotal

        totals = {
            "quantity": total_quantity,
            "subtotal": subtotal - iva_amount,
            "iva": iva_amount,
            "total_sell": total_sell,
        }
        return totals
