"""
Servicio para Dashboard con métricas avanzadas
Proporciona datos para gráficos, KPIs y análisis de negocio
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F, Value, DecimalField, IntegerField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from django.utils import timezone
from ..models import (
    RegistersellDetail, 
    Products, 
    Stock, 
    SellProducts,
    Clients
)
from ..logging_config import (
    get_sell_logger,
    log_execution_time,
    log_function_call,
    LogOperation
)


class DashboardService:
    """Servicio para generar métricas y datos del dashboard"""
    
    @staticmethod
    @log_execution_time(get_sell_logger())
    def get_main_kpis(days_back=30):
        """
        Obtiene los KPIs principales del dashboard
        
        Args:
            days_back (int): Número de días hacia atrás para calcular métricas
            
        Returns:
            dict: KPIs principales del negocio
        """
        logger = get_sell_logger()
        
        with LogOperation(f'Calculando KPIs principales para {days_back} días', logger):
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Consulta principal para ventas en el período
            sales_queryset = RegistersellDetail.objects.filter(
                date__range=[start_date, end_date]
            )
            
            # KPIs de ventas
            sales_data = sales_queryset.aggregate(
                total_sales=Count('idsell'),
                total_revenue=Coalesce(Sum('total_sell'), Value(0), output_field=DecimalField()),
                average_sale=Coalesce(Avg('total_sell'), Value(0), output_field=DecimalField()),
            )
            
            # KPIs de productos
            products_data = Products.objects.aggregate(
                total_products=Count('idproducts'),
            )
            
            # KPIs de stock
            stock_data = Stock.objects.aggregate(
                total_stock=Coalesce(Sum('quantitystock'), Value(0), output_field=IntegerField()),
                products_in_stock=Count('idstock'),
                low_stock_products=Count('idstock', filter=Q(quantitystock__lt=10))
            )
            
            # KPIs de clientes
            clients_data = Clients.objects.aggregate(
                total_clients=Count('id'),
            )
            
            # Calcular crecimiento (comparar con período anterior)
            prev_start = start_date - timedelta(days=days_back)
            prev_sales = RegistersellDetail.objects.filter(
                date__range=[prev_start, start_date]
            ).aggregate(
                prev_revenue=Coalesce(Sum('total_sell'), Value(0), output_field=DecimalField()),
                prev_sales_count=Count('idsell')
            )
            
            # Calcular porcentajes de crecimiento
            revenue_growth = 0
            sales_growth = 0
            
            if prev_sales['prev_revenue'] > 0:
                revenue_growth = ((sales_data['total_revenue'] - prev_sales['prev_revenue']) 
                                / prev_sales['prev_revenue']) * 100
                
            if prev_sales['prev_sales_count'] > 0:
                sales_growth = ((sales_data['total_sales'] - prev_sales['prev_sales_count']) 
                              / prev_sales['prev_sales_count']) * 100
            
            kpis = {
                # Ventas
                'total_sales': sales_data['total_sales'],
                'total_revenue': float(sales_data['total_revenue']),
                'average_sale': float(sales_data['average_sale']),
                'revenue_growth': round(revenue_growth, 2),
                'sales_growth': round(sales_growth, 2),
                
                # Productos y Stock
                'total_products': products_data['total_products'],
                'total_stock': stock_data['total_stock'],
                'products_in_stock': stock_data['products_in_stock'],
                'low_stock_products': stock_data['low_stock_products'],
                
                # Clientes
                'total_clients': clients_data['total_clients'],
                
                # Metadatos
                'period_days': days_back,
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d')
            }
            
            logger.info(f'KPIs calculados: {sales_data["total_sales"]} ventas, ${sales_data["total_revenue"]} ingresos')
            return kpis
    
    @staticmethod
    @log_execution_time(get_sell_logger())
    def get_sales_chart_data(days_back=30, grouping='day'):
        """
        Obtiene datos para gráfico de ventas a lo largo del tiempo
        
        Args:
            days_back (int): Días hacia atrás
            grouping (str): 'day', 'week', 'month' - agrupación de datos
            
        Returns:
            dict: Datos para gráfico de líneas/barras
        """
        logger = get_sell_logger()
        
        with LogOperation(f'Generando datos de gráfico de ventas: {grouping} por {days_back} días', logger):
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Usar SQL raw más simple para evitar problemas de timezone
            sales_by_date = RegistersellDetail.objects.filter(
                date__range=[start_date, end_date]
            ).extra(
                select={'date_only': "DATE(date)"},
            ).values('date_only').annotate(
                sales_count=Count('idsell'),
                revenue=Coalesce(Sum('total_sell'), Value(0), output_field=DecimalField())
            ).order_by('date_only')
            
            # Formatear datos para Chart.js
            labels = []
            sales_data = []
            revenue_data = []
            
            for item in sales_by_date:
                if item['date_only']:  # Evitar valores None
                    labels.append(str(item['date_only']))
                    sales_data.append(item['sales_count'])
                    revenue_data.append(float(item['revenue']))
            
            # Si no hay datos, crear datos vacíos para evitar errores
            if not labels:
                labels = ['Sin datos']
                sales_data = [0]
                revenue_data = [0]
            
            chart_data = {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Ventas',
                        'data': sales_data,
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'Ingresos ($)',
                        'data': revenue_data,
                        'borderColor': 'rgb(255, 99, 132)',
                        'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                        'yAxisID': 'y1'
                    }
                ]
            }
            
            logger.info(f'Datos de gráfico generados: {len(labels)} puntos de datos')
            return chart_data
    
    @staticmethod
    @log_execution_time(get_sell_logger())
    def get_products_performance(limit=10):
        """
        Obtiene los productos con mejor y peor rendimiento
        
        Args:
            limit (int): Número de productos a mostrar
            
        Returns:
            dict: Top productos y productos con bajo rendimiento
        """
        logger = get_sell_logger()
        
        with LogOperation(f'Analizando rendimiento de productos (top {limit})', logger):
            # Obtener ventas por producto desde RegistersellDetail
            # Nota: Necesitaríamos parsear detail_sell o usar otra lógica
            # Por ahora usamos SellProducts como proxy
            
            product_sales = SellProducts.objects.select_related('idproduct').values(
                'idproduct__name',
                'idproduct__idproducts',
                'idproduct__price'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('priceunitaty'))
            ).order_by('-total_revenue')
            
            # Top productos
            top_products = list(product_sales[:limit])
            
            # Productos con bajo stock
            low_stock_products = Stock.objects.select_related('id_products').filter(
                quantitystock__lt=10
            ).values(
                'id_products__name',
                'id_products__idproducts',
                'quantitystock'
            )[:limit]
            
            performance_data = {
                'top_products': [
                    {
                        'name': item['idproduct__name'],
                        'quantity_sold': item['total_quantity'],
                        'revenue': float(item['total_revenue']),
                        'price': float(item['idproduct__price'])
                    } for item in top_products
                ],
                'low_stock_products': [
                    {
                        'name': item['id_products__name'],
                        'stock': item['quantitystock']
                    } for item in low_stock_products
                ]
            }
            
            logger.info(f'Rendimiento calculado: {len(top_products)} top productos, {len(low_stock_products)} productos con bajo stock')
            return performance_data
    
    @staticmethod
    @log_function_call(get_sell_logger())
    def get_payment_methods_chart():
        """
        Obtiene distribución de métodos de pago para gráfico circular
        
        Returns:
            dict: Datos para gráfico de dona/circular
        """
        logger = get_sell_logger()
        
        payment_distribution = RegistersellDetail.objects.values('type_pay').annotate(
            count=Count('idsell'),
            revenue=Sum('total_sell')
        ).order_by('-count')
        
        # Preparar datos para Chart.js
        labels = []
        data = []
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ]
        
        for i, item in enumerate(payment_distribution):
            labels.append(item['type_pay'] or 'No especificado')
            data.append(item['count'])
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors[:len(data)],
                'borderWidth': 1
            }]
        }
        
        logger.info(f'Métodos de pago analizados: {len(labels)} tipos diferentes')
        return chart_data
    
    @staticmethod
    @log_function_call(get_sell_logger())
    def get_recent_activities(limit=20):
        """
        Obtiene actividades recientes del sistema
        
        Args:
            limit (int): Número máximo de actividades
            
        Returns:
            list: Lista de actividades recientes
        """
        logger = get_sell_logger()
        
        with LogOperation(f'Obteniendo {limit} actividades recientes', logger):
            recent_sales = RegistersellDetail.objects.select_related().order_by('-date')[:limit]
            
            activities = []
            for sale in recent_sales:
                activities.append({
                    'type': 'sale',
                    'description': f'Venta realizada por {sale.id_employed}',
                    'amount': float(sale.total_sell),
                    'timestamp': sale.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'details': {
                        'payment_method': sale.type_pay,
                        'state': sale.state_sell
                    }
                })
            
            logger.info(f'Actividades recientes obtenidas: {len(activities)} registros')
            return activities
    
    @staticmethod
    @log_execution_time(get_sell_logger())
    def get_dashboard_summary():
        """
        Obtiene un resumen completo para el dashboard principal
        
        Returns:
            dict: Resumen completo con todos los datos necesarios
        """
        logger = get_sell_logger()
        
        with LogOperation('Generando resumen completo del dashboard', logger):
            summary = {
                'kpis': DashboardService.get_main_kpis(30),
                'sales_chart': DashboardService.get_sales_chart_data(30, 'day'),
                'products_performance': DashboardService.get_products_performance(10),
                'payment_methods': DashboardService.get_payment_methods_chart(),
                'recent_activities': DashboardService.get_recent_activities(10),
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info('Resumen completo del dashboard generado exitosamente')
            return summary
    
    @staticmethod
    @log_function_call(get_sell_logger())
    def get_alerts_and_notifications():
        """
        Obtiene alertas y notificaciones para el dashboard
        
        Returns:
            list: Lista de alertas activas
        """
        logger = get_sell_logger()
        
        alerts = []
        
        # Alerta de stock bajo
        low_stock_count = Stock.objects.filter(quantitystock__lt=10).count()
        if low_stock_count > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Stock Bajo',
                'message': f'{low_stock_count} productos con stock bajo',
                'action': 'Ver inventario',
                'priority': 'medium'
            })
        
        # Alerta de productos sin stock
        no_stock_count = Stock.objects.filter(quantitystock=0).count()
        if no_stock_count > 0:
            alerts.append({
                'type': 'danger',
                'title': 'Sin Stock',
                'message': f'{no_stock_count} productos agotados',
                'action': 'Reabastecer urgente',
                'priority': 'high'
            })
        
        # Verificar ventas del día
        today = timezone.now().date()
        today_sales = RegistersellDetail.objects.filter(date__date=today).count()
        
        if today_sales == 0 and timezone.now().hour > 12:
            alerts.append({
                'type': 'info',
                'title': 'Sin ventas hoy',
                'message': 'No se han registrado ventas el día de hoy',
                'action': 'Revisar actividad',
                'priority': 'low'
            })
        
        logger.info(f'Alertas generadas: {len(alerts)} alertas activas')
        return alerts
