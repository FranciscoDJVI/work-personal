from django import forms
from django.contrib.auth.models import User, Group

# MODELS
from . import models


class ProductForm(forms.ModelForm):
    class Meta:
        model = models.Products
        labels = {
            "name": "",
            "price": "",
            "description": "",
        }
        field = ["name", "price", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Producto",
                    "class": "bg-gray-200 p-2 text-black",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Precio",
                    "class": "bg-gray-200 p-2 text-black",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Desc...",
                    "class": "bg-gray-200 p-2 text-black",
                }
            ),
        }

        exclude = ["idproduct"]


class DeleteProductForm(forms.ModelForm):
    class Meta:
        model = models.Products
        field = ["name"]
        labels = {"name": ""}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Buscar producto",
                    "class": "bg-gray-200 text-black p-2",
                }
            )
        }

        exclude = ["idproduct", "price", "description"]


class SearchProduct(forms.ModelForm):
    class Meta:
        model = models.Products
        fields = ["name"]
        labels = {"name": ""}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "buscar",
                    "class": "bg-gray-200 text-black p-2",
                }
            )
        }

        exclude = ["idproduct", "price", "description"]


class SellForm(forms.ModelForm):
    # Campo personalizado para la búsqueda de productos
    product_search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar producto...",
                "class": "bg-white p-2 m-5 w-40 text-black font-medium",
                "id": "product-search-input",
                "autocomplete": "off",
            }
        ),
        label="",
    )

    # Campo oculto para almacenar el ID del producto seleccionado
    id_product = forms.ModelChoiceField(
        queryset=models.Products.objects.all(),
        widget=forms.HiddenInput(attrs={"id": "selected-product-id"}),
        required=True,
    )

    class Meta:
        model = models.Sell
        fields = ["id_product", "totalsell"]
        labels = {
            "totalsell": "",
            "id_product": "",
        }
        widgets = {
            "totalsell": forms.NumberInput(
                attrs={
                    "placeholder": "cantidad",
                    "class": "bg-white p-2 m-5 w-40 text-black font-medium",
                }
            ),
        }


class StockForm(forms.ModelForm):
    class Meta:
        model = models.Stock
        fields = ["id_products", "quantitystock"]
        labels = {
            "id_products": "",
            "quantitystock": "",
        }
        widgets = {
            "id_products": forms.Select(
                attrs={
                    "placeholder": "id_product",
                    "class": "bg-gray-200 text-black p-2 m-5",
                }
            ),
            "quantitystock": forms.NumberInput(
                attrs={
                    "placeholder": "cantidad",
                    "class": "bg-gray-200 text-black p-2 m-5",
                }
            ),
        }


class SentSellForm(forms.Form):
    action_type = forms.CharField(widget=forms.HiddenInput(), initial="sent_sell")
    pass


class AssginUserToGroupForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("username"),
        label="seleccionar usuario",
        widget=forms.Select(attrs={"class": "border border-gray-400 text-xm p-2 m-4"}),
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by("name"),
        label="",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "p-2"}),
    )


class RegisterSellDetailForm(forms.ModelForm):
    OPTIONS_TYPE_PAY = [
        (
            "Efectivo",
            "Efectivo",
        ),
        ("transferencia", "Transferencia"),
        ("tarjeta credito", "Tarjeta crédito"),
        ("tarjeta debito", "Tarjeta débito"),
    ]
    type_pay = forms.ChoiceField(
        choices=OPTIONS_TYPE_PAY,
        label="",
        initial="Efectivo",
        widget=forms.Select(attrs={"class": "bg-gray-200 p-2 text-black font-medium"}),
    )
    OPTIONS_STATE_SELL = [
        (
            "Pagado",
            "Pagado",
        ),
        ("En espera", "En espera"),
    ]
    state_sell = forms.ChoiceField(
        choices=OPTIONS_STATE_SELL,
        label="",
        initial="Pagado",
        widget=forms.Select(attrs={"class": "bg-gray-200 p-2 text-black font-medium"}),
    )

    class Meta:
        model = models.RegistersellDetail
        fields = ["type_pay", "state_sell", "notes", "quantity_pay"]
        labels = {
            "notes": "",
            "quantity_pay": "",
        }
        widgets = {
            "notes": forms.TextInput(
                attrs={
                    "placeholder": "coment.",
                    "class": "bg-gray-200 p-2 text-black font-medium",
                }
            ),
            "quantity_pay": forms.TextInput(
                attrs={
                    "placeholder": "cant. pago",
                    "class": "bg-gray-200 p-2 text-black font-medium",
                }
            ),
        }


class ClientsForm(forms.ModelForm):
    class Meta:
        model = models.Clients
        fields = "__all__"
        labels = {
            "name": "",
            "email": "",
            "direction": "",
            "telephone": "",
            "nit": "",
            "country": "",
            "departament": "",
            "city": "",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Nombre/Razón social",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "direction": forms.TextInput(
                attrs={
                    "placeholder": "Dirección",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "telephone": forms.TextInput(
                attrs={
                    "placeholder": "Telefono",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "nit": forms.TextInput(
                attrs={
                    "placeholder": "nit",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "placeholder": "País",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "departament": forms.TextInput(
                attrs={
                    "placeholder": "Departamento",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "Ciudad",
                    "class": "bg-gray-200 border-cyan-950  text-black p-2 m-5",
                }
            ),
        }


class SearchEmailForm(forms.Form):
    query = forms.CharField(
        label="Buscar",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "bg-gray-200 text-black font-medium p-1"}
        ),
    )
