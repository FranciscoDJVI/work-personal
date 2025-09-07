from django.core.cache import cache
from psysmysql.models import Products
from django.db.models import Q, ObjectDoesNotExist
from ..constants import (
    CACHE_KEY_ALL_PRODUCTS,
    CACHE_TIMEOUT_FLASH,
)
from ..utils import clear_model_cache
from ..logging_config import get_product_logger, log_execution_time, LogOperation

from ..services.search_orm import Search


class CreateProduct:

    @staticmethod
    @log_execution_time(get_product_logger())
    def create_product(name, price, description):
        logger = get_product_logger()

        with LogOperation(f"Creando producto: {name}", logger):
            # Verificar si existe
            if Search.filter(Products, "name", name).exists():
                logger.warning(f"No es posible crear el producto: {name}")
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


class GetAllProducts:

    @staticmethod
    def get_all_products():

        cache_key = f"{CACHE_KEY_ALL_PRODUCTS}"
        all_products = cache.get(cache_key)
        total_products_save = None

        if all_products is None:

            all_products = (
                Search.search_default(Products).select_related().order_by("name")
            )
            total_products_save = all_products.count()
            cache.set(cache_key, all_products, CACHE_TIMEOUT_FLASH)

        return {
            "products": all_products,
            "total": total_products_save,
        }


class SearchByAjax:

    @staticmethod
    def search_products_ajax(query, limit=10):
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


class UpdateProducts:

    @staticmethod
    def update_product(original_name, new_name, new_price, new_description):

        try:
            product = Search.get(Products, "name", original_name)
            product.name = new_name
            product.price = new_price
            product.description = new_description
            product.save()

            # Limpiar cache
            clear_model_cache(CACHE_KEY_ALL_PRODUCTS)

            return product
        except ObjectDoesNotExist:
            raise ValueError("Producto no encontrado")


class DeleteProducts:

    @staticmethod
    def delete_product(name: str) -> bool:
        try:
            delete_product = Search.get(Products, "name", name)
            delete_product.delete()

            # Limpiar cache
            clear_model_cache(CACHE_KEY_ALL_PRODUCTS)

            return True
        except ObjectDoesNotExist:
            raise ValueError("Producto no encontrado")
