"""
Filters for PsysMsql API

This module contains filter classes for advanced filtering capabilities
in API endpoints using django-filter.
"""

import django_filters
from django.db.models import Q,F
from datetime import datetime, timedelta
from ..models import Products, Sell, Stock, Clients, RegistersellDetail
from ..forms import RegisterSellDetailForm


class ProductFilter(django_filters.FilterSet):
    """Filter for Products with advanced options"""

    name = django_filters.CharFilter(lookup_expr="icontains")
    price = django_filters.NumberFilter(lookup_expr="exact")
    description = django_filters.CharFilter(lookup_expr="icontains")

    # Stock-based filtering
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")
    out_of_stock = django_filters.BooleanFilter(method="filter_out_of_stock")

    class Meta:
        model = Products
        fields = [
            "name",
            "description",
            "in_stock",
            "low_stock",
            "out_of_stock",
        ]

    @staticmethod
    def filter_in_stock(queryset, value):
        """Filter products that are in stock"""
        if value:
            # Get products with stock > 0
            stock_ids = Stock.objects.filter(quantity__gt=0).values_list(
                "name_id", flat=True
            )
            return queryset.filter(id__in=stock_ids)
        return queryset

    @staticmethod
    def filter_low_stock(queryset, value):
        """Filter products with low stock (<=10)"""
        if value:
            stock_ids = Stock.objects.filter(
                quantity__gt=0, quantity__lte=10
            ).values_list("name_id", flat=True)
            return queryset.filter(id__in=stock_ids)
        return queryset

    @staticmethod
    def filter_out_of_stock(queryset, value):
        """Filter products that are out of stock"""
        if value:
            # Products with no stock record or quantity = 0
            stock_ids = Stock.objects.filter(quantity=0).values_list(
                "name_id", flat=True
            )
            no_stock_ids = queryset.exclude(
                id__in=Stock.objects.values_list("name_id", flat=True)
            ).values_list("id", flat=True)

            all_out_of_stock = list(stock_ids) + list(no_stock_ids)
            return queryset.filter(id__in=all_out_of_stock)
        return queryset


class StockFilter(django_filters.FilterSet):
    """Filter for Stock with quantity-based options"""

    product_name = django_filters.CharFilter(
        field_name="name__name", lookup_expr="icontains"
    )
    quantity_min = django_filters.NumberFilter(field_name="quantity", lookup_expr="gte")
    quantity_max = django_filters.NumberFilter(field_name="quantity", lookup_expr="lte")
    quantity_range = django_filters.RangeFilter(field_name="quantity")

    # Stock status filters
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")
    out_of_stock = django_filters.BooleanFilter(method="filter_out_of_stock")
    overstocked = django_filters.BooleanFilter(method="filter_overstocked")

    class Meta:
        model = Stock
        fields = [
            "product_name",
            "quantity_min",
            "quantity_max",
            "low_stock",
            "out_of_stock",
        ]

    @staticmethod
    def filter_low_stock(queryset, value):
        """Filter stock items below minimum threshold"""
        if value:
            return queryset.filter(quantity__lte=django_filters.filters.F("min_stock"))
        return queryset

    @staticmethod
    def filter_out_of_stock(queryset, value):
        """Filter out of stock items"""
        if value:
            return queryset.filter(quantity=0)
        return queryset

    @staticmethod
    def filter_overstocked(queryset, value):
        """Filter overstocked items (above maximum)"""
        if value:
            return queryset.filter(quantity__gte=django_filters.filters.F("max_stock"))
        return queryset


