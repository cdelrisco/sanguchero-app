import firebase_admin
from firebase_admin import firestore
import datetime

# 1. Nos conectamos a Google Cloud
firebase_admin.initialize_app()
db = firestore.client()

# 2. LA REALIDAD OFFLINE: Esto es lo único que envía el celular en la noche.
# Solo los IDs de lo que vendió y la cantidad. Cero precios, cero matemáticas.
ventas_crudas_del_dia = [
    {"id_prod": "prod_001", "cantidad": 15},  # 15 Panes con Chicharrón
    {"id_prod": "prod_003", "cantidad": 5},   # 5 Hamburguesas
    {"id_prod": "prod_004", "cantidad": 20},  # 20 Chichas
]

def procesar_cierre_inteligente(vendedor_id, ventas_crudas):
    print("☁️ Iniciando procesamiento en la nube...")
    
    # PASO A: Descargamos el catálogo oficial de precios de Firestore
    print("1. Consultando precios oficiales...")
    productos_ref = db.collection('productos').stream()
    catalogo = {}
    for doc in productos_ref:
        catalogo[doc.id] = doc.to_dict() # Guardamos en memoria: {'prod_001': {nombre:..., precio:...}}

    # PASO B: Hacemos los cálculos cruzando los datos
    print("2. Calculando la caja del día...")
    total_dinero = 0.0
    detalle_final = []

    for venta in ventas_crudas:
        id_producto = venta['id_prod']
        cantidad = venta['cantidad']
        
        # Buscamos el producto en nuestro catálogo oficial
        if id_producto in catalogo:
            producto_oficial = catalogo[id_producto]
            precio_unitario = producto_oficial['precio']
            subtotal = precio_unitario * cantidad
            
            # Sumamos a la caja fuerte
            total_dinero += subtotal
            
            # Armamos el recibo detallado
            detalle_final.append({
                "producto": producto_oficial['nombre'],
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })
        else:
            print(f"⚠️ Alerta: El producto {id_producto} no existe en la base de datos.")

    # PASO C: Armamos el documento final y lo guardamos en Firestore
    print("3. Guardando el Cierre Oficial...")
    fecha_hoy = "2026-02-23" # Simulamos la fecha actual
    
    documento_cierre = {
        "vendedor_id": vendedor_id,
        "fecha_cierre": fecha_hoy,
        "total_ventas": total_dinero,
        "detalle": detalle_final,
        "estado": "auditado_por_nube"
    }
    
    # Guardamos en la colección 'cierres_diarios'
    doc_id = f"{vendedor_id}_{fecha_hoy}"
    db.collection('cierres_diarios').document(doc_id).set(documento_cierre)
    
    print("\n✅ ¡CIERRE EXITOSO!")
    print(f"💰 Total calculado en caja: S/ {total_dinero:.2f}")
    for item in detalle_final:
        print(f"   - {item['cantidad']}x {item['producto']} (S/ {item['subtotal']:.2f})")

# Ejecutamos el motor
if __name__ == "__main__":
    procesar_cierre_inteligente("sangucheria_carlitos", ventas_crudas_del_dia)