import json
from django.contrib import messages
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.views import View
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.http import JsonResponse
from django.contrib.auth.models import User

from .tasks import send_sell_confirmation_email
from .models import Products, Sell, SellProducts, Stock, RegistersellDetail, Clients
from .services.product_service import ProductService
from .services.sell_service import SellService
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
from .constants import (
    SUCCESS_PRODUCT_SAVED,
    SUCCESS_PRODUCT_DELETED,
    SUCCESS_SELL_CREATED,
    SUCCESS_STOCK_UPDATED,
    SUCCESS_STOCK_CREATED,
    ERROR_DATABASE_ERROR,
    ERROR_INVALID_FORM,
    CACHE_KEY_ALL_PRODUCTS,
    PRODUCTS_PER_PAGE,
    SELLS_PER_PAGE,
    CACHE_TIMEOUT_FLASH,
    PRODUCTS_PER_PAGE,
)
from .utils import (
    is_admin,
    is_seller,
    paginate_queryset,
)


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
    """Vista refactorizada para registro de productos usando ProductService"""
    if request.method == "POST":
        formregister = ProductForm(request.POST)
        if formregister.is_valid():
            name = formregister.cleaned_data["name"]
            price = formregister.cleaned_data["price"]
            description = formregister.cleaned_data["description"]

            try:
                ProductService.create_product(name, price, description)
                messages.success(request, SUCCESS_PRODUCT_SAVED)

            except ValueError as e:
                messages.info(request, str(e))
            except DatabaseError as e:
                messages.error(request, f"{ERROR_DATABASE_ERROR}: {e}")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

            return redirect("register_product")
    else:
        formregister = ProductForm()
    return render(request, "registerproduct.html", {"formregister": formregister})


def view_product(request):
    for products in ProductService.get_products_paginated(request, PRODUCTS_PER_PAGE):

        context = {"product": products}

        return render(request, "allproducts.html", context)


@login_required
@permission_required("psysmysql.delete_products", login_url="error")
def delete_product(request):
    if request.method == "POST":
        form = DeleteProductForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]

            ProductService.delete_product(name)
            messages.success(request, SUCCESS_PRODUCT_DELETED)

            return redirect("delete-product")
        else:
            for field, errors in sentform.errors.items():
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
    def get_context_data(request, formsearch=None, formupdate=None, productsearch=None):
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
        context = self.get_context_data(request)
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
            context = self.get_context_data(request)
            return render(request, self.template_name, context)

    def _handle_search_product(self, request):
        formsearch = SearchProduct(request.POST)
        formupdate = ProductForm()

        if formsearch.is_valid():
            namesearch = formsearch.cleaned_data["name"]
            product_found = ProductService.get_product_by_name(namesearch)

            if product_found:
                productsearch = product_found
                request.session["original_name"] = namesearch

                # ¡LA CLAVE ESTÁ AQUÍ! Inicializa formupdate con la instancia del producto encontrado
                formupdate = ProductForm(instance=productsearch)
            else:
                messages.error(request, "No se encontraron productos con ese nombre.")
                productsearch = None
        else:
            messages.error(
                request,
                "Por favor, corrige los errores en el formulario de búsqueda.",
            )
        context = self.get_context_data(
            request,
            formsearch=formsearch,
            formupdate=formupdate,
            productsearch=productsearch,
        )

        return render(request, "updateproduct.html", context)

    def _handle_update_product(self, request):
        original_name = request.session.get("original_name")
        productsearch = None

        if not original_name:
            messages.error(request, "No hay producto con ese nombre")
            context = self.get_context_data(request)
            return render(request, self.template_name, context)

        formupdate = ProductForm(request.POST)
        formsearch = SearchProduct()

        if formupdate.is_valid():
            new_name = formupdate.cleaned_data["name"]
            new_price = formupdate.cleaned_data["price"]
            new_description = formupdate.cleaned_data["description"]

            original_name = request.session.get("original_name")

            ProductService.update_product(
                original_name, new_name, new_price, new_description
            )
        else:
            messages.error(
                request,
                "Por favor, corrige los errores en el formulario de actualización.",
            )
            if original_name:
                try:
                    productsearch = Products.objects.get(name=original_name)
                except Products.DoesNotExist:
                    productsearch = None
        formupdate = ProductForm()
        context = self.get_context_data(
            request,
            formsearch=formsearch,
            formupdate=formupdate,
            productsearch=productsearch,
        )
        return render(request, "updateproduct.html", context)


