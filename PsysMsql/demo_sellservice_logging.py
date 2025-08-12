#!/usr/bin/env python3
"""
Demo del sistema de logging en SellService
Muestra cómo funciona el logging con operaciones de venta
"""

import os
import sys
import django


# Configurar Django
sys.path.append('/home/Francisco-dev/work/Python/Django/WORK/PsysMsql')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PsysMsql.settings')
django.setup()

from psysmysql.services.sell_service import SellService
from psysmysql.logging_config import get_sell_logger
from psysmysql.models import SellProducts

def demo_logging_sellservice():
    """
    Demuestra el sistema de logging del SellService
    """
    logger = get_sell_logger()
    
    print("🚀 DEMO: Sistema de Logging en SellService")
    print("=" * 60)
    
    # 1. Demo de cálculo de totales
    print("\n📊 1. CALCULANDO TOTALES DE VENTA")
    print("-" * 40)
    
    try:
        # Simular productos en carrito (esto normalmente vendría de la DB)
        sell_products = SellProducts.objects.all()[:3]  # Tomar máximo 3 productos
        
        if sell_products.exists():
            totals = SellService.calculate_sell_totals(sell_products)
            print(f"✅ Totales calculados exitosamente")
            print(f"   📦 Productos: {totals['quantity']}")
            print(f"   💰 Subtotal: ${totals['subtotal']}")
            print(f"   📈 IVA: ${totals['iva_calculated']}")
        else:
            print("⚠️  No hay productos en el carrito para demostrar")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Demo de validación de carrito
    print("\n🔍 2. VALIDANDO CARRITO")
    print("-" * 40)
    
    try:
        validation = SellService.validate_cart_before_checkout()
        print(f"✅ Validación completada:")
        print(f"   ✓ Válido: {validation['valid']}")
        print(f"   📦 Productos: {validation['products_count']}")
        if validation['errors']:
            print(f"   ❌ Errores: {len(validation['errors'])}")
        if validation['warnings']:
            print(f"   ⚠️  Advertencias: {len(validation['warnings'])}")
            
    except Exception as e:
        print(f"❌ Error en validación: {e}")
    
    # 3. Demo de cálculo de cambio
    print("\n💵 3. CALCULANDO CAMBIO")
    print("-" * 40)
    
    try:
        # Simular una venta de $50.00 con pago de $60.00
        total = 50.00
        payment = 60.00
        change = SellService.calculate_change(total, payment)
        print(f"✅ Cambio calculado:")
        print(f"   💰 Total: ${total}")
        print(f"   💸 Pago: ${payment}")
        print(f"   🔄 Cambio: ${change}")
        
    except Exception as e:
        print(f"❌ Error calculando cambio: {e}")
    
    # 4. Demo de limpieza de cache
    print("\n🧹 4. LIMPIANDO CACHE")
    print("-" * 40)
    
    try:
        SellService.clear_sell_cache()
        print("✅ Cache limpiado exitosamente")
        
    except Exception as e:
        print(f"❌ Error limpiando cache: {e}")
    
    # 5. Mostrar logs recientes
    print("\n📋 5. LOGS GENERADOS")
    print("-" * 40)
    print("Los logs se han guardado en el sistema de logging.")
    print("Para ver los logs en tiempo real:")
    print("   tail -f logs/psysmysql_*.log")
    print()
    print("Para filtrar logs de ventas:")
    print("   grep 'psysmysql.sells' logs/psysmysql_*.log")

if __name__ == "__main__":
    demo_logging_sellservice()
