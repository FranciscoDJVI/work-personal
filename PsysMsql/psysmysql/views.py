import json
from django.contrib import messages
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib.auth.models import User

from .tasks import send_sell_confirmation_email
from .models import Products, Sell, SellProducts, Stock
from .services.product_service import (
    CreateProduct,
    GetAllProducts,
    SearchByAjax,
    UpdateProducts,
    DeleteProducts,
)
from .services.sell_service import (
    Search,
    RegisterSell,
    RegisterSellDetails,
    GetStatistic,
    GetIndividualtatistic,
    DeleteSellItem,
    CalculatedTotals,
)

from .services.stock_service import (
    SearchItemInStock,
    CreateStock,
    GetStcokSummaty,
    GetStockAlerts,
)
from .services.clients_service import RegisterClients, GertAllClients
from .services.factura_service import (
    GetDataClientForBill,
    create_bill_in_memory,
)
from .forms import (
    ProductForm,
    DeleteProductForm,
    SearchProduct,
    SearchEmailForm,
    SellForm,
    StockForm,
    SentSellForm,
    AssginUserToGroupForm,
    RegisterSellDetailForm,
    ClientsForm,
)
from .utils import (
    is_admin,
    is_seller,
    paginate_queryset,
)
from psysmysql import constants


def app(request):
    return render(request, "app.html")


@login_required
def dashboard(request):
    if request.user.is_authenticated:
        if is_admin(request.user):
            return render(request, "admin/admin_dashboard.html")
        elif is_seller(request.user):
            return render(request, "admin/admin_seller_dashboard.html")
    return redirect("login")


@login_required
@permission_required("psysmysql.add_products", login_url="error")
def register_product(request):
    if request.method == "POST":
        formregister = ProductForm(request.POST)
        if formregister.is_valid():
            name = formregister.cleaned_data["name"]
            price = formregister.cleaned_data["price"]
            description = formregister.cleaned_data["description"]

            try:
                CreateProduct.create_product(name, price, description)
                messages.success(request, constants.SUCCESS_PRODUCT_SAVED)

            except ValueError as e:
                messages.info(request, str(e))
            except DatabaseError as e:
                messages.error(request, f"{constants.ERROR_DATABASE_ERROR}: {e}")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

            return redirect("register_product")
    else:
        formregister = ProductForm()
    return render(request, "registerproduct.html", {"formregister": formregister})


def view_product(request):
    all_products = GetAllProducts.get_all_products().get("products")
    total_products = GetAllProducts.get_all_products().get("total")

    context = {"all_products": all_products, "total_products_save": total_products}
    return render(request, "allproducts.html", context)


@login_required
@permission_required("psysmysql.delete_products", login_url="error")
def delete_product(request):
    if request.method == "POST":
        form = DeleteProductForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]

            DeleteProducts.delete_product(name)
            messages.success(request, constants.SUCCESS_PRODUCT_DELETED)

            return redirect("delete-product")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request,
                        f"Error en el formulario de envío '{field}': {error}",
                    )
            return None
    else:
        form = DeleteProductForm()
        return render(request, "deleteproduct.html", {"form": form})


