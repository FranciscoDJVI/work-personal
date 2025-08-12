"""
Utilidades para cache, optimización de queries y funciones helper
"""
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from .constants import (
    ADMIN_GROUP, SELLER_GROUP, 
     CACHE_TIMEOUT_MEDIUM,
    PRODUCTS_PER_PAGE
)

def is_admin(user):
    """Verifica si el usuario pertenece al grupo Administrador"""
    if user.is_authenticated:
        return user.groups.filter(name=ADMIN_GROUP).exists()
    return False

def is_seller(user):
    """Verifica si el usuario pertenece al grupo Vendedor"""
    if user.is_authenticated:
        return user.groups.filter(name=SELLER_GROUP).exists()
    return False

def get_cached_users_with_groups():
    """Obtiene usuarios con grupos usando cache"""
    cache_key = "users_with_groups"
    users = cache.get(cache_key)
    
    if users is None:
        users = User.objects.all().order_by("username").prefetch_related("groups")
        cache.set(cache_key, users, CACHE_TIMEOUT_MEDIUM)
    
    return users

def invalidate_user_cache():
    """Invalida el cache de usuarios cuando hay cambios"""
    cache.delete("users_with_groups")

def paginate_queryset(queryset, request, per_page=PRODUCTS_PER_PAGE):
    """
    Pagina un queryset con manejo de errores
    
    Args:
        queryset: QuerySet a paginar
        request: Objeto request de Django
        per_page: Elementos por página
    
    Returns:
        tuple: (page_obj, paginator)
    """
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # Si la página no es un entero, mostrar la primera página
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj, paginator

def get_cache_key_for_model(model_name, user_id=None):
    """
    Genera cache keys consistentes para modelos
    
    Args:
        model_name: Nombre del modelo (ej: 'products', 'stock')
        user_id: ID del usuario (opcional, para cache por usuario)
    
    Returns:
        str: Cache key generado
    """
    if user_id:
        return f"{model_name}_{user_id}"
    return model_name

def clear_model_cache(model_name, user_id=None):
    """
    Limpia el cache de un modelo específico
    
    Args:
        model_name: Nombre del modelo
        user_id: ID del usuario (opcional)
    """
    cache_key = get_cache_key_for_model(model_name, user_id)
    cache.delete(cache_key)
