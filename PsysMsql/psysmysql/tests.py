from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from decimal import Decimal
from .models import Products, Stock, SellProducts, Clients
from .services.product_service import ProductService
from .services.sell_service import SellService


class ProductModelTestCase(TestCase):
    """Tests para el modelo Products"""
    
    def setUp(self):
        self.product = Products.objects.create(
            name="Producto Test",
            price=Decimal('100.00'),
            description="Descripción de prueba"
        )
    
    def test_product_creation(self):
        """Test creación de producto"""
        self.assertEqual(self.product.name, "Producto Test")
        self.assertEqual(self.product.price, Decimal('100.00'))
        self.assertEqual(str(self.product), "Producto Test")
    
    def test_product_unique_constraint(self):
        """Test que no se puedan crear productos duplicados"""
        with self.assertRaises(Exception):
            Products.objects.create(
                name="Producto Test",  # Mismo nombre
                price=Decimal('200.00'),
                description="Otra descripción"
            )


class ProductServiceTestCase(TestCase):
    """Tests para ProductService"""
    
    def setUp(self):
        self.product = Products.objects.create(
            name="Producto Service Test",
            price=Decimal('150.00'),
            description="Test service"
        )
    
    def test_search_products_ajax(self):
        """Test búsqueda AJAX de productos"""
        results = ProductService.search_products_ajax("Service")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Producto Service Test")
        self.assertEqual(results[0]['price'], 150.0)
    
    def test_search_products_ajax_empty_query(self):
        """Test búsqueda con query vacío"""
        results = ProductService.search_products_ajax("")
        self.assertEqual(len(results), 0)
    
    def test_create_product_success(self):
        """Test creación exitosa de producto"""
        product = ProductService.create_product(
            "Nuevo Producto",
            Decimal('200.00'),
            "Nueva descripción"
        )
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Nuevo Producto")
    
    def test_create_product_duplicate(self):
        """Test creación de producto duplicado"""
        with self.assertRaises(ValueError):
            ProductService.create_product(
                "Producto Service Test",  # Ya existe
                Decimal('300.00'),
                "Descripción duplicada"
            )


class SellServiceTestCase(TestCase):
    """Tests para SellService"""
    
    def setUp(self):
        self.product1 = Products.objects.create(
            name="Producto 1",
            price=Decimal('100.00'),
            description="Test 1"
        )
        self.product2 = Products.objects.create(
            name="Producto 2",
            price=Decimal('200.00'),
            description="Test 2"
        )
        
        # Crear items de venta
        self.sell_item1 = SellProducts.objects.create(
            idproduct=self.product1,
            quantity=2,
            priceunitaty=Decimal('100.00')
        )
        self.sell_item2 = SellProducts.objects.create(
            idproduct=self.product2,
            quantity=1,
            priceunitaty=Decimal('200.00')
        )
    
    def test_calculate_sell_totals(self):
        """Test cálculo de totales de venta"""
        queryset = SellProducts.objects.all()
        totals = SellService.calculate_sell_totals(queryset)
        
        # Total: (2 * 100) + (1 * 200) = 400
        expected_subtotal = 400.0
        expected_iva = 400.0 * 0.19  # 76.0
        
        self.assertEqual(totals['quantity'], 3)
        self.assertEqual(totals['subtotal'], expected_subtotal)
        self.assertEqual(totals['iva_calculated'], expected_iva)
        self.assertEqual(len(totals['list_items']), 2)
    
    def test_calculate_change(self):
        """Test cálculo de cambio"""
        change = SellService.calculate_change(100.0, 150.0)
        self.assertEqual(change, 50.0)
    
    def test_calculate_change_insufficient_payment(self):
        """Test cambio con pago insuficiente"""
        with self.assertRaises(ValueError):
            SellService.calculate_change(100.0, 80.0)
    
    def test_validate_sell_data_success(self):
        """Test validación exitosa de datos de venta"""
        errors = SellService.validate_sell_data(self.product1.pk, 5)
        self.assertEqual(len(errors), 0)
    
    def test_validate_sell_data_no_product(self):
        """Test validación sin producto"""
        errors = SellService.validate_sell_data(None, 5)
        self.assertIn("Debe seleccionar un producto", errors)
    
    def test_validate_sell_data_invalid_quantity(self):
        """Test validación con cantidad inválida"""
        errors = SellService.validate_sell_data(self.product1.pk, 0)
        self.assertIn("La cantidad debe ser mayor a 0", errors)


class ClientModelTestCase(TestCase):
    """Tests para el modelo Clients"""
    
    def test_client_creation(self):
        """Test creación de cliente"""
        client = Clients.objects.create(
            name="Cliente Test",
            email="test@test.com",
            direction="Dirección test",
            nit="123456789",
            country="Colombia",
            departament="Bogotá",
            city="Bogotá"
        )
        self.assertEqual(client.name, "Cliente Test")
        self.assertEqual(str(client), "Cliente Test")


class ViewsTestCase(TestCase):
    """Tests básicos para vistas principales"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        
        # Crear grupos
        self.admin_group = Group.objects.create(name='Administrador')
        self.seller_group = Group.objects.create(name='Vendedor')
    
    def test_app_view_loads(self):
        """Test que la vista principal carga correctamente"""
        response = self.client.get(reverse('app'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_requires_login(self):
        """Test que el dashboard requiere login"""
        response = self.client.get(reverse('main'))
        self.assertRedirects(response, '/accounts/login/?next=/main/')
    
    def test_dashboard_with_admin_user(self):
        """Test dashboard con usuario administrador"""
        self.user.groups.add(self.admin_group)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)


class IntegrationTestCase(TestCase):
    """Tests de integración"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_group = Group.objects.create(name='Administrador')
        self.user.groups.add(self.admin_group)
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_product_crud_flow(self):
        """Test flujo completo de CRUD de productos"""
        # Crear producto usando servicio
        product = ProductService.create_product(
            "Producto Integración",
            Decimal('250.00'),
            "Test de integración"
        )
        
        # Verificar que se creó
        self.assertIsNotNone(product)
        
        # Buscar producto
        found_product = ProductService.get_product_by_name("Producto Integración")
        self.assertIsNotNone(found_product)
        
        # Actualizar producto
        updated = ProductService.update_product(
            "Producto Integración",
            "Producto Actualizado",
            Decimal('300.00'),
            "Descripción actualizada"
        )
        self.assertEqual(updated.name, "Producto Actualizado")
        
        # Eliminar producto
        deleted = ProductService.delete_product("Producto Actualizado")
        self.assertTrue(deleted)