@method_decorator(
    [
        login_required(login_url="login"),
        permission_required("psysmysql.change_product", login_url="login"),
    ],
    name="dispatch",
)
class Update(View):
    template_name = "updateproduct.html"

    @staticmethod
    def get_context_data(formsearch=None, formupdate=None, productsearch=None):
        if formsearch is None:
            formsearch = SearchProduct()
        if formupdate is None:
            formupdate = ProductForm()

        return {
            "form": formsearch,
            "formupdate": formupdate,
            "productsearch": productsearch,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if "search" in request.POST:
            return self._handle_search_product(request)
        elif "update" in request.POST:
            return self._handle_update_product(request)
        else:
            messages.error(
                request,
                "Acción POST no reconocida. Asegúrate de que el botón tenga un atributo 'name'.",
            )
            context = self.get_context_data()
            return render(request, self.template_name, context)

    def _handle_search_product(self, request):
        formsearch = SearchProduct(request.POST)
        formupdate = ProductForm()
        productsearch = None

        if formsearch.is_valid():
            namesearch = formsearch.cleaned_data["name"]
            productsearch = None
            try:
                product_found = Search.get(Products, "name", namesearch)
                productsearch = product_found
                request.session["original_name"] = namesearch

                # Inicializar formupdate con la instancia del producto encontrado
                formupdate = ProductForm(instance=productsearch)

            except ObjectDoesNotExist:
                messages.error(request, "El producto no existe.")
        else:
            messages.error(
                request,
                "Por favor, corrige los errores en el formulario de búsqueda.",
            )
        context = self.get_context_data(
            formsearch=formsearch, formupdate=formupdate, productsearch=productsearch
        )

        return render(request, "updateproduct.html", context)

    def _handle_update_product(self, request):
        original_name = request.session.get("original_name")
        productsearch = None

        if not original_name:
            messages.error(request, "No hay producto con ese nombre")
            context = self.get_context_data()
            return render(request, self.template_name, context)

        formupdate = ProductForm(request.POST)
        formsearch = SearchProduct()

        if formupdate.is_valid():
            new_name = formupdate.cleaned_data["name"]
            new_price = formupdate.cleaned_data["price"]
            new_description = formupdate.cleaned_data["description"]

            original_name = request.session.get("original_name")

            UpdateProducts.update_product(
                original_name, new_name, new_price, new_description
            )
        else:
            messages.error(
                request,
                "Por favor, corrige los errores en el formulario de actualización.",
            )
            if original_name:
                try:
                    productsearch = Search.get(Products, "name", original_name)
                except ObjectDoesNotExist:
                    productsearch = None
        formupdate = ProductForm()
        context = self.get_context_data(
            formsearch=formsearch, formupdate=formupdate, productsearch=productsearch
        )
        return render(request, "updateproduct.html", context)


@login_required
def search_products_ajax(request):
    # Vista AJAX para buscar productos
    if request.method == "GET":
        query = request.GET.get("q", "").strip()
        try:
            # Usar servicio para búsqueda optimizada
            results = SearchByAjax.search_products_ajax(query, limit=10)
            return JsonResponse({"results": results})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@method_decorator(
    [
        login_required(login_url="login"),
        permission_required("psysmysql.add_sell", login_url="login"),
    ],
    name="dispatch",
)
class SellProductView(View):
    template_name = "sellproduct.html"

    @staticmethod
    def get_context_data(request):
        # Preparar formularios
        formsell = SellForm()
        sentform = SentSellForm()
        formregsitersell = RegisterSellDetailForm()

        # Buscar  clientes
        formsearch = SearchEmailForm(request.GET or None)
        search_results = []
        search_query = None

        if formsearch.is_valid():
            search_query = formsearch.cleaned_data["query"]
            if search_query:
                search_results = Search.search_clients_by_email(search_query)
        list_sell_products = Search.search_default(SellProducts)
        totals = CalculatedTotals.calculated_totals()
        change = request.session.pop("change", None)
        # Combinar todo el contexto
        context = {
            "totals": totals,
            "list_sell_products": list_sell_products,
            "formsell": formsell,
            "sentform": sentform,
            "formregsitersell": formregsitersell,
            "formsearch": formsearch,
            "search_query": search_query,
            "search_results": search_results,
            "change": change,
        }
        return context

    def get(self, request, *args, **kwargs):
        """Maneja las solicitudes GET (cuando se carga la página inicialmente)."""
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if "sell" in request.POST:
            return self._handle_sell_form(request)
        elif "add" in request.POST:
            return self._handle_add_form(request)
        elif "sent" in request.POST:
            return self._handle_sent_form(request)
        else:
            messages.error(
                request,
                "Acción POST no reconocida. Asegúrate de que el botón tenga un atributo 'name'.",
            )
            context = self.get_context_data(request)
            return render(request, self.template_name, context)

    @staticmethod
    def _handle_sell_form(request):
        formsell = SellForm(request.POST)
        if formsell.is_valid():
            totalsell = formsell.cleaned_data["totalsell"]
            idproduct = formsell.cleaned_data["id_product"]

            request.session["idproduct"] = idproduct.pk

            try:
                RegisterSell.register_sell(idproduct, totalsell)

                list_sell_products = Search.search_default(SellProducts)

                context = SellProductView.get_context_data(request)

                context["list_sell_products"] = list_sell_products
                context["totals"] = CalculatedTotals.calculated_totals()

                messages.success(request, constants.SUCCESS_SELL_CREATED)
                return render(request, "sellproduct.html", context)
            except Exception as e:
                messages.error(request, f"Error al registrar la venta: {e}")
            return redirect("sell_product")
        else:
            for field, errors in formsell.errors.items():
                for error in errors:
                    messages.error(request, f"Error en '{field}': {error}")
            return None

    @staticmethod
    def _handle_add_form(request):
        formregsitersell = RegisterSellDetailForm(request.POST)
        if formregsitersell.is_valid():
            type_pay = formregsitersell.cleaned_data["type_pay"]
            state_sell = formregsitersell.cleaned_data["state_sell"]
            notes = formregsitersell.cleaned_data["notes"]
            quantity_pay = formregsitersell.cleaned_data["quantity_pay"]

            id_employed = (
                request.user.username if request.user.is_authenticated else "anonymous"
            )

            try:
                details = Search.search_default(SellProducts)
                totals = CalculatedTotals.calculated_totals()
                detail_items: list = []
                for item in details:
                    detail_items.append(
                        {
                            "id": int(item.idsell_product),
                            "name": str(item.idproduct.name),
                            "price": float(item.priceunitaty),
                            "quantity": int(item.quantity),
                            "pricexquantity": int(item.quantity)
                            * float(item.priceunitaty),
                        }
                    )
                detail_items.append(
                    {
                        "totals": totals,
                    }
                )

                RegisterSellDetails.register_detail(
                    id_employed,
                    totals.get("total_sell"),
                    type_pay,
                    state_sell,
                    notes,
                    detail_items,
                    quantity_pay,
                )
                quantity_pay_save = float(quantity_pay)
                request.session["quantity_pay"] = quantity_pay_save
                change = GetStatistic.get_change_statistics(quantity_pay_save)
                request.session["change"] = change

                messages.success(request, constants.SUCCESS_SELL_CREATED)
            except DatabaseError as e:
                messages.error(
                    request,
                    f"Error en la base de datos al registrar el detalle de venta: {e}",
                )
            except Exception as e:
                messages.error(
                    request,
                    f"Ocurrió un error inesperado al registrar el detalle de venta: {e}",
                )

        else:
            for field, errors in formregsitersell.errors.items():
                for error in errors:
                    messages.error(
                        request,
                        f"Error en el formulario de registro de venta '{field}': {error}",
                    )
        return redirect("sell_product")

    @staticmethod
    def _handle_sent_form(request):
        sentform = SentSellForm(request.POST)

        if sentform.is_valid():
            # id of product sell
            id_product_save = request.session.get("idproduct")

            # queryset of product_sell in the sell
            sell_product_individual = Search.filter(
                SellProducts, "idproduct", id_product_save
            )

            # queryset of the list of the sellProducts registered.
            sell_products = Search.search_default(SellProducts)
            client_email_to_send = request.POST.get(
                "client_email_selected"
            )  # Obtén el correo del campo oculto

            ### EMAIL INFORMATION ###
            email_subject = constants.SUBJET_MESSAGE
            email_body = constants.BODY_EMAIL
            client_info_to_bill = GetDataClientForBill.get_data_client(
                client_email_to_send
            )

            items_factura = []

            for sell_product_info in sell_products:
                sell_product_instance = sell_product_info.idproduct
                items_factura.append(
                    {
                        "quantity": sell_product_info.quantity,
                        "name": sell_product_instance.name,
                        "price": sell_product_info.priceunitaty,
                    }
                )
            if not client_info_to_bill:
                datos_factura = {
                    "number": "",
                    "client": {
                        "name": "",
                        "direction": "",
                    },
                    "items": "",
                }
            else:
                datos_factura = {
                    "number": client_info_to_bill[0]["number_bill"],
                    "client": {
                        "name": client_info_to_bill[0]["name"],
                        "direction": client_info_to_bill[0]["direction"],
                    },
                    "items": items_factura,
                }
            pdf_buffer = create_bill_in_memory(datos_factura)
            email_message = pdf_buffer.getvalue()

            for item in sell_product_individual:
                product_id = item.idproduct_id
                quantity = item.quantity
                if not product_id or quantity is None:
                    messages.error(
                        request,
                        f"Faltan datos para enviar el producto (ID {product_id} de producto o cantidad{quantity}).",
                    )
                    return redirect("sell_product")
                try:
                    product_stock = Search.get(Stock, "id_products", product_id)
                    if product_stock.quantitystock == 0:
                        messages.error(
                            request, f"El stock del producto ID {product_id} es cero."
                        )
                    elif product_stock.quantitystock < quantity:
                        messages.warning(
                            request,
                            f"Solo quedan {product_stock.quantitystock} unidades del producto ID {product_id} en stock. No se pudo enviar {quantity} unidades.",
                        )
                    else:
                        product_stock.quantitystock -= quantity
                        product_stock.save()
                        Search.search_default(SellProducts).delete()
                        Search.search_default(Sell).delete()

                except ObjectDoesNotExist:
                    messages.error(
                        request,
                        f"Producto ID {product_id} no encontrado en stock.",
                    )
                except DatabaseError as e:
                    messages.error(
                        request,
                        f"Error en la base de datos al actualizar stock para el producto ID {product_id}: {e}",
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f"Ocurrió un error inesperado para el producto ID {product_id}: {e}",
                    )
                messages.success(request, "Proceso de envío de ventas completado.")
                if not client_email_to_send:
                    messages.warning(
                        request,
                        "No se proporcionó un correo de cliente para enviar la confirmación.",
                    )
                else:
                    send_sell_confirmation_email.delay(
                        client_email_to_send, email_subject, email_body, email_message
                    )
                    messages.info(
                        request,
                        f"Se inició el envío de correo de confirmación a {client_email_to_send}.",
                    )

                return redirect("sell_product")

        else:
            for field, errors in sentform.errors.items():
                for error in errors:
                    messages.error(
                        request,
                        f"Error en el formulario de envío '{field}': {error}",
                    )
        return redirect("sell_product")


@login_required()
def listallsellregisterview(request):
    registers = GetStatistic.get_register_sell_statistic()
    statistics = GetStatistic.quantity_total_sells()
    type_payments = GetStatistic.quantity_and_types_payment()
    total_money_sell = GetStatistic.total_money_sell()

    context = {
        "registers_sell_statistics": json.loads(registers),
        "totals_sell": json.loads(statistics),
        "totals_type_payment": json.loads(type_payments),
        "total_money_sell": json.loads(total_money_sell),
    }

    return render(request, "listallsellregister.html", context)


# all sell registers.
@login_required
def detailregisterview(request, pk):
    detail_individual_register = GetIndividualtatistic.get_individual_statistics(pk)

    details_json = detail_individual_register.values("detail_sell").first()[
        "detail_sell"
    ]
    idsell_json = detail_individual_register.values("idsell")
    details = json.loads(details_json.replace("'", '"'))

    context = {
        "detail_individual_registers": details,
        "idsell": idsell_json.values("idsell").first()["idsell"],
    }
    return render(request, "listdetailsellregister.html", context)


def delete_sell_item(request, pk):
    if request.method == "POST":
        pass
    else:
        DeleteSellItem.delete_sell(pk)
        return redirect("sell_product")
    return redirect("sell_product")


def list_product_sell(request):
    list_sell_products = SellProducts.objects.select_related(
        "idproduct", "idsell"
    ).all()

    # Paginar si hay muchos registros
    page_obj, paginator = paginate_queryset(
        list_sell_products, request, constants.SELLS_PER_PAGE
    )

    context = {
        "list_sell_products": page_obj,
        "paginator": paginator,
        "page_obj": page_obj,
    }
    return render(request, "listsellproducts.html", context)


@login_required
@permission_required("psysmysql.add_stock", login_url="error")
def register_stock(request):
    if request.method == "POST":
        stockform = StockForm(request.POST)
        if stockform.is_valid():
            id_product_instance = stockform.cleaned_data["id_products"]
            quantitystock = stockform.cleaned_data["quantitystock"]

            try:
                stock_item = SearchItemInStock.search_item(id_product_instance.pk)
                # Usar servicio para actualización de stock
                if stock_item:
                    stock_item = CreateStock.create_or_update_stock(
                        id_product_instance.pk,
                        quantitystock,
                        "add",  # Agregar al stock existente
                    )
                    messages.success(request, constants.SUCCESS_STOCK_UPDATED)
                else:
                    stock_item = CreateStock.create_or_update_stock(
                        id_product_instance.pk,
                        quantitystock,
                    )
                    messages.success(request, constants.SUCCESS_STOCK_CREATED)
                return redirect("stock_products")

            except ValidationError as e:
                messages.error(request, str(e))
            except DatabaseError as e:
                messages.error(request, f"{constants.ERROR_DATABASE_ERROR}: {e}")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")
        else:
            messages.error(request, constants.ERROR_INVALID_FORM)

        return redirect("stock_products")
    else:
        stockform = StockForm()

        # Usar servicio para obtener resumen de stock
        try:
            stock_summary = GetStcokSummaty.get_stock_summary()
            stock_alerts = GetStockAlerts.get_stock_alerts()
            register_list_stock = (
                Stock.objects.select_related("id_products")
                .all()
                .order_by("quantitystock")
            )

            context = {
                "form": stockform,
                "list_stock": register_list_stock,
                "stock_summary": stock_summary,
                "stock_alerts": stock_alerts,
            }
        except Exception as e:
            messages.error(request, f"Error cargando datos de stock: {e}")
            context = {"form": stockform, "list_stock": []}

    return render(request, "stock.html", context)


def list_stock(request):
    obj_list_stock = Search.filter(Stock, "name", "name")
    return render(request, "liststock.html", {"list_stock": obj_list_stock})


def page_404(request):
    wait_time = 5
    return render(request, "404.html", {"wait_time": wait_time})


@login_required
@permission_required("auth.change_user", raise_exception=True)
def assign_user_to_group(request):
    if request.method == "POST":
        form = AssginUserToGroupForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            selected_groups = form.cleaned_data["groups"]

            user.groups.set(selected_groups)

            messages.success(
                request,
                f"Usuario '{user.username}' actualizado en los grupos con éxito",
            )
            return redirect("assing_user")
    else:
        form = AssginUserToGroupForm()
    users_with_groups = (
        User.objects.all().order_by("username").prefetch_related("groups")
    )

    context = {
        "form": form,
        "title": "Asignar usuario a grupo",
        "users_with_groups": users_with_groups,
    }

    return render(request, "assing_user.html", context)


def register_clients(request):
    if request.method == "POST":
        formclients = ClientsForm(request.POST)
        if formclients.is_valid():
            name = formclients.cleaned_data["name"]
            email = formclients.cleaned_data["email"]
            direction = formclients.cleaned_data["direction"]
            telephone = formclients.cleaned_data["telephone"]
            nit = formclients.cleaned_data["nit"]
            country = formclients.cleaned_data["country"]
            departament = formclients.cleaned_data["departament"]
            city = formclients.cleaned_data["city"]

            RegisterClients.register_client(
                name,
                email,
                direction,
                telephone,
                nit,
                country,
                departament,
                city,
            )
            return redirect("register_client")
        else:
            return redirect("register_client")
    else:
        formclients = ClientsForm()
        return render(request, "registerclients.html", {"formclients": formclients})


def view_clients(request):
    all_client_registers = GertAllClients.get_all_clients()
    context = {"all_clients": all_client_registers}
    return render(request, "allclients.html", context)
