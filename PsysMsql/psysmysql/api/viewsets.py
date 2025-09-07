"""
ViewSets for PsysMsql API

This module contains all ViewSets that define the API endpoints.
Each ViewSet provides CRUD operations and custom actions for specific models.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from django.db import transaction
from datetime import datetime, timedelta

from ..models import Products, Sell, SellProducts, Stock, Clients, RegistersellDetail
from ..services.product_service import CreateProduct, UpdateProducts, DeleteProducts
from ..services.sell_service import  RegisterSell
from .serializers import (
    ProductSerializer,
    ProductListSerializer,
    StockSerializer,
    ClientSerializer,
    SellSerializer,
    SellCreateSerializer,
    UserSerializer,
    UserCreateSerializer,
    RegisterSellDetailSerializer,
)
from .permissions import IsOwnerOrAdmin
from .filters import ProductFilter, SellFilter, StockFilter, RegisterSellDetailFilter


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users

    Provides CRUD operations for users with proper permissions
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "date_joined"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products

    Provides CRUD operations and additional actions for product management
    """

    queryset = Products.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "id"]
    ordering = ["name"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        """Create product using ProductService"""
        try:
            name = serializer.validated_data["name"]
            price = serializer.validated_data["price"]
            description = serializer.validated_data.get("description", "")

            product = CreateProduct.create_product(name, price, description)
            serializer.instance = product
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        """Update product using ProductService"""
        try:
            UpdateProducts.update_product(
                serializer.instance, **serializer.validated_data
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        """Delete product using ProductService"""
        try:
            DeleteProducts.delete_product(instance)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Get products with low stock"""
        threshold = request.query_params.get("threshold", 10)
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 10

        # Get products where stock is below threshold
        low_stock_products = []
        for product in self.get_queryset():
            try:
                stock = Stock.objects.get(name=product)
                if stock.quantitystock <= threshold:
                    low_stock_products.append(product)
            except Stock.DoesNotExist:
                low_stock_products.append(product)  # No stock record = low stock

        serializer = ProductListSerializer(low_stock_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def out_of_stock(self):
        """Get products that are out of stock"""
        out_of_stock_products = []
        for product in self.get_queryset():
            try:
                stock = Stock.objects.get(name=product)
                if stock.quantitystock == 0:
                    out_of_stock_products.append(product)
            except Stock.DoesNotExist:
                out_of_stock_products.append(product)

        serializer = ProductListSerializer(out_of_stock_products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stock_history(self):
        """Get stock movement history for a product"""
        product = self.get_object()
        # This would require a StockMovement model to track history
        # For now, return basic stock info
        try:
            stock = Stock.objects.get(name=product)
            data = {
                "current_stock": stock.quantitystock,
                "min_stock": stock.min_stock,
                "max_stock": stock.max_stock,
                # Add movement history when StockMovement model is implemented
                "movements": [],
            }
            return Response(data)
        except Stock.DoesNotExist:
            return Response(
                {"current_stock": 0, "min_stock": 0, "max_stock": 0, "movements": []}
            )


class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock

    Provides CRUD operations for stock management
    """

    queryset = Stock.objects.all().select_related("id_products")
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = StockFilter
    search_fields = ["id_products__name"]
    ordering_fields = ["quantity", "id_products__name"]
    ordering = ["id_products__name"]

    @action(detail=False, methods=["get"])
    def summary(self):
        """Get stock summary statistics"""
        queryset = self.get_queryset()

        total_products = queryset.count()
        total_stock_value = sum(stock.quantity * stock.name.price for stock in queryset)
        low_stock_count = sum(
            1 for stock in queryset if stock.quantity <= stock.min_stock
        )
        out_of_stock_count = queryset.filter(quantity=0).count()

        data = {
            "total_products": total_products,
            "total_stock_value": total_stock_value,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "stock_levels": {
                "in_stock": total_products - out_of_stock_count,
                "low_stock": low_stock_count,
                "out_of_stock": out_of_stock_count,
            },
        }

        return Response(data)

    @action(detail=True, methods=["post"])
    def adjust(self, request):
        """Adjust stock quantity with reason"""
        stock = self.get_object()
        adjustment = request.data.get("adjustment", 0)

        try:
            adjustment = int(adjustment)
            new_quantity = stock.quantity + adjustment

            if new_quantity < 0:
                return Response(
                    {"error": "La cantidad resultante no puede ser negativa"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stock.quantity = new_quantity
            stock.save()

            # Log the adjustment (would require StockMovement model)
            serializer = self.get_serializer(stock)
            return Response(serializer.data)

        except ValueError:
            return Response(
                {"error": "El ajuste debe ser un número entero"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clients

    Provides CRUD operations and customer analytics
    """

    queryset = Clients.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "id",
        "name",
        "email",
        "direction",
        "telephone",
        "nit",
        "country",
        "departament",
        "city",
    ]
    ordering_fields = [
        "id",
        "name",
        "direction",
        "telephone",
        "nit",
        "country",
        "departament",
        "city",
    ]
    ordering = ["name"]

    @action(detail=True, methods=["get"])
    def purchase_history(self):
        """Get purchase history for a client"""
        client = self.get_object()
        sells = Sell.objects.filter(client=client).order_by("-created_at")

        serializer = SellSerializer(sells, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self):
        """Get statistics for a client"""
        client = self.get_object()
        sells = Sell.objects.filter(client=client)

        total_purchases = sells.aggregate(
            total_amount=Sum("total_price"),
            total_orders=Count("id"),
            avg_order=Avg("total_price"),
        )

        # Most purchased products
        top_products = (
            SellProducts.objects.filter(sell__client=client)
            .values("name__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:5]
        )

        data = {
            "total_amount": total_purchases["total_amount"] or 0,
            "total_orders": total_purchases["total_orders"] or 0,
            "average_order_value": total_purchases["avg_order"] or 0,
            "top_products": list(top_products),
            "first_purchase": (
                sells.order_by("created_at").first().created_at
                if sells.exists()
                else None
            ),
            "last_purchase": (
                sells.order_by("-created_at").first().created_at
                if sells.exists()
                else None
            ),
        }

        return Response(data)


class SellViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales

    Provides CRUD operations and sales analytics
    """

    queryset = Sell.objects.all()
    serializer_class = SellSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SellFilter
    search_fields = ["idsell", "datesell", "totalsell", "id_product"]
    ordering_fields = ["datesell", "total_price"]
    ordering = ["datesell"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return SellCreateSerializer
        return SellSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new sale using SellService"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Use SellService to create the sale
            client_id = serializer.validated_data["client_id"]
            payment_method = serializer.validated_data["payment_method"]
            products_data = serializer.validated_data["products"]

            sell = RegisterSell.register_sell(
                client_id=client_id,
                user=request.user,
                payment_method=payment_method,
                products=products_data,
            )

            # Return the created sale
            response_serializer = SellSerializer(sell)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request):
        """Cancel a sale and restore stock"""
        sell = self.get_object()
        reason = request.data.get("reason", "Cancelación solicitada")

        try:
            SellService.cancel_sale(sell, reason)
            return Response({"message": "Venta cancelada exitosamente"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        """Get sales analytics"""
        # Date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        # Override with query parameters if provided
        if "start_date" in request.query_params:
            try:
                start_date = datetime.strptime(
                    request.query_params["start_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        if "end_date" in request.query_params:
            try:
                end_date = datetime.strptime(
                    request.query_params["end_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        # Filter sales by date range
        sells_queryset = self.get_queryset().filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )

        # Basic metrics
        metrics = sells_queryset.aggregate(
            total_sales=Sum("total_price"),
            total_orders=Count("id"),
            avg_order_value=Avg("total_price"),
        )

        # Sales by payment method
        payment_methods = sells_queryset.values("payment_method").annotate(
            total=Sum("total_price"), count=Count("id")
        )

        # Top products
        top_products_data = (
            SellProducts.objects.filter(sell__in=sells_queryset)
            .values("name")
            .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("quantity"))
            .order_by("-total_quantity")[:10]
        )

        top_products = Products.objects.filter(
            id__in=[item["name"] for item in top_products_data]
        )

        # Low stock products
        low_stock_products = []
        for product in Products.objects.all()[:10]:  # Limit for performance
            try:
                stock = Stock.objects.get(name=product)
                if stock.quantitystock <= 10:  # Configurable threshold
                    low_stock_products.append(product)
            except Stock.DoesNotExist:
                low_stock_products.append(product)

        # Monthly sales (simplified)
        monthly_sales = []
        current_date = start_date
        while current_date <= end_date:
            month_sales = sells_queryset.filter(
                created_at__year=current_date.year, created_at__month=current_date.month
            ).aggregate(total=Sum("total_price"))

            monthly_sales.append(
                {
                    "month": current_date.strftime("%Y-%m"),
                    "total": month_sales["total"] or 0,
                }
            )

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        data = {
            "total_sales": metrics["total_sales"] or 0,
            "total_orders": metrics["total_orders"] or 0,
            "average_order_value": metrics["avg_order_value"] or 0,
            "top_products": ProductListSerializer(top_products, many=True).data,
            "sales_by_payment_method": {
                item["payment_method"]: item["total"] for item in payment_methods
            },
            "monthly_sales": monthly_sales,
            "low_stock_products": ProductListSerializer(
                low_stock_products, many=True
            ).data,
        }

        return Response(data)

    @action(detail=False, methods=["get"])
    def daily_summary(self):
        """Get daily sales summary"""
        today = datetime.now().date()

        # Get today's sales
        today_sales = self.get_queryset().filter(created_at__date=today)

        summary = today_sales.aggregate(
            total_sales=Sum("total_price"),
            total_orders=Count("id"),
            avg_order_value=Avg("total_price"),
        )

        # Sales by hour
        hourly_sales = []
        for hour in range(24):
            hour_sales = today_sales.filter(created_at__hour=hour).aggregate(
                total=Sum("total_price")
            )

            hourly_sales.append({"hour": hour, "total": hour_sales["total"] or 0})

        data = {
            "date": today,
            "total_sales": summary["total_sales"] or 0,
            "total_orders": summary["total_orders"] or 0,
            "average_order_value": summary["avg_order_value"] or 0,
            "hourly_sales": hourly_sales,
        }

        return Response(data)


# viewset RegisterSellDetailViewSet


class RegisterSellDetailViewset(viewsets.ModelViewSet):
    """ViewSet for managing register sell details"""

    queryset = RegistersellDetail.objects.all().order_by("-date")
    serializer_class = RegisterSellDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = RegisterSellDetailFilter
    search_fields = ["id_employed", "type_pay", "state_sell", "notes", "detail_sell"]
    ordering_fields = ["date", "total_sell", "id_employed"]
    ordering = ["-date"]

    @staticmethod
    def get_list_detail():
        """Get list of register sell details"""
        try:
            list_detail = RegistersellDetail.objects.all().order_by("-date")
            return list_detail
        except RegistersellDetail.DoesNotExist:
            return 0
