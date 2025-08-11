"""
Vistas del Dashboard con métricas avanzadas
Incluye vistas para el dashboard principal y endpoints AJAX
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.db import models
from .services.dashboard_service import DashboardService
from .services.sell_service import SellService
from .services.stock_service import StockService
from .logging_config import (
    get_sell_logger,
    log_execution_time,
    log_function_call,
    LogOperation
)


class DashboardView(View):
    """Vista principal del dashboard con métricas de negocio"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Renderiza la página principal del dashboard"""
        logger = get_sell_logger()
        
        with LogOperation('Cargando dashboard principal', logger):
            # Intentar obtener datos del cache primero
            dashboard_data = cache.get('dashboard_summary')
            
            if not dashboard_data:
                # Si no hay cache, generar datos y guardar en cache por 5 minutos
                dashboard_data = DashboardService.get_dashboard_summary()
                cache.set('dashboard_summary', dashboard_data, 300)  # 5 minutos
                logger.info('Datos del dashboard generados y guardados en cache')
            else:
                logger.info('Datos del dashboard obtenidos desde cache')
            
            # Obtener alertas (no cacheadas para tiempo real)
            alerts = DashboardService.get_alerts_and_notifications()
            
            context = {
                'dashboard_data': dashboard_data,
                'alerts': alerts,
                'page_title': 'Dashboard - PsysMysql',
                'user': request.user
            }
            
            logger.info(f'Dashboard cargado para usuario: {request.user.username}')
            return render(request, 'dashboard/main.html', context)


class DashboardAPIView(View):
    """API endpoints para actualizar datos del dashboard vía AJAX"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Endpoint para obtener datos actualizados del dashboard"""
        logger = get_sell_logger()
        
        endpoint = request.GET.get('endpoint', 'summary')
        days = int(request.GET.get('days', 30))
        
        try:
            with LogOperation(f'API call: {endpoint} para {days} días', logger):
                if endpoint == 'summary':
                    data = DashboardService.get_dashboard_summary()
                    
                elif endpoint == 'kpis':
                    data = DashboardService.get_main_kpis(days)
                    
                elif endpoint == 'sales_chart':
                    grouping = request.GET.get('grouping', 'day')
                    data = DashboardService.get_sales_chart_data(days, grouping)
                    
                elif endpoint == 'products':
                    limit = int(request.GET.get('limit', 10))
                    data = DashboardService.get_products_performance(limit)
                    
                elif endpoint == 'payment_methods':
                    data = DashboardService.get_payment_methods_chart()
                    
                elif endpoint == 'activities':
                    limit = int(request.GET.get('limit', 20))
                    data = DashboardService.get_recent_activities(limit)
                    
                elif endpoint == 'alerts':
                    data = DashboardService.get_alerts_and_notifications()
                    
                else:
                    return JsonResponse({'error': 'Endpoint no válido'}, status=400)
                
                logger.info(f'API respuesta exitosa para {endpoint}')
                return JsonResponse({
                    'success': True,
                    'data': data,
                    'endpoint': endpoint
                })
                
        except Exception as e:
            logger.error(f'Error en API {endpoint}: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class RealtimeStatsView(View):
    """Vista para estadísticas en tiempo real"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Endpoint para estadísticas en tiempo real (WebSocket alternative)"""
        logger = get_sell_logger()
        
        try:
            with LogOperation('Obteniendo estadísticas en tiempo real', logger):
                # Estadísticas rápidas sin cache
                from django.utils import timezone
                from .models import RegistersellDetail, SellProducts, Stock
                
                today = timezone.now().date()
                
                realtime_stats = {
                    'timestamp': timezone.now().isoformat(),
                    'today_sales': RegistersellDetail.objects.filter(
                        date__date=today
                    ).count(),
                    'cart_items': SellProducts.objects.count(),
                    'low_stock_alert': Stock.objects.filter(
                        quantitystock__lt=10
                    ).count(),
                    'no_stock_alert': Stock.objects.filter(
                        quantitystock=0
                    ).count()
                }
                
                logger.info('Estadísticas en tiempo real actualizadas')
                return JsonResponse({
                    'success': True,
                    'data': realtime_stats
                })
                
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas tiempo real: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
@log_function_call(get_sell_logger())
def quick_stats(request):
    """Vista rápida para estadísticas básicas (para includes)"""
    from django.utils import timezone
    from .models import RegistersellDetail
    
    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)
    
    stats = {
        'today_sales': RegistersellDetail.objects.filter(date__date=today).count(),
        'week_sales': RegistersellDetail.objects.filter(date__date__gte=week_ago).count(),
        'total_revenue_today': RegistersellDetail.objects.filter(
            date__date=today
        ).aggregate(total=models.Sum('total_sell'))['total'] or 0
    }
    
    return JsonResponse(stats)


@login_required  
@log_function_call(get_sell_logger())
def refresh_dashboard_cache(request):
    """Endpoint para forzar actualización del cache del dashboard"""
    logger = get_sell_logger()
    
    try:
        # Limpiar cache existente
        cache.delete('dashboard_summary')
        
        # Generar nuevos datos
        dashboard_data = DashboardService.get_dashboard_summary()
        
        # Guardar en cache
        cache.set('dashboard_summary', dashboard_data, 300)
        
        logger.info('Cache del dashboard actualizado exitosamente')
        return JsonResponse({
            'success': True,
            'message': 'Cache actualizado exitosamente',
            'timestamp': dashboard_data['generated_at']
        })
        
    except Exception as e:
        logger.error(f'Error actualizando cache del dashboard: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
