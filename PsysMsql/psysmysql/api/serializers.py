"""
Serializers for PsysMsql API

This module contains serializers for converting model instances to/from JSON.
All serializers include proper validation, nested relationships, and field customization.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import (
    Products, 
    Sell, 
    SellProducts, 
    Stock, 
    RegistersellDetail, 
    Clients
)
from ..forms import RegisterSellDetailForm

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with safe field exposure"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users with password handling"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        """Validate password confirmation matches"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def create(self, validated_data):
        """Create user with properly hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Products model with computed fields and validation
    """
    
    # Computed fields
    stock_quantity = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            'id', 'name', 'description', 'price', 
            'stock_quantity', 'stock_status', 'formatted_price'
        ]
        read_only_fields = ['id']
    
    def get_stock_quantity(self, obj):
        """Get total stock quantity for this product"""
        try:
            stock = Stock.objects.get(id_products=obj)
            return stock.quantitystock
        except Stock.DoesNotExist:
            return 0
    
    def get_stock_status(self, obj):
        """Determine stock status based on quantity"""
        quantity = self.get_stock_quantity(obj)
        if quantity == 0:
            return "out_of_stock"
        elif quantity < 10:  # Configurable threshold
            return "low_stock"
        else:
            return "in_stock"
    
    def get_formatted_price(self, obj):
        """Format price as currency string"""
        return f"${obj.price:,.2f}"
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a cero")
        return value
    
    def validate_name(self, value):
        """Validate product name uniqueness on creation/update"""
        if self.instance:
            # Update case - exclude current instance
            if Products.objects.exclude(pk=self.instance.pk).filter(name=value).exists():
                raise serializers.ValidationError("Ya existe un producto con este nombre")
        else:
            # Create case
            if Products.objects.filter(name=value).exists():
                raise serializers.ValidationError("Ya existe un producto con este nombre")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product listings"""
    
    stock_quantity = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = ['id', 'name', 'price', 'stock_quantity', 'stock_status']
    
    def get_stock_quantity(self, obj):
        try:
            stock = Stock.objects.get(id_products=obj)
            return stock.quantitystock
        except Stock.DoesNotExist:
            return 0
    
    def get_stock_status(self, obj):
        quantity = self.get_stock_quantity(obj)
        if quantity == 0:
            return "out_of_stock"
        elif quantity < 10:
            return "low_stock"
        else:
            return "in_stock"


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model with product details"""
    
    product_name = serializers.CharField(source='name.name', read_only=True)
    product_price = serializers.DecimalField(source='name.price', max_digits=10, decimal_places=2, read_only=True)
    product_id = serializers.IntegerField(source='name.id', read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'product_id', 'product_name', 'product_price',
            'quantity', 'min_stock', 'max_stock'
        ]
        read_only_fields = ['id', 'product_id', 'product_name', 'product_price']
    
    def validate_quantity(self, value):
        """Validate quantity is not negative"""
        if value < 0:
            raise serializers.ValidationError("La cantidad no puede ser negativa")
        return value


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Clients model with validation"""
    
    total_purchases = serializers.SerializerMethodField()
    last_purchase_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Clients
        fields = [
            'id', 'name', 'lastname', 'telephone', 'email', 'address',
            'total_purchases', 'last_purchase_date'
        ]
        read_only_fields = ['id', 'total_purchases', 'last_purchase_date']
    
    def get_total_purchases(self, obj):
        """Get total amount of purchases for this client"""
        sells = Sell.objects.filter(client=obj)
        return sum(sell.total_price for sell in sells)
    
    def get_last_purchase_date(self, obj):
        """Get date of last purchase"""
        last_sell = Sell.objects.filter(client=obj).order_by('-created_at').first()
        return last_sell.created_at if last_sell else None
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if self.instance:
            if Clients.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
                raise serializers.ValidationError("Ya existe un cliente con este email")
        else:
            if Clients.objects.filter(email=value).exists():
                raise serializers.ValidationError("Ya existe un cliente con este email")
        return value


class SellProductSerializer(serializers.ModelSerializer):
    """Serializer for individual products in a sale"""
    
    product_name = serializers.CharField(source='name.name', read_only=True)
    product_price = serializers.DecimalField(source='name.price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = SellProducts
        fields = [
            'id', 'name', 'product_name', 'product_price',
            'quantity', 'subtotal'
        ]
        read_only_fields = ['id', 'product_name', 'product_price', 'subtotal']
    
    def get_subtotal(self, obj):
        """Calculate subtotal for this product in the sale"""
        return obj.quantity * obj.name.price


class SellSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Sell model with nested products and client details
    """
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    products = SellProductSerializer(source='sellproducts_set', many=True, read_only=True)
    products_count = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Sell
        fields = [
            'id', 'client', 'client_name', 'client_email',
            'user', 'user_name', 'total_price', 'payment_method',
            'created_at', 'updated_at', 'products', 'products_count', 'total_items'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'client_name', 'client_email', 'user_name']
    
    def get_products_count(self, obj):
        """Get count of different products in this sale"""
        return obj.sellproducts_set.count()
    
    def get_total_items(self, obj):
        """Get total quantity of items in this sale"""
        return sum(sp.quantity for sp in obj.sellproducts_set.all())


class SellCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new sales with products
    """
    
    client_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=RegisterSellDetailForm.OPTIONS_TYPE_PAY)
    products = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_client_id(self, value):
        """Validate client exists"""
        if not Clients.objects.filter(id=value).exists():
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def validate_products(self, value):
        """Validate products list and availability"""
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un producto")
        
        for product_data in value:
            if 'product_id' not in product_data or 'quantity' not in product_data:
                raise serializers.ValidationError("Cada producto debe tener product_id y quantity")
            
            try:
                product = Products.objects.get(id=product_data['product_id'])
                stock = Stock.objects.get(name=product)
                quantity = int(product_data['quantity'])
                
                if quantity <= 0:
                    raise serializers.ValidationError(f"Cantidad inválida para {product.name}")
                
                if stock.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {product.name}. Disponible: {stock.quantity}"
                    )
            except Products.DoesNotExist:
                raise serializers.ValidationError(f"Producto no encontrado: {product_data['product_id']}")
            except Stock.DoesNotExist:
                raise serializers.ValidationError(f"Stock no encontrado para producto: {product_data['product_id']}")
            except ValueError:
                raise serializers.ValidationError("Cantidad debe ser un número entero")
        
        return value


class RegisterSellDetailSerializer(serializers.ModelSerializer):
    """Serializer for sell detail records"""
    
    sell_id = serializers.IntegerField(source='sell.id', read_only=True)
    client_name = serializers.CharField(source='sell.client.name', read_only=True)
    total_price = serializers.DecimalField(source='sell.total_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = RegistersellDetail
        fields = [
            'id', 'sell_id', 'client_name', 'total_price',
            'details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'sell_id', 'client_name', 'total_price']


class AnalyticsSerializer(serializers.Serializer):
    """Serializer for analytics data"""
    
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = ProductListSerializer(many=True)
    sales_by_payment_method = serializers.DictField()
    monthly_sales = serializers.ListField()
    low_stock_products = ProductListSerializer(many=True)
