import firebase_admin
from firebase_admin import firestore

# 1. Nos conectamos a Google Cloud
firebase_admin.initialize_app()
db = firestore.client()

def descargar_menu_activo():
    print("📲 Conectando al WiFi... Descargando menú actualizado...\n")
    
    # 2. Hacemos una consulta a la colección 'productos'
    # Solo traemos los que tienen 'disponible' en True
    productos_ref = db.collection('productos')
    query = productos_ref.where('disponible', '==', True)
    
    # Ejecutamos la consulta
    resultados = query.stream()
    
    menu_para_la_app = []
    
    # 3. Mostramos los datos simulando la interfaz de botones
    print("--- 🍔 BOTONES GENERADOS EN LA PANTALLA 🥤 ---")
    for doc in resultados:
        producto = doc.to_dict()
        producto['id'] = doc.id # Guardamos también el ID del documento
        menu_para_la_app.append(producto)
        
        # Formateamos cómo se vería el botón
        print(f" 🟩 [{producto['categoria'][:3].upper()}] {producto['nombre']} -> S/ {producto['precio']:.2f}")
        
    print("----------------------------------------------")
    print("✅ Menú guardado en la memoria del celular.")
    print("📶 El sanguchero ya puede apagar sus datos y salir a vender.")
    
    return menu_para_la_app

# Ejecutamos la lectura
if __name__ == "__main__":
    descargar_menu_activo()