class SellFilter(django_filters.FilterSet):
    """Filter for Sales with comprehensive options"""

    # Client filtering
    client_name = django_filters.CharFilter(
        field_name="client__name", lookup_expr="icontains"
    )
    client_lastname = django_filters.CharFilter(
        field_name="client__lastname", lookup_expr="icontains"
    )
    client_email = django_filters.CharFilter(
        field_name="client__email", lookup_expr="icontains"
    )

    # User/seller filtering
    user_username = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )

    # Price filtering
    total_price_min = django_filters.NumberFilter(
        field_name="total_price", lookup_expr="gte"
    )
    total_price_max = django_filters.NumberFilter(
        field_name="total_price", lookup_expr="lte"
    )
    total_price_range = django_filters.RangeFilter(field_name="total_price")

    # Payment method
    payment_method = django_filters.ChoiceFilter(
        choices=RegisterSellDetailForm.OPTIONS_TYPE_PAY
    )

    # Date filtering
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    created_date = django_filters.DateFilter(field_name="created_at__date")

    # Convenient date filters
    today = django_filters.BooleanFilter(method="filter_today")
    this_week = django_filters.BooleanFilter(method="filter_this_week")
    this_month = django_filters.BooleanFilter(method="filter_this_month")
    last_30_days = django_filters.BooleanFilter(method="filter_last_30_days")

    class Meta:
        model = Sell
        fields = [
            "client_name",
            "client_lastname",
            "client_email",
            "user_username",
            "payment_method",
            "total_price_min",
            "total_price_max",
            "created_after",
            "created_before",
            "created_date",
        ]

    @staticmethod
    def filter_today(queryset, value):
        """Filter sales from today"""
        if value:
            today = datetime.now().date()
            return queryset.filter(created_at__date=today)
        return queryset

    @staticmethod
    def filter_this_week(queryset, value):
        """Filter sales from this week"""
        if value:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=week_start)
        return queryset

    @staticmethod
    def filter_this_month(queryset, value):
        """Filter sales from this month"""
        if value:
            today = datetime.now().date()
            month_start = today.replace(day=1)
            return queryset.filter(created_at__date__gte=month_start)
        return queryset

    @staticmethod
    def filter_last_30_days(queryset, value):
        """Filter sales from last 30 days"""
        if value:
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            return queryset.filter(created_at__date__gte=thirty_days_ago)
        return queryset


class ClientFilter(django_filters.FilterSet):
    """Filter for Clients"""

    name = django_filters.CharFilter(lookup_expr="icontains")
    lastname = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    telephone = django_filters.CharFilter(lookup_expr="icontains")
    address = django_filters.CharFilter(lookup_expr="icontains")

    # Search across multiple fields
    search = django_filters.CharFilter(method="filter_search")

    # Client activity filters
    has_purchases = django_filters.BooleanFilter(method="filter_has_purchases")
    active_last_days = django_filters.NumberFilter(method="filter_active_last_days")

    class Meta:
        model = Clients
        fields = ["name", "lastname", "email", "telephone", "address"]

    @staticmethod
    def filter_search(queryset, value):
        """Search across name, lastname, email"""
        if value:
            return queryset.filter(
                Q(name__icontains=value)
                | Q(lastname__icontains=value)
                | Q(email__icontains=value)
                | Q(telephone__icontains=value)
            )
        return queryset

    @staticmethod
    def filter_has_purchases(queryset, value):
        """Filter clients who have made purchases"""
        if value:
            client_ids = Sell.objects.values_list("client_id", flat=True).distinct()
            return queryset.filter(id__in=client_ids)
        else:
            client_ids = Sell.objects.values_list("client_id", flat=True).distinct()
            return queryset.exclude(id__in=client_ids)

    @staticmethod
    def filter_active_last_days(queryset, value):
        """Filter clients active in the last N days"""
        if value:
            cutoff_date = datetime.now().date() - timedelta(days=value)
            client_ids = (
                Sell.objects.filter(created_at__date__gte=cutoff_date)
                .values_list("client_id", flat=True)
                .distinct()
            )
            return queryset.filter(id__in=client_ids)
        return queryset


class RegisterSellDetailFilter(django_filters.FilterSet):
    """Filter of register sell details"""

    date = django_filters.DateFromToRangeFilter(field_name="date")

    id_employed = django_filters.CharFilter(lookup_expr="icontains")
    notes = django_filters.CharFilter(lookup_expr="icontains")
    detail_sell = django_filters.CharFilter(lookup_expr="icontains")

    total_sell = django_filters.NumberFilter(lookup_expr="exact")
    quantity_pay = django_filters.NumberFilter(lookup_expr="exact")
    idsell = django_filters.NumberFilter(lookup_expr="exact")

    type_pay = django_filters.ChoiceFilter(
        lookup_expr="exact", choices=RegisterSellDetailForm.OPTIONS_TYPE_PAY
    )
    state_sell = django_filters.ChoiceFilter(
        lookup_expr="exact", choices=RegisterSellDetailForm.OPTIONS_STATE_SELL
    )

    class Meta:
        model = RegistersellDetail
        fields = [
            "idsell",
            "date",
            "id_employed",
            "total_sell",
            "type_pay",
            "state_sell",
            "notes",
            "detail_sell",
            "quantity_pay",
        ]

    @staticmethod
    def filter_idsell(queryset, value):
        """Filter by sell ID"""
        if value:
            idsell_ids = RegistersellDetail.objects.filter(idsell=value).values(
                "idsell"
            )
            return queryset.filter(id__in=idsell_ids)
        return queryset
