import functions_framework
import firebase_admin
from firebase_admin import firestore
import datetime

# Inicializamos Firebase FUERA de las funciones principales.
# Esto es una buena práctica para que el contenedor reutilice la conexión.
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

# =====================================================================
# FUNCIÓN 1: RECIBIR EL CIERRE DEL DÍA (La que ya desplegaste)
# =====================================================================
@functions_framework.http
def recibir_cierre_dia(request):
    """HTTP Cloud Function para procesar el cierre de caja."""
    
    # --- CONFIGURACIÓN CORS ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    # --- RECIBIR LOS DATOS DEL CELULAR ---
    request_json = request.get_json(silent=True)
    
    if not request_json or 'ventas' not in request_json:
        return ({"error": "No se enviaron datos de ventas válidos."}, 400, headers)

    vendedor_id = request_json.get('vendedor_id', 'vendedor_desconocido')
    ventas_crudas = request_json['ventas']

    try:
        # --- LÓGICA DE NEGOCIO (El Cerebro) ---
        productos_ref = db.collection('productos').stream()
        catalogo = {doc.id: doc.to_dict() for doc in productos_ref}

        total_dinero = 0.0
        detalle_final = []

        for venta in ventas_crudas:
            id_producto = venta['id_prod']
            cantidad = venta['cantidad']
            
            if id_producto in catalogo:
                producto_oficial = catalogo[id_producto]
                precio_unitario = float(producto_oficial['precio'])
                subtotal = precio_unitario * cantidad
                
                total_dinero += subtotal
                
                detalle_final.append({
                    "producto": producto_oficial['nombre'],
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal
                })

        # --- GUARDAR EN FIRESTORE ---
        fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        doc_id = f"{vendedor_id}_{fecha_hoy}_{datetime.datetime.now().strftime('%H%M%S')}"
        
        documento_cierre = {
            "vendedor_id": vendedor_id,
            "fecha_cierre": fecha_hoy,
            "total_ventas": total_dinero,
            "detalle": detalle_final,
            "estado": "auditado_por_nube",
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        db.collection('cierres_diarios').document(doc_id).set(documento_cierre)
        
        respuesta = {
            "mensaje": "Cierre procesado exitosamente",
            "total_calculado": total_dinero,
            "id_recibo": doc_id
        }
        
        return (respuesta, 200, headers)

    except Exception as e:
        print(f"Error procesando cierre: {e}")
        return ({"error": "Error interno del servidor"}, 500, headers)


# =====================================================================
# FUNCIÓN 2: DESCARGAR EL MENÚ ACTUALIZADO (La nueva)
# =====================================================================
@functions_framework.http
def descargar_menu(request):
    """HTTP Cloud Function para enviar el menú activo a la app del celular."""
    
    # --- CONFIGURACIÓN CORS ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # --- CONSULTAR FIRESTORE ---
        # Solo traemos los productos que están marcados como disponibles
        # (Si un día no hay pan, el admin pone disponible: False en la base de datos y ya no baja al celular)
        productos_ref = db.collection('productos').where('disponible', '==', True).stream()
        
        menu_activo = []
        for doc in productos_ref:
            producto = doc.to_dict()
            menu_activo.append({
                "id_prod": doc.id,
                "nombre": producto.get('nombre', 'Producto Sin Nombre'),
                "precio": float(producto.get('precio', 0.0)),
                "categoria": producto.get('categoria', 'Otros')
            })
            
        # --- RESPONDER AL CELULAR ---
        return ({"menu": menu_activo}, 200, headers)

    except Exception as e:
        print(f"Error descargando menú: {e}")
        return ({"error": "No se pudo cargar el menú desde la base de datos"}, 500, headers)
    
# =====================================================================
# FUNCIÓN 3: GESTIONAR CATÁLOGO (Para el panel de Administrador)
# =====================================================================
@functions_framework.http
def gestionar_catalogo(request):
    """HTTP Cloud Function para listar, crear o editar productos."""
    
    # --- CONFIGURACIÓN CORS ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # SI ES GET: Devolvemos TODOS los productos (activos e inactivos)
        if request.method == 'GET':
            productos_ref = db.collection('productos').stream()
            catalogo = []
            for doc in productos_ref:
                p = doc.to_dict()
                p['id_prod'] = doc.id
                catalogo.append(p)
                
            return ({"productos": catalogo}, 200, headers)

        # SI ES POST: Guardamos o actualizamos un producto
        elif request.method == 'POST':
            data = request.get_json(silent=True)
            
            # Si nos envían un ID, es una actualización. Si no, generamos uno nuevo.
            id_prod = data.get('id_prod')
            if not id_prod:
                import uuid
                # Generamos un ID corto aleatorio (ej. prod_a1b2c3d4)
                id_prod = f"prod_{str(uuid.uuid4())[:8]}" 
            
            # Preparamos el documento
            producto_a_guardar = {
                "nombre": data.get('nombre', 'Sin Nombre'),
                "precio": float(data.get('precio', 0.0)),
                "categoria": data.get('categoria', 'Otros'),
                "disponible": bool(data.get('disponible', True))
            }
            
            # Guardamos en Firestore
            db.collection('productos').document(id_prod).set(producto_a_guardar)
            
            return ({"mensaje": "✅ Producto guardado con éxito", "id_prod": id_prod}, 200, headers)

    except Exception as e:
        print(f"Error en admin catalogo: {e}")
        return ({"error": "Error interno al gestionar el catálogo"}, 500, headers)
    
# =====================================================================
# FUNCIÓN 4: DASHBOARD ANALÍTICO (VERSIÓN 6 MÉTRICAS - OMNICANAL)
# =====================================================================
@functions_framework.http
def obtener_dashboard(request):
    """HTTP Cloud Function para generar estadísticas de ventas de todas las terminales."""
    
    # --- CONFIGURACIÓN CORS ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # AQUÍ ESTÁ LA CORRECCIÓN CLAVE: 
        # Usamos .stream() directo sin .where() para leer todos los recibos de cualquier vendedor
        cierres_ref = db.collection('cierres_diarios').stream()
        
        total_ingresos = 0.0
        fechas_unicas = set()
        ventas_por_producto = {}
        ingresos_por_producto = {}
        total_unidades = 0

        for doc in cierres_ref:
            cierre = doc.to_dict()
            
            # Sumar días trabajados de forma única
            fecha = cierre.get('fecha_cierre')
            if fecha:
                fechas_unicas.add(fecha)
                
            total_ingresos += cierre.get('total_ventas', 0)
            
            # Recorrer el detalle de cada ticket o cierre
            for item in cierre.get('detalle', []):
                nombre = item['producto']
                cantidad = item['cantidad']
                subtotal = item['subtotal']
                
                ventas_por_producto[nombre] = ventas_por_producto.get(nombre, 0) + cantidad
                ingresos_por_producto[nombre] = ingresos_por_producto.get(nombre, 0) + subtotal
                total_unidades += cantidad

        dias_trabajados = len(fechas_unicas)

        # Si aún no hay ventas, devolvemos un mensaje seguro para no romper la app
        if dias_trabajados == 0:
            return ({"mensaje": "No hay datos suficientes"}, 200, headers)

        # Calcular promedios y ganadores
        producto_estrella = max(ventas_por_producto, key=ventas_por_producto.get)
        producto_rentable = max(ingresos_por_producto, key=ingresos_por_producto.get)
        promedio_diario = total_ingresos / dias_trabajados

        # Empaquetar las 6 métricas para el HTML del Administrador
        datos_dashboard = {
            "total_ingresos": total_ingresos,
            "dias_trabajados": dias_trabajados,
            "promedio_diario": promedio_diario,
            "total_unidades": total_unidades,
            "producto_estrella": {
                "nombre": producto_estrella,
                "cantidad": ventas_por_producto[producto_estrella]
            },
            "producto_rentable": {
                "nombre": producto_rentable,
                "ingresos": ingresos_por_producto[producto_rentable]
            }
        }

        return (datos_dashboard, 200, headers)

    except Exception as e:
        print(f"Error en dashboard: {e}")
        return ({"error": "Error interno al generar dashboard"}, 500, headers)
    
# =====================================================================
# FUNCIÓN 5: LOGIN DE ADMINISTRADOR
# =====================================================================
@functions_framework.http
def login_admin(request):
    """HTTP Cloud Function para validar el acceso al panel."""
    
    # --- CONFIGURACIÓN CORS ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        datos = request.get_json(silent=True)
        usuario = datos.get('usuario')
        password = datos.get('password')

        # Credenciales de prueba para la competencia
        USUARIO_CORRECTO = "admin"
        PASSWORD_CORRECTO = "demo2026"

        if usuario == USUARIO_CORRECTO and password == PASSWORD_CORRECTO:
            # Si es correcto, devolvemos éxito y un "token" simulado
            return ({"acceso": True, "mensaje": "Bienvenido"}, 200, headers)
        else:
            # Si falla, devolvemos error 401 (No autorizado)
            return ({"acceso": False, "error": "Usuario o contraseña incorrectos"}, 401, headers)

    except Exception as e:
        print(f"Error en login: {e}")
        return ({"error": "Error interno del servidor"}, 500, headers)