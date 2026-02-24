import firebase_admin
from firebase_admin import firestore

# 1. Autenticación automática (Usa tu sesión de gcloud)
print("Conectando a Google Cloud...")
firebase_admin.initialize_app()
db = firestore.client()

# 2. El "Payload": Los datos que la app offline del sanguchero enviaría por la noche
datos_cierre_hoy = {
    "fecha_cierre": "2026-02-23", 
    "vendedor_id": "sangucheria_carlitos",
    "total_ventas": 145.00,
    "detalle_productos": [
        {"producto": "Pan con Chicharrón", "cantidad": 10, "subtotal": 100.00},
        {"producto": "Hamburguesa Clásica", "cantidad": 3, "subtotal": 21.00},
        {"producto": "Chicha Morada", "cantidad": 8, "subtotal": 24.00}
    ]
}

def guardar_cierre_en_firestore(datos):
    try:
        # Creamos un ID único usando el vendedor y la fecha
        doc_id = f"{datos['vendedor_id']}_{datos['fecha_cierre']}"
        
        # Apuntamos a la colección 'cierres_diarios' (si no existe, Firestore la crea)
        doc_ref = db.collection('cierres_diarios').document(doc_id)
        
        # Enviamos los datos a la nube
        doc_ref.set(datos)
        print(f"✅ ¡Éxito! El cierre del día se guardó en Firestore.")
        print(f"   Colección: cierres_diarios | Documento: {doc_id}")
        
    except Exception as e:
        print(f"❌ Error al intentar guardar en Firestore: {e}")

# 3. Ejecutamos la simulación
if __name__ == "__main__":
    guardar_cierre_en_firestore(datos_cierre_hoy)