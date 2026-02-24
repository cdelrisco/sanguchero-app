import firebase_admin
from firebase_admin import firestore

# 1. Nos conectamos a Google Cloud
firebase_admin.initialize_app()
db = firestore.client()

def generar_reporte_administrador(vendedor_id):
    print(f"📊 Generando reporte para: {vendedor_id}...\n")
    
    # 2. Consultamos todos los cierres de este vendedor
    cierres_ref = db.collection('cierres_diarios').where('vendedor_id', '==', vendedor_id).stream()
    
    total_ingresos = 0.0
    dias_trabajados = 0
    ventas_por_producto = {} # Para contar cantidades
    ingresos_por_producto = {} # Para contar dinero
    
    # 3. Procesamos cada día de trabajo
    for doc in cierres_ref:
        cierre = doc.to_dict()
        dias_trabajados += 1
        total_ingresos += cierre.get('total_ventas', 0)
        
        # Analizamos el detalle de productos vendidos ese día
        for item in cierre.get('detalle', []):
            nombre = item['producto']
            cantidad = item['cantidad']
            subtotal = item['subtotal']
            
            # Sumamos las cantidades
            if nombre in ventas_por_producto:
                ventas_por_producto[nombre] += cantidad
                ingresos_por_producto[nombre] += subtotal
            else:
                ventas_por_producto[nombre] = cantidad
                ingresos_por_producto[nombre] = subtotal

    # 4. Verificamos si hay datos
    if dias_trabajados == 0:
        print("No hay ventas registradas para analizar.")
        return

    # 5. Calculamos los ganadores
    # Buscamos el producto con mayor cantidad vendida
    producto_estrella = max(ventas_por_producto, key=ventas_por_producto.get)
    # Buscamos el producto que generó más dinero
    producto_rentable = max(ingresos_por_producto, key=ingresos_por_producto.get)

    # 6. Mostramos el Dashboard en la terminal
    print("========================================")
    print("       📈 DASHBOARD DE RESULTADOS       ")
    print("========================================")
    print(f"🗓️  Días analizados: {dias_trabajados}")
    print(f"💰 Ingresos Totales: S/ {total_ingresos:.2f}")
    print(f"💵 Promedio Diario:  S/ {(total_ingresos / dias_trabajados):.2f}")
    print("----------------------------------------")
    print(f"⭐ PRODUCTO ESTRELLA (Más popular):")
    print(f"   {producto_estrella} ({ventas_por_producto[producto_estrella]} unidades)")
    print(f"💎 PRODUCTO MÁS RENTABLE (Más ingresos):")
    print(f"   {producto_rentable} (S/ {ingresos_por_producto[producto_rentable]:.2f})")
    print("========================================")

# Ejecutamos el análisis
if __name__ == "__main__":
    # Usamos el mismo ID que pusimos en los scripts anteriores
    generar_reporte_administrador("sangucheria_carlitos")