@login_required
def search_products_ajax(request):
    """Vista AJAX refactorizada usando ProductService"""
    if request.method == "GET":
        query = request.GET.get("q", "").strip()
        try:
            # Usar servicio para búsqueda optimizada
            results = ProductService.search_products_ajax(query, limit=10)
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
        """
        Método refactorizado usando SellService para preparar contexto.
        Mucho más limpio y mantenible.
        """
        # Usar servicio para obtener todo el contexto de venta
        sell_context = SellService.get_sell_summary_for_template(request)

        # Preparar formularios
        formsell = SellForm()
        sentform = SentSellForm()
        formregsitersell = RegisterSellDetailForm()

        # Búsqueda de clientes usando servicio
        formsearch = SearchEmailForm(request.GET or None)
        search_results = []
        search_query = None

        if formsearch.is_valid():
            search_query = formsearch.cleaned_data["query"]
            if search_query:
                search_results = SellService.search_clients_by_email(search_query)

        # Combinar todo el contexto
        context = {
            **sell_context,  # Incluye todos los cálculos del servicio
            "formsell": formsell,
            "sentform": sentform,
            "formregsitersell": formregsitersell,
            "formsearch": formsearch,
            "search_query": search_query,
            "search_results": search_results,
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
        """Lógica para el formulario 'sell'."""
        formsell = SellForm(request.POST)
        if formsell.is_valid():
            totalsell = formsell.cleaned_data["totalsell"]
            idproduct = formsell.cleaned_data["id_product"]

            try:
                SellService.add_product_to_sell(idproduct.idproducts, totalsell)
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
        """Lógica para el formulario 'add'."""
        formregsitersell = RegisterSellDetailForm(request.POST)
        if formregsitersell.is_valid():
            type_pay = formregsitersell.cleaned_data["type_pay"]
            state_sell = formregsitersell.cleaned_data["state_sell"]
            notes = formregsitersell.cleaned_data["notes"]
            quantity_pay = formregsitersell.cleaned_data["quantity_pay"]

            list_sell_products = SellProducts.objects.all()

            list_items = []
            total_sale_calculated = 0

            for item in list_sell_products:
                item_total = item.quantity * item.priceunitaty
                total_sale_calculated += item_total

                list_items.append(
                    {
                        "id_product": item.idproduct.pk,
                        "name": item.idproduct.name,
                        "quantity": item.quantity,
                        "price": float(item.priceunitaty),
                        "pricexquantity": float(item_total),
                    }
                )
                list_items.append(
                    {
                        "pay": {"quantity_pay": float(quantity_pay)},
                        "money": {
                            "money_back": float(quantity_pay - total_sale_calculated)
                        },
                    }
                )

            money_back = quantity_pay - total_sale_calculated

            request.session["money_back"] = float(money_back)
            request.session["quantity_pay"] = float(quantity_pay)

            id_employed = (
                request.user.username if request.user.is_authenticated else "anonymous"
            )
            register_sell = RegistersellDetail(
                id_employed=id_employed,
                total_sell=total_sale_calculated,
                type_pay=type_pay,
                state_sell=state_sell,
                notes=notes,
                quantity_pay=quantity_pay,
                detail_sell=json.dumps(list_items),
            )
            register_sell.save()
            try:
                if register_sell:
                    messages.success(request, SUCCESS_SELL_CREATED)
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
        """Lógica para el formulario 'sent'."""
        sentform = SentSellForm(request.POST)

        if sentform.is_valid():

            productsell = Sell.objects.all()

            data = []
            for item in productsell:
                data.append(
                    {
                        "id": item.idsell,
                        "dateSell": timezone.localtime(item.datesell).isoformat(),
                        "totalsell": item.totalsell,
                        "id_product": item.id_product_id,
                    }
                )
            request.session["data_json_sell"] = data

            all_data = request.session.get("data_json_sell", [])
            client_email_to_send = request.POST.get(
                "client_email_selected"
            )  # Obtén el correo del campo oculto

            sell_product = SellProducts.objects.all()
            data_sell_products = []
            for item in sell_product:
                data_sell_products.append(
                    {
                        "id": item.idsell_product,
                        "name": str(item.idproduct),
                        "cantidad": item.quantity,
                        "precio/unitario": float(item.priceunitaty),
                        "idsell": item.idsell_id,
                    }
                )
            request.session["data_json_sell_product"] = data_sell_products

            data_sell_products = request.session.get("data_json_sell_product", [])

            email_subject = "Confirmación de Venta - Su Compra"
            email_message = str(data_sell_products)

            for item in all_data:
                product_id = item["id_product"]
                quantity = item["totalsell"]
                if not product_id or quantity is None:
                    messages.error(
                        request,
                        f"Faltan datos para enviar el producto (ID {product_id} de producto o cantidad{quantity}).",
                    )
                    return redirect("sell_product")
                try:
                    product_stock = Stock.objects.get(id_products=product_id)
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
                        SellProducts.objects.all().delete()
                        Sell.objects.all().delete()
                except Stock.DoesNotExist:
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
            if client_email_to_send:
                send_sell_confirmation_email.delay(
                    client_email_to_send, email_subject, email_message
                )
                messages.info(
                    request,
                    f"Se inició el envío de correo de confirmación a {client_email_to_send}.",
                )
            else:
                messages.warning(
                    request,
                    "No se proporcionó un correo de cliente para enviar la confirmación.",
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
    listallregister = RegistersellDetail.objects.all()
    statistics = SellService.get_sales_statistics()

    # List of the register sell and statistics about all sells.
    context = {
        "list": listallregister,
        "statistics": statistics,
    }

    print(statistics)
    return render(request, "listallsellregister.html", context)


@login_required()
# función para mostrar los datos de los registros de ventas.
def detailregisterview(request, pk):
    register_sell_instance = get_object_or_404(RegistersellDetail, idsell=pk)

    detail_products_list = []
    # Verificamos que register_sell_instance no este vacio y que tambien sea una instancia o un objecto de python.
    if register_sell_instance.detail_sell and isinstance(
        register_sell_instance.detail_sell, str
    ):
        try:
            # Decodificación de los datos de tipo Json.
            detail_products_list = json.loads(register_sell_instance.detail_sell)
        except json.JSONDecodeError:
            print(f"Error: detail_sell para idsell={pk} no es JSON válido.")

    context = {
        "register_sell_instance": register_sell_instance,
        "detail": detail_products_list,
    }
    return render(request, "listdetailsellregister.html", context)


def delete_sell_item(request, pk):
    if request.method == "POST":
        pass
    else:
        SellService.remove_sell_item(pk)
        return redirect("sell_product")
    return render(request, "deletesellitem.html", {"item", sell_detail_item})


def list_product_sell(request):
    list_sell_products = SellProducts.objects.select_related(
        "idproduct", "idsell"
    ).all()

    # Paginar si hay muchos registros
    page_obj, paginator = paginate_queryset(list_sell_products, request, SELLS_PER_PAGE)

    context = {
        "list_sell_products": page_obj,
        "paginator": paginator,
        "page_obj": page_obj,
    }
    return render(request, "listsellproducts.html", context)


@login_required
@permission_required("psysmysql.add_stock", login_url="error")
def register_stock(request):
    """Vista refactorizada para gestión de stock usando StockService"""
    from .services.stock_service import StockService

    if request.method == "POST":
        stockform = StockForm(request.POST)
        if stockform.is_valid():
            id_product_instance = stockform.cleaned_data["id_products"]
            quantitystock = stockform.cleaned_data["quantitystock"]

            try:
                stock_item = StockService.search_item_in_stock(id_product_instance.pk)
                # Usar servicio para actualización de stock
                if stock_item:
                    stock_item = StockService.update_stock(
                        id_product_instance.pk,
                        quantitystock,
                        "add",  # Agregar al stock existente
                    )
                    messages.success(request, SUCCESS_STOCK_UPDATED)
                else:
                    stock_item = StockService.update_stock(
                        id_product_instance.pk,
                        quantitystock,
                    )
                    messages.success(request, SUCCESS_STOCK_CREATED)
                return redirect("stock_products")

            except ValidationError as e:
                messages.error(request, str(e))
            except DatabaseError as e:
                messages.error(request, f"{ERROR_DATABASE_ERROR}: {e}")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")
        else:
            messages.error(request, ERROR_INVALID_FORM)

        return redirect("stock_products")
    else:
        stockform = StockForm()

        # Usar servicio para obtener resumen de stock
        try:
            stock_summary = StockService.get_stock_summary()
            stock_alerts = StockService.get_stock_alerts()
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
    obj_list_stock = Stock.objects.filter("name")
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

            new_client = Clients(
                name=name,
                email=email,
                direction=direction,
                nit=nit,
                telephone=telephone,
                country=country,
                departament=departament,
                city=city,
            )

            new_client.save()

            return redirect("register_client")
        else:
            return redirect("register_client")
    else:
        formclients = ClientsForm()
        return render(request, "registerclients.html", {"formclients": formclients})
