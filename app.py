"""
Sistema de Gestión para Emprendimientos Gastronómicos - VERSIÓN MEJORADA
Con diseño visual mejorado, subproductos, stock negativo, y más
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import pandas as pd
import io

# =============================================================================
# CONFIGURACIÓN Y ESTILOS
# =============================================================================

SUPABASE_URL = "https://rqwuytrkwnmtzowkusil.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxd3V5dHJrd25tdHpvd2t1c2lsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAyOTk4NzIsImV4cCI6MjA4NTg3NTg3Mn0.FnvDYN0KYpIIPAx4csJ4xozV07QIUbOERqmFuhuQzDY"

# CSS personalizado para mejorar diseño
def aplicar_estilos():
    st.markdown("""
    <style>
    /* Colores principales */
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --success-color: #45B7D1;
        --warning-color: #FFA07A;
        --danger-color: #FF6B6B;
    }
    
    /* Métricas mejoradas */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }
    
    /* Cards con sombra */
    .stExpander {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    
    /* Botones mejorados */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Tabs más bonitas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* Inputs con mejor estilo */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 8px;
    }
    
    /* Dataframes */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Alertas personalizadas */
    .stock-warning {
        background-color: #FFF3CD;
        border-left: 4px solid #FFA07A;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    
    .stock-danger {
        background-color: #FFE5E5;
        border-left: 4px solid #FF6B6B;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    
    .stock-ok {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# =============================================================================
# UTILIDADES
# =============================================================================

def normalizar_unidad(cantidad, unidad_origen, unidad_destino):
    """Convierte entre unidades compatibles"""
    conversiones_peso = {
        ('kg', 'gr'): 1000,
        ('gr', 'kg'): 0.001,
        ('kg', 'kg'): 1,
        ('gr', 'gr'): 1
    }
    
    conversiones_volumen = {
        ('l', 'ml'): 1000,
        ('ml', 'l'): 0.001,
        ('l', 'l'): 1,
        ('ml', 'ml'): 1
    }
    
    if (unidad_origen, unidad_destino) in conversiones_peso:
        return cantidad * conversiones_peso[(unidad_origen, unidad_destino)]
    elif (unidad_origen, unidad_destino) in conversiones_volumen:
        return cantidad * conversiones_volumen[(unidad_origen, unidad_destino)]
    else:
        return cantidad

def exportar_a_excel(df, nombre_hoja):
    """Exporta DataFrame a Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=nombre_hoja, index=False)
    output.seek(0)
    return output

def mostrar_stock_badge(stock):
    """Muestra badge de stock con color según estado"""
    if stock < 0:
        return f'<span style="background-color:#FF6B6B; color:white; padding:4px 12px; border-radius:12px; font-weight:600;">⚠️ {stock:.1f} (FALTA)</span>'
    elif stock < 10:
        return f'<span style="background-color:#FFA07A; color:white; padding:4px 12px; border-radius:12px; font-weight:600;">⚡ {stock:.1f} (BAJO)</span>'
    else:
        return f'<span style="background-color:#4CAF50; color:white; padding:4px 12px; border-radius:12px; font-weight:600;">✓ {stock:.1f}</span>'

# =============================================================================
# FUNCIONES DE PERFIL DE USUARIO
# =============================================================================

def obtener_perfil_usuario(user_id):
    """Obtiene perfil del usuario"""
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    return response.data[0] if response.data else None

def actualizar_nombre_negocio(user_id, nuevo_nombre):
    """Actualiza nombre del negocio"""
    try:
        supabase.table('users').update({'nombre_negocio': nuevo_nombre}).eq('id', user_id).execute()
        return True, "Nombre actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# FUNCIONES DE AUTENTICACIÓN
# =============================================================================

def verificar_estado_usuario(user_id):
    """Verifica acceso"""
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            user = response.data[0]
            estado = user.get('estado')
            fecha_vencimiento = user.get('fecha_vencimiento')
            
            if estado == 'suspendido':
                return False, "Cuenta suspendida. Contactá al administrador."
            
            if fecha_vencimiento:
                if datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date() < date.today():
                    return False, "Suscripción vencida. Contactá al administrador."
            
            return True, "Acceso permitido"
        return False, "Usuario no encontrado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login(email, password):
    """Login"""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.user:
            tiene_acceso, mensaje = verificar_estado_usuario(response.user.id)
            if tiene_acceso:
                st.session_state['user'] = response.user
                st.session_state['user_id'] = response.user.id
                st.session_state['email'] = response.user.email
                # Cargar perfil
                perfil = obtener_perfil_usuario(response.user.id)
                st.session_state['nombre_negocio'] = perfil.get('nombre_negocio', 'Mi Negocio') if perfil else 'Mi Negocio'
                return True, "Login exitoso"
            else:
                supabase.auth.sign_out()
                return False, mensaje
        return False, "Credenciales inválidas"
    except Exception as e:
        return False, f"Error: {str(e)}"

def logout():
    """Logout"""
    try:
        supabase.auth.sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    except Exception as e:
        st.error(f"Error: {str(e)}")

def registrar_usuario(email, password, nombre_negocio, nombre_contacto, telefono):
    """Registro"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        
        if response.user:
            supabase.table('users').insert({
                'id': response.user.id,
                'email': email,
                'nombre_negocio': nombre_negocio,
                'nombre_contacto': nombre_contacto,
                'telefono': telefono,
                'estado': 'prueba'
            }).execute()
            
            return True, "Registro exitoso. Pendiente de aprobación."
        return False, "Error al crear usuario"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# LOGIN UI
# =============================================================================

def mostrar_login():
    """Pantalla login mejorada"""
    
    # Centrar contenido
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #FF6B6B;'>🍰</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Sistema de Gestión Gastronómica</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Para emprendimientos que crecen</p>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "✨ Crear Cuenta"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="tu@email.com")
                password = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
                
                submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
                
                if submitted:
                    if email and password:
                        success, mensaje = login(email, password)
                        if success:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
                    else:
                        st.warning("Completá todos los campos")
        
        with tab2:
            with st.form("register_form"):
                reg_negocio = st.text_input("🏪 Nombre de tu Negocio", placeholder="Ej: Pastelería La Delicia")
                reg_contacto = st.text_input("👤 Tu Nombre", placeholder="Ej: Juan Pérez")
                reg_email = st.text_input("📧 Email", placeholder="tu@email.com", key="reg_email")
                reg_telefono = st.text_input("📞 Teléfono", placeholder="Opcional", key="reg_tel")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    reg_password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres", key="reg_pass")
                with col_b:
                    reg_password2 = st.text_input("🔒 Confirmar", type="password", placeholder="Repetí la contraseña", key="reg_pass2")
                
                submitted = st.form_submit_button("Crear Cuenta", use_container_width=True, type="primary")
                
                if submitted:
                    if reg_email and reg_password and reg_negocio and reg_contacto:
                        if reg_password != reg_password2:
                            st.error("Las contraseñas no coinciden")
                        elif len(reg_password) < 6:
                            st.error("La contraseña debe tener al menos 6 caracteres")
                        else:
                            success, mensaje = registrar_usuario(reg_email, reg_password, reg_negocio, reg_contacto, reg_telefono)
                            if success:
                                st.success(mensaje)
                                st.info("📧 Revisá tu email para confirmar")
                            else:
                                st.error(mensaje)
                    else:
                        st.warning("Completá campos obligatorios")

# =============================================================================
# FUNCIONES DE NEGOCIO
# =============================================================================

def obtener_ingredientes(user_id):
    """Obtener ingredientes"""
    response = supabase.table('ingredientes').select('*').eq('user_id', user_id).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def obtener_productos_para_ingredientes(user_id):
    """Obtiene productos marcados como subproductos"""
    response = supabase.table('productos').select('*').eq('user_id', user_id).eq('es_subproducto', True).execute()
    return response.data if response.data else []

def registrar_compra(user_id, fecha, ingrediente, cantidad, unidad, total, costo_unitario, proveedor):
    """Registra compra y actualiza stock"""
    try:
        # Registrar compra
        compra_data = {
            'user_id': user_id,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'ingrediente': ingrediente,
            'cantidad': cantidad,
            'unidad': unidad,
            'total': total,
            'costo_unitario': costo_unitario,
            'proveedor': proveedor
        }
        supabase.table('compras').insert(compra_data).execute()
        
        # Actualizar stock
        ing_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente).execute()
        
        if ing_response.data:
            ing_actual = ing_response.data[0]
            unidad_ing = ing_actual['unidad']
            cantidad_convertida = normalizar_unidad(cantidad, unidad, unidad_ing)
            
            nuevo_stock = ing_actual['stock_actual'] + cantidad_convertida
            nuevo_comprado = ing_actual['comprado'] + cantidad_convertida
            
            supabase.table('ingredientes').update({
                'stock_actual': nuevo_stock,
                'comprado': nuevo_comprado,
                'costo_unitario': costo_unitario,
                'precio_compra': total,
                'cantidad_compra': cantidad
            }).eq('id', ing_actual['id']).execute()
        else:
            supabase.table('ingredientes').insert({
                'user_id': user_id,
                'nombre': ingrediente,
                'unidad': unidad,
                'stock_actual': cantidad,
                'comprado': cantidad,
                'consumido': 0,
                'costo_unitario': costo_unitario,
                'precio_compra': total,
                'cantidad_compra': cantidad
            }).execute()
        
        return True, "Compra registrada y stock actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def obtener_compras(user_id):
    """Obtener compras ordenadas cronológicamente"""
    response = supabase.table('compras').select('*').eq('user_id', user_id).order('fecha', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def registrar_pedido_con_descuento(user_id, fecha, producto_nombre, cantidad, tipo, precio_unitario, cliente):
    """Registra pedido AUNQUE NO HAYA STOCK (stock negativo permitido)"""
    try:
        # Buscar producto
        producto_response = supabase.table('productos').select('*').eq('user_id', user_id).eq('nombre', producto_nombre).execute()
        
        if not producto_response.data:
            return False, f"Producto '{producto_nombre}' no encontrado.", []
        
        producto = producto_response.data[0]
        producto_id = producto['id']
        
        # Obtener receta
        receta_response = supabase.table('recetas').select('*').eq('producto_id', producto_id).execute()
        
        if not receta_response.data:
            return False, f"El producto no tiene receta.", []
        
        # Calcular lo que falta (pero NO bloquear)
        faltantes_info = []
        
        for ingrediente in receta_response.data:
            cantidad_necesaria = ingrediente['cantidad'] * cantidad
            
            # Buscar en ingredientes
            stock_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente['ingrediente_nombre']).execute()
            
            if stock_response.data:
                ing_actual = stock_response.data[0]
                stock_actual = ing_actual['stock_actual']
                unidad_ing = ing_actual['unidad']
                cantidad_convertida = normalizar_unidad(cantidad_necesaria, ingrediente['unidad'], unidad_ing)
                
                if stock_actual < cantidad_convertida:
                    faltante = cantidad_convertida - stock_actual
                    faltantes_info.append({
                        'ingrediente': ingrediente['ingrediente_nombre'],
                        'faltante': faltante,
                        'unidad': unidad_ing
                    })
        
        # Registrar pedido (SIEMPRE)
        total = precio_unitario * cantidad if precio_unitario else None
        
        pedido_data = {
            'user_id': user_id,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'producto': producto_nombre,
            'cantidad': cantidad,
            'tipo': tipo,
            'precio_unitario': precio_unitario,
            'total': total,
            'cliente': cliente
        }
        supabase.table('pedidos').insert(pedido_data).execute()
        
        # Descontar stock (puede quedar negativo)
        for ingrediente in receta_response.data:
            cantidad_a_descontar = ingrediente['cantidad'] * cantidad
            
            ing_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente['ingrediente_nombre']).execute()
            
            if ing_response.data:
                ing_actual = ing_response.data[0]
                unidad_ing = ing_actual['unidad']
                cantidad_convertida = normalizar_unidad(cantidad_a_descontar, ingrediente['unidad'], unidad_ing)
                
                nuevo_stock = ing_actual['stock_actual'] - cantidad_convertida
                nuevo_consumido = ing_actual['consumido'] + cantidad_convertida
                
                supabase.table('ingredientes').update({
                    'stock_actual': nuevo_stock,
                    'consumido': nuevo_consumido
                }).eq('id', ing_actual['id']).execute()
        
        mensaje = f"Pedido registrado ({cantidad} unidades de {producto_nombre})."
        return True, mensaje, faltantes_info
    
    except Exception as e:
        return False, f"Error: {str(e)}", []

def obtener_pedidos(user_id):
    """Obtener pedidos ordenados"""
    response = supabase.table('pedidos').select('*').eq('user_id', user_id).order('fecha', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def obtener_productos(user_id):
    """Obtener productos"""
    response = supabase.table('productos').select('*').eq('user_id', user_id).eq('activo', True).execute()
    return response.data if response.data else []

def calcular_lista_compras(user_id):
    """Calcula qué ingredientes están en negativo (necesitan comprarse)"""
    df = obtener_ingredientes(user_id)
    if df.empty:
        return []
    
    faltantes = df[df['stock_actual'] < 0].copy()
    if faltantes.empty:
        return []
    
    faltantes['cantidad_a_comprar'] = faltantes['stock_actual'].abs()
    return faltantes[['nombre', 'cantidad_a_comprar', 'unidad', 'costo_unitario']].to_dict('records')

# =============================================================================
# INTERFAZ PRINCIPAL MEJORADA
# =============================================================================

def mostrar_app_principal():
    """Interfaz principal con mejor diseño"""
    aplicar_estilos()
    
    user_id = st.session_state.get('user_id')
    nombre_negocio = st.session_state.get('nombre_negocio', 'Mi Negocio')
    
    with st.sidebar:
        # Header con nombre del negocio EDITABLE
        if 'editing_name' not in st.session_state:
            st.session_state['editing_name'] = False
        
        if st.session_state['editing_name']:
            nuevo_nombre = st.text_input("Nombre del negocio", value=nombre_negocio, key="edit_nombre_negocio")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾", key="save_nombre"):
                    success, msg = actualizar_nombre_negocio(user_id, nuevo_nombre)
                    if success:
                        st.session_state['nombre_negocio'] = nuevo_nombre
                        st.session_state['editing_name'] = False
                        st.rerun()
            with col2:
                if st.button("❌", key="cancel_nombre"):
                    st.session_state['editing_name'] = False
                    st.rerun()
        else:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### 🏪 {nombre_negocio}")
            with col2:
                if st.button("✏️", key="edit_nombre_btn"):
                    st.session_state['editing_name'] = True
                    st.rerun()
        
        st.caption(f"👤 {st.session_state.get('email', '')}")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()
        
        st.divider()
        
        # Menú con iconos
        pagina = st.radio(
            "📍 Navegación",
            [
                "📊 Dashboard",
                "🧺 Inventario", 
                "🛒 Compras",
                "📦 Pedidos",
                "🍪 Productos",
                "📋 Lista de Compras",
                "💵 Calculadora",
                "💰 Finanzas"
            ],
            label_visibility="collapsed"
        )
    
    # Contenido
    if pagina == "📊 Dashboard":
        mostrar_dashboard()
    elif pagina == "🧺 Inventario":
        mostrar_inventario()
    elif pagina == "🛒 Compras":
        mostrar_compras()
    elif pagina == "📦 Pedidos":
        mostrar_pedidos()
    elif pagina == "🍪 Productos":
        mostrar_productos()
    elif pagina == "📋 Lista de Compras":
        mostrar_lista_compras()
    elif pagina == "💵 Calculadora":
        mostrar_calculadora()
    elif pagina == "💰 Finanzas":
        mostrar_finanzas()

def mostrar_dashboard():
    """Dashboard mejorado"""
    st.title("📊 Dashboard")
    
    user_id = st.session_state.get('user_id')
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    df_ing = obtener_ingredientes(user_id)
    df_ped = obtener_pedidos(user_id)
    df_comp = obtener_compras(user_id)
    productos = obtener_productos(user_id)
    
    with col1:
        st.metric("🧺 Ingredientes", len(df_ing))
    with col2:
        st.metric("📦 Pedidos", len(df_ped))
    with col3:
        st.metric("🍪 Productos", len(productos))
    with col4:
        total_invertido = df_comp['total'].sum() if not df_comp.empty and 'total' in df_comp.columns else 0
        st.metric("💰 Invertido", f"${total_invertido:,.0f}")
    
    st.write("")
    
    # Alertas importantes
    lista_compras = calcular_lista_compras(user_id)
    if lista_compras:
        st.markdown(f"""
        <div class="stock-danger">
            <strong>⚠️ ALERTA: Tenés {len(lista_compras)} ingredientes con stock negativo</strong><br>
            Andá a <strong>📋 Lista de Compras</strong> para ver qué necesitás comprar.
        </div>
        """, unsafe_allow_html=True)
    
    # Stock bajo (positivo pero menor a 10)
    if not df_ing.empty:
        stock_bajo = df_ing[(df_ing['stock_actual'] > 0) & (df_ing['stock_actual'] < 10)]
        if not stock_bajo.empty:
            st.markdown(f"""
            <div class="stock-warning">
                <strong>⚡ {len(stock_bajo)} ingredientes con stock bajo</strong>
            </div>
            """, unsafe_allow_html=True)

def mostrar_lista_compras():
    """NUEVA SECCIÓN: Lista de qué comprar"""
    st.title("📋 Lista de Compras Pendientes")
    st.write("Ingredientes que necesitás comprar (stock negativo)")
    
    user_id = st.session_state.get('user_id')
    lista = calcular_lista_compras(user_id)
    
    if not lista:
        st.success("✅ ¡Todo bien! No hay ingredientes faltantes.")
        st.balloons()
    else:
        st.markdown(f"""
        <div class="stock-danger">
            <strong>⚠️ Necesitás comprar {len(lista)} ingredientes</strong>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Tabla mejorada
        total_a_invertir = 0
        
        for item in lista:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {item['nombre']}")
                with col2:
                    st.metric("Faltante", f"{item['cantidad_a_comprar']:.1f} {item['unidad']}")
                with col3:
                    costo_unit = item.get('costo_unitario', 0)
                    st.metric("Costo/u", f"${costo_unit:.2f}")
                with col4:
                    total_item = item['cantidad_a_comprar'] * costo_unit
                    st.metric("Total", f"${total_item:,.2f}")
                    total_a_invertir += total_item
                
                st.divider()
        
        # Total
        st.markdown(f"""
        <div style="background-color:#4ECDC4; color:white; padding:20px; border-radius:10px; text-align:center;">
            <h2>Total a invertir: ${total_a_invertir:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.info("💡 **Tip:** Una vez que compres estos ingredientes, registralos en la sección **🛒 Compras** para actualizar el stock.")

def mostrar_inventario():
    """Inventario mejorado"""
    st.title("🧺 Inventario de Ingredientes")
    
    user_id = st.session_state.get('user_id')
    df = obtener_ingredientes(user_id)
    
    # Botón exportar
    if not df.empty:
        excel_file = exportar_a_excel(df, "Inventario")
        st.download_button(
            label="📥 Exportar a Excel",
            data=excel_file,
            file_name=f"inventario_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Agregar nuevo (formulario limpio después de submit)
    with st.expander("➕ Agregar Nuevo Ingrediente", expanded=False):
        with st.form("form_nuevo_ingrediente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre*")
                unidad = st.selectbox("Unidad*", ["gr", "kg", "un", "lata", "ml", "l"])
            with col2:
                stock = st.number_input("Stock inicial", min_value=0.0, value=0.0, step=0.1)
                costo = st.number_input("Costo unitario", min_value=0.0, value=0.0, step=0.01)
            
            if st.form_submit_button("✅ Agregar", type="primary"):
                if nombre:
                    try:
                        supabase.table('ingredientes').insert({
                            'user_id': user_id,
                            'nombre': nombre,
                            'unidad': unidad,
                            'stock_actual': stock,
                            'costo_unitario': costo,
                            'comprado': 0,
                            'consumido': 0
                        }).execute()
                        st.success(f"✅ {nombre} agregado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("El nombre es obligatorio")
    
    st.write("")
    
    # Listar con diseño mejorado
    if not df.empty:
        for idx, row in df.iterrows():
            stock_actual = row['stock_actual']
            
            # Color según stock
            if stock_actual < 0:
                badge_color = "danger"
                icon = "⚠️"
            elif stock_actual < 10:
                badge_color = "warning"
                icon = "⚡"
            else:
                badge_color = "ok"
                icon = "✓"
            
            with st.expander(f"{icon} {row['nombre']} - {stock_actual:.1f} {row['unidad']}", expanded=False):
                st.markdown(mostrar_stock_badge(stock_actual), unsafe_allow_html=True)
                st.write("")
                
                # Mostrar detalles
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Comprado", f"{row['comprado']:.1f}")
                with col2:
                    st.metric("Consumido", f"{row['consumido']:.1f}")
                with col3:
                    st.metric("Costo/u", f"${row['costo_unitario']:.2f}")
    else:
        st.info("No hay ingredientes. ¡Agregá el primero!")

def mostrar_compras():
    """Compras mejorada con formulario que se limpia"""
    st.title("🛒 Compras de Insumos")
    
    user_id = st.session_state.get('user_id')
    
    tab1, tab2 = st.tabs(["➕ Registrar Compra", "📋 Historial"])
    
    with tab1:
        st.subheader("Nueva Compra")
        
        # Formulario que se limpia al enviar
        with st.form("form_compra", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("Fecha", value=date.today())
                
                try:
                    ings = supabase.table('ingredientes').select('nombre, unidad').eq('user_id', user_id).execute()
                    lista_ings = [ing['nombre'] for ing in ings.data] if ings.data else []
                except:
                    lista_ings = []
                
                usar_existente = st.checkbox("Usar ingrediente existente", value=True if lista_ings else False)
                
                if usar_existente and lista_ings:
                    ingrediente = st.selectbox("Ingrediente", lista_ings)
                    ing_data = supabase.table('ingredientes').select('unidad').eq('user_id', user_id).eq('nombre', ingrediente).execute()
                    unidad = ing_data.data[0]['unidad'] if ing_data.data else 'gr'
                    st.caption(f"Unidad: {unidad}")
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        ingrediente = st.text_input("Ingrediente nuevo*")
                    with col_b:
                        unidad = st.selectbox("Unidad*", ["gr", "kg", "un", "ml", "l", "lata"])
            
            with col2:
                cantidad = st.number_input("Cantidad*", min_value=0.0, value=0.0, step=1.0)
                total = st.number_input("Total pagado ($)*", min_value=0.0, value=0.0, step=1.0)
                proveedor = st.text_input("Proveedor (opcional)")
            
            if cantidad > 0 and total > 0:
                costo_unitario = total / cantidad
                st.info(f"💰 Costo unitario: ${costo_unitario:.2f} por {unidad}")
            else:
                costo_unitario = 0
            
            if st.form_submit_button("✅ Registrar Compra", type="primary", use_container_width=True):
                if not ingrediente or cantidad <= 0:
                    st.error("Completá campos obligatorios")
                else:
                    success, mensaje = registrar_compra(user_id, fecha, ingrediente, cantidad, unidad, total, costo_unitario, proveedor)
                    if success:
                        st.success(mensaje)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(mensaje)
    
    with tab2:
        st.subheader("Historial (más reciente primero)")
        
        df = obtener_compras(user_id)
        
        if not df.empty:
            # Exportar
            excel_file = exportar_a_excel(df, "Compras")
            st.download_button(
                label="📥 Exportar a Excel",
                data=excel_file,
                file_name=f"compras_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Mostrar
            st.dataframe(
                df[['fecha', 'ingrediente', 'cantidad', 'unidad', 'total', 'costo_unitario', 'proveedor']].head(50),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay compras registradas")

def mostrar_pedidos():
    """Pedidos mejorado - PERMITE STOCK NEGATIVO"""
    st.title("📦 Registro de Pedidos")
    
    user_id = st.session_state.get('user_id')
    
    tab1, tab2 = st.tabs(["➕ Nuevo Pedido", "📋 Historial"])
    
    with tab1:
        st.subheader("Registrar Pedido")
        
        try:
            productos_response = supabase.table('productos').select('nombre').eq('user_id', user_id).eq('activo', True).execute()
            lista_productos = [p['nombre'] for p in productos_response.data] if productos_response.data else []
        except:
            lista_productos = []
        
        if not lista_productos:
            st.warning("⚠️ Creá productos primero en **🍪 Productos**")
            return
        
        # Formulario que se limpia
        with st.form("form_pedido", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("Fecha*", value=date.today())
                producto = st.selectbox("Producto*", lista_productos)
                cantidad = st.number_input("Cantidad*", min_value=1, value=1, step=1)
            
            with col2:
                tipo = st.selectbox("Tipo*", ["Venta", "Regalo", "Muestra"])
                precio_unitario = st.number_input("Precio unitario", min_value=0.0, value=0.0, step=10.0)
                cliente = st.text_input("Cliente (opcional)")
            
            if producto:
                try:
                    prod_data = supabase.table('productos').select('*').eq('user_id', user_id).eq('nombre', producto).execute()
                    if prod_data.data:
                        precio_sugerido = prod_data.data[0].get('precio_venta', 0)
                        st.caption(f"💡 Precio sugerido: ${precio_sugerido:,.2f}")
                except:
                    pass
            
            if st.form_submit_button("✅ Registrar Pedido", type="primary", use_container_width=True):
                if not producto or cantidad <= 0:
                    st.error("Completá campos obligatorios")
                else:
                    with st.spinner("Procesando..."):
                        success, mensaje, faltantes = registrar_pedido_con_descuento(user_id, fecha, producto, cantidad, tipo.lower(), precio_unitario, cliente)
                        
                        if success:
                            st.success(mensaje)
                            
                            # Mostrar advertencia si hay faltantes
                            if faltantes:
                                st.markdown("""
                                <div class="stock-warning">
                                    <strong>⚠️ ATENCIÓN: Algunos ingredientes quedaron en negativo</strong>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                for f in faltantes:
                                    st.warning(f"🔴 {f['ingrediente']}: faltan {f['faltante']:.2f} {f['unidad']}")
                                
                                st.info("📋 Andá a **Lista de Compras** para ver qué necesitás reponer")
                            else:
                                st.balloons()
                            
                            st.rerun()
                        else:
                            st.error(mensaje)
    
    with tab2:
        st.subheader("Historial (más reciente primero)")
        df = obtener_pedidos(user_id)
        
        if not df.empty:
            excel_file = exportar_a_excel(df, "Pedidos")
            st.download_button(
                label="📥 Exportar a Excel",
                data=excel_file,
                file_name=f"pedidos_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.dataframe(
                df[['fecha', 'producto', 'cantidad', 'tipo', 'precio_unitario', 'total', 'cliente']].head(50),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay pedidos")

# Continuar con productos y calculadora...
def mostrar_productos():
    st.title("🍪 Productos")
    st.info("Sección de productos con subproductos en desarrollo...")

def mostrar_calculadora():
    st.title("💵 Calculadora de Precios")
    st.info("Calculadora en desarrollo...")

def mostrar_finanzas():
    st.title("💰 Finanzas")
    st.info("Análisis financiero en desarrollo...")

# =============================================================================
# MAIN
# =============================================================================

def main():
    st.set_page_config(
        page_title="Gestión Gastronómica",
        page_icon="🍰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if 'user' not in st.session_state:
        mostrar_login()
    else:
        tiene_acceso, mensaje = verificar_estado_usuario(st.session_state['user_id'])
        if tiene_acceso:
            mostrar_app_principal()
        else:
            st.error(mensaje)
            if st.button("Cerrar Sesión"):
                logout()

if __name__ == "__main__":
    main()
