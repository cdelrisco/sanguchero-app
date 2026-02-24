import firebase_admin
from firebase_admin import firestore

# 1. Nos conectamos igual que antes
print("Conectando a Google Cloud...")
firebase_admin.initialize_app()
db = firestore.client()

# 2. Nuestro menú inicial de la Sanguchería
menu_inicial = [
    {"id_prod": "prod_001", "nombre": "Pan con Chicharrón", "precio": 10.00, "categoria": "Sánguches", "disponible": True},
    {"id_prod": "prod_002", "nombre": "Pan con Lomo", "precio": 12.00, "categoria": "Sánguches", "disponible": True},
    {"id_prod": "prod_003", "nombre": "Hamburguesa Clásica", "precio": 7.00, "categoria": "Sánguches", "disponible": True},
    {"id_prod": "prod_004", "nombre": "Chicha Morada (Vaso)", "precio": 3.00, "categoria": "Bebidas", "disponible": True},
    {"id_prod": "prod_005", "nombre": "Café Pasado", "precio": 2.50, "categoria": "Bebidas", "disponible": True}
]

def cargar_catalogo(productos):
    print("Subiendo el menú a Firestore...")
    coleccion_ref = db.collection('productos')
    
    # Recorremos la lista y guardamos cada producto
    for item in productos:
        # Usamos el id_prod como el nombre del documento para que sea fácil de buscar
        doc_id = item.pop("id_prod") # Sacamos el ID de la data para usarlo como llave
        
        try:
            coleccion_ref.document(doc_id).set(item)
            print(f"  🥪 Agregado: {item['nombre']} a S/ {item['precio']}")
        except Exception as e:
            print(f"  ❌ Error al agregar {item['nombre']}: {e}")
            
    print("\n✅ ¡Catálogo cargado exitosamente!")

# 3. Ejecutamos la carga
if __name__ == "__main__":
    cargar_catalogo(menu_inicial)