from django.core.cache import cache
from django.db.models import Q
from ..models import Products, Stock
from ..constants import (
    CACHE_KEY_ALL_PRODUCTS,
    CACHE_TIMEOUT_FLASH,
)
from ..utils import clear_model_cache
from ..logging_config import get_product_logger, log_execution_time, LogOperation


class ProductService:
    @staticmethod
    def get_all_products_save():

        cache_key = f"{CACHE_KEY_ALL_PRODUCTS}"
        all_products = cache.get(cache_key)
        total_products_save = None

        if all_products is None:

            all_products = Products.objects.all().select_related().order_by("name")
            total_products_save = all_products.count()
            cache.set(cache_key, all_products, CACHE_TIMEOUT_FLASH)

        return {
            "products": all_products,
            "total": total_products_save,
        }

    @staticmethod
    def search_products_ajax(query, limit=10):
        """
        Buscar productos por medio de AJAX
        """
        if not query or len(query) < 2:
            return []

        # Optimizar: usar only() para traer solo campos necesarios
        products = Products.objects.filter(Q(name__icontains=query)).only(
            "idproducts", "name", "price", "description"
        )[:limit]

        return [
            {
                "id": product.idproducts,
                "name": product.name,
                "price": float(product.price),
                "description": product.description,
            }
            for product in products
        ]

    @staticmethod
    @log_execution_time(get_product_logger())
    def create_product(name, price, description):
        logger = get_product_logger()

        with LogOperation(f"Creando producto: {name}", logger):
            # Verificar si existe
            if Products.objects.filter(name=name).exists():
                logger.warning(f"Intento de crear producto duplicado: {name}")
                raise ValueError("El producto ya existe")

            # Crear producto
            product = Products.objects.create(
                name=name, price=price, description=description
            )

            logger.info(
                f"Producto creado exitosamente: {name} (ID: {product.idproducts})"
            )

            # Limpiar cache
            clear_model_cache(CACHE_KEY_ALL_PRODUCTS)
            logger.debug("Cache de productos limpiado")

            return product

    @staticmethod
    def update_product(original_name, new_name, new_price, new_description):

        try:
            product = ProductService.get_product_by_name(original_name)
            product.name = new_name
            product.price = new_price
            product.description = new_description
            product.save()

            # Limpiar cache
            clear_model_cache(CACHE_KEY_ALL_PRODUCTS)

            return product
        except Products.DoesNotExist:
            raise ValueError("Producto no encontrado")

    @staticmethod
    def delete_product(name: str) -> bool:
        try:
            # Reutilizacion del metodo de buscar productos por el nombre.
            delete_product = ProductService.get_product_by_name(name)
            delete_product.delete()

            # Limpiar cache
            clear_model_cache(CACHE_KEY_ALL_PRODUCTS)

            return True
        except Products.DoesNotExist:
            raise ValueError("Producto no encontrado")

    @staticmethod
    def get_product_by_name(name):

        try:
            return Products.objects.get(name=name)
        except Products.DoesNotExist:
            return None

    @staticmethod
    def get_product_stock_info(product_id):
        try:
            stock = Stock.objects.select_related("id_products").get(
                id_products_id=product_id
            )
            return {
                "product": stock.id_products,
                "quantity": stock.quantitystock,
                "available": stock.quantitystock > 0,
            }
        except Stock.DoesNotExist:
            return None

    @staticmethod
    def update_or_create_stock(product_id, quantity):
        stock, created = Stock.objects.update_or_create(
            id_products_id=product_id, defaults={"quantitystock": quantity}
        )
        return stock, created
