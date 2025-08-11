#!/usr/bin/env python3
"""
Demo del Dashboard con datos de prueba
Genera datos y muestra las funcionalidades del dashboard
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Configurar Django
sys.path.append('/home/Francisco-dev/work/Python/Django/WORK/PsysMsql')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PsysMsql.settings')
django.setup()

from psysmysql.services.dashboard_service import DashboardService
from psysmysql.models import Products, RegistersellDetail, Stock, Clients, SellProducts


def generate_sample_data():
    """
    Genera datos de prueba para demostrar el dashboard
    """
    print("🔄 Generando datos de prueba...")
    
    # 1. Crear productos de ejemplo si no existen
    products_data = [
        {"name": "Laptop Dell XPS", "price": 1299.99, "description": "Laptop profesional"},
        {"name": "Mouse Logitech", "price": 29.99, "description": "Mouse inalámbrico"},
        {"name": "Teclado Mecánico", "price": 89.99, "description": "Teclado gaming"},
        {"name": "Monitor 4K", "price": 399.99, "description": "Monitor ultra HD"},
        {"name": "Webcam HD", "price": 59.99, "description": "Cámara web 1080p"},
    ]
    
    created_products = []
    for product_data in products_data:
        product, created = Products.objects.get_or_create(
            name=product_data["name"],
            defaults={
                'price': Decimal(str(product_data["price"])),
                'description': product_data["description"]
            }
        )
        created_products.append(product)
        if created:
            print(f"   ✅ Producto creado: {product.name}")
            
            # Crear stock para cada producto
            Stock.objects.get_or_create(
                id_products=product,
                defaults={'quantitystock': random.randint(5, 50)}
            )
    
    # 2. Crear clientes de ejemplo
    clients_data = [
        {"name": "Juan Pérez", "email": "juan@example.com", "nit": "12345678"},
        {"name": "María García", "email": "maria@example.com", "nit": "87654321"},
        {"name": "Carlos López", "email": "carlos@example.com", "nit": "11223344"},
    ]
    
    for client_data in clients_data:
        client, created = Clients.objects.get_or_create(
            email=client_data["email"],
            defaults={
                'name': client_data["name"],
                'nit': client_data["nit"],
                'direction': 'Dirección de ejemplo',
                'country': 'Colombia',
                'departament': 'Bogotá',
                'city': 'Bogotá'
            }
        )
        if created:
            print(f"   ✅ Cliente creado: {client.name}")
    
    # 3. Generar ventas de los últimos 30 días
    print("   📊 Generando ventas de ejemplo...")
    
    payment_methods = ['efectivo', 'tarjeta', 'transferencia', 'cheque']
    employees = ['admin', 'vendedor1', 'vendedor2', 'empleado_demo']
    
    for i in range(30):  # Últimos 30 días
        date = datetime.now() - timedelta(days=i)
        
        # Generar 1-5 ventas por día aleatoriamente
        num_sales = random.randint(0, 5)
        
        for j in range(num_sales):
            # Seleccionar producto y cantidad aleatoriamente
            product = random.choice(created_products)
            quantity = random.randint(1, 3)
            unit_price = product.price
            total = unit_price * quantity
            
            # Crear registro de venta
            sale = RegistersellDetail.objects.create(
                id_employed=random.choice(employees),
                total_sell=total,
                type_pay=random.choice(payment_methods),
                state_sell='completada',
                notes=f'Venta de demo - {product.name}',
                quantity_pay=total + Decimal(str(random.uniform(0, 10))),  # Simular pago con cambio
                detail_sell=f'[{{"name": "{product.name}", "quantity": {quantity}, "price": {float(unit_price)}}}]'
            )
            
            # Actualizar fecha manualmente para simular ventas históricas
            sale.date = date.replace(
                hour=random.randint(8, 18),
                minute=random.randint(0, 59)
            )
            sale.save()
    
    print(f"   ✅ Datos de prueba generados exitosamente")
    print(f"   📦 Productos: {Products.objects.count()}")
    print(f"   👥 Clientes: {Clients.objects.count()}")
    print(f"   💰 Ventas: {RegistersellDetail.objects.count()}")
    print(f"   📋 Stock registros: {Stock.objects.count()}")


def demo_dashboard_service():
    """
    Demuestra las funcionalidades del DashboardService
    """
    print("\n🎯 DEMO: Dashboard Service")
    print("=" * 50)
    
    # 1. KPIs principales
    print("\n📊 1. KPIs PRINCIPALES")
    print("-" * 30)
    
    kpis = DashboardService.get_main_kpis(30)
    print(f"   📈 Ventas totales: {kpis['total_sales']}")
    print(f"   💰 Ingresos totales: ${kpis['total_revenue']:,.2f}")
    print(f"   📊 Venta promedio: ${kpis['average_sale']:,.2f}")
    print(f"   📦 Productos total: {kpis['total_products']}")
    print(f"   ⚠️  Stock bajo: {kpis['low_stock_products']} productos")
    print(f"   👥 Clientes totales: {kpis['total_clients']}")
    print(f"   📈 Crecimiento ventas: {kpis['sales_growth']}%")
    print(f"   💹 Crecimiento ingresos: {kpis['revenue_growth']}%")
    
    # 2. Datos para gráficos
    print("\n📈 2. DATOS PARA GRÁFICOS")
    print("-" * 30)
    
    chart_data = DashboardService.get_sales_chart_data(30, 'day')
    print(f"   📅 Puntos de datos: {len(chart_data['labels'])}")
    print(f"   📊 Datasets: {len(chart_data['datasets'])}")
    
    if chart_data['labels']:
        print(f"   📆 Período: {chart_data['labels'][0]} - {chart_data['labels'][-1]}")
    
    # 3. Rendimiento de productos
    print("\n🏆 3. RENDIMIENTO DE PRODUCTOS")
    print("-" * 30)
    
    performance = DashboardService.get_products_performance(5)
    print(f"   🔝 Top productos: {len(performance['top_products'])}")
    
    for i, product in enumerate(performance['top_products'][:3], 1):
        print(f"      {i}. {product['name']}: {product['quantity_sold']} unidades, ${product['revenue']:,.2f}")
    
    print(f"   ⚠️  Productos con stock bajo: {len(performance['low_stock_products'])}")
    
    # 4. Métodos de pago
    print("\n💳 4. MÉTODOS DE PAGO")
    print("-" * 30)
    
    payment_data = DashboardService.get_payment_methods_chart()
    print(f"   🏷️  Métodos disponibles: {len(payment_data['labels'])}")
    
    for label, count in zip(payment_data['labels'], payment_data['datasets'][0]['data']):
        print(f"      {label}: {count} transacciones")
    
    # 5. Actividades recientes
    print("\n🕐 5. ACTIVIDADES RECIENTES")
    print("-" * 30)
    
    activities = DashboardService.get_recent_activities(5)
    print(f"   📝 Actividades encontradas: {len(activities)}")
    
    for i, activity in enumerate(activities[:3], 1):
        print(f"      {i}. {activity['description']} - ${activity['amount']:,.2f}")
        print(f"         📅 {activity['timestamp']}")
    
    # 6. Alertas
    print("\n🚨 6. ALERTAS Y NOTIFICACIONES")
    print("-" * 30)
    
    alerts = DashboardService.get_alerts_and_notifications()
    print(f"   ⚡ Alertas activas: {len(alerts)}")
    
    for alert in alerts:
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(alert['priority'], "⚪")
        print(f"      {priority_icon} {alert['title']}: {alert['message']}")


def demo_dashboard_complete():
    """
    Demuestra el resumen completo del dashboard
    """
    print("\n🎯 DEMO: Dashboard Completo")
    print("=" * 50)
    
    summary = DashboardService.get_dashboard_summary()
    
    print(f"   ✅ Resumen generado en: {summary['generated_at']}")
    print(f"   📊 KPIs incluidos: {len(summary['kpis'])} métricas")
    print(f"   📈 Gráficos: {len(summary['sales_chart']['datasets'])} datasets")
    print(f"   🏆 Top productos: {len(summary['products_performance']['top_products'])}")
    print(f"   🕐 Actividades: {len(summary['recent_activities'])}")
    
    # Mostrar estructura de datos
    print(f"\n   🗂️  ESTRUCTURA DE DATOS:")
    for key, value in summary.items():
        if key == 'generated_at':
            continue
        print(f"      - {key}: {type(value).__name__}")


def main():
    """
    Función principal del demo
    """
    print("🚀 DEMO COMPLETO DEL DASHBOARD")
    print("=" * 60)
    
    # Paso 1: Generar datos de prueba
    generate_sample_data()
    
    # Paso 2: Demostrar funcionalidades del service
    demo_dashboard_service()
    
    # Paso 3: Demostrar dashboard completo
    demo_dashboard_complete()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETADO EXITOSAMENTE")
    print("\n📌 PRÓXIMOS PASOS:")
    print("   1. Accede al dashboard en: http://localhost:8000/dashboard/")
    print("   2. Explora las métricas y gráficos interactivos")
    print("   3. Prueba las funcionalidades AJAX de actualización")
    print("   4. Revisa los logs generados en: logs/psysmysql_*.log")
    print("\n🎉 ¡Dashboard listo para usar!")


if __name__ == "__main__":
    main()
