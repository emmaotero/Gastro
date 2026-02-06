"""
App de Gestión para Pastelerías
Sistema multi-tenant con control de acceso
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
import pandas as pd

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# TODO: Reemplazar con tus credenciales de Supabase
SUPABASE_URL = "TU_SUPABASE_URL"  # Lo obtenés de tu proyecto en Supabase
SUPABASE_KEY = "TU_SUPABASE_ANON_KEY"  # Lo obtenés de tu proyecto en Supabase

# Inicializar cliente Supabase
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = get_supabase_client()

# =============================================================================
# FUNCIONES DE AUTENTICACIÓN
# =============================================================================

def verificar_estado_usuario(user_id):
    """Verifica si el usuario tiene acceso activo"""
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            user = response.data[0]
            estado = user.get('estado')
            fecha_vencimiento = user.get('fecha_vencimiento')
            
            # Verificar si está suspendido
            if estado == 'suspendido':
                return False, "Tu cuenta ha sido suspendida. Contacta al administrador."
            
            # Verificar si venció
            if fecha_vencimiento:
                if datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date() < date.today():
                    return False, "Tu suscripción ha vencido. Contacta al administrador."
            
            return True, "Acceso permitido"
        return False, "Usuario no encontrado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login(email, password):
    """Login de usuario"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Verificar estado del usuario
            tiene_acceso, mensaje = verificar_estado_usuario(response.user.id)
            if tiene_acceso:
                st.session_state['user'] = response.user
                st.session_state['user_id'] = response.user.id
                st.session_state['email'] = response.user.email
                return True, "Login exitoso"
            else:
                supabase.auth.sign_out()
                return False, mensaje
        return False, "Credenciales inválidas"
    except Exception as e:
        return False, f"Error en login: {str(e)}"

def logout():
    """Cerrar sesión"""
    try:
        supabase.auth.sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    except Exception as e:
        st.error(f"Error al cerrar sesión: {str(e)}")

def registrar_usuario(email, password, nombre_negocio, nombre_contacto, telefono):
    """Registro de nuevo usuario (queda pendiente de aprobación)"""
    try:
        # Crear usuario en Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Crear registro en tabla users
            supabase.table('users').insert({
                'id': response.user.id,
                'email': email,
                'nombre_negocio': nombre_negocio,
                'nombre_contacto': nombre_contacto,
                'telefono': telefono,
                'estado': 'prueba'  # Estado inicial
            }).execute()
            
            return True, "Registro exitoso. Tu cuenta está pendiente de aprobación."
        return False, "Error al crear usuario"
    except Exception as e:
        return False, f"Error en registro: {str(e)}"

# =============================================================================
# INTERFAZ DE LOGIN/REGISTRO
# =============================================================================

def mostrar_login():
    """Pantalla de login"""
    st.title("🍰 Sistema de Gestión para Pastelerías")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Iniciar Sesión")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Ingresar", type="primary"):
            if email and password:
                success, mensaje = login(email, password)
                if success:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.warning("Por favor completa todos los campos")
    
    with tab2:
        st.subheader("Crear Nueva Cuenta")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Contraseña", type="password", key="reg_password")
        reg_password2 = st.text_input("Confirmar Contraseña", type="password", key="reg_password2")
        reg_negocio = st.text_input("Nombre de tu Pastelería", key="reg_negocio")
        reg_contacto = st.text_input("Tu Nombre", key="reg_contacto")
        reg_telefono = st.text_input("Teléfono (opcional)", key="reg_telefono")
        
        if st.button("Registrarse", type="primary"):
            if reg_email and reg_password and reg_negocio and reg_contacto:
                if reg_password != reg_password2:
                    st.error("Las contraseñas no coinciden")
                elif len(reg_password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    success, mensaje = registrar_usuario(
                        reg_email, reg_password, reg_negocio, 
                        reg_contacto, reg_telefono
                    )
                    if success:
                        st.success(mensaje)
                        st.info("📧 Revisa tu email para confirmar tu cuenta")
                    else:
                        st.error(mensaje)
            else:
                st.warning("Por favor completa todos los campos obligatorios")

# =============================================================================
# FUNCIONES DE NEGOCIO (CRUD)
# =============================================================================

def obtener_ingredientes(user_id):
    """Obtener todos los ingredientes del usuario"""
    response = supabase.table('ingredientes').select('*').eq('user_id', user_id).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def agregar_ingrediente(user_id, nombre, unidad, stock_actual, costo_unitario):
    """Agregar un nuevo ingrediente"""
    try:
        supabase.table('ingredientes').insert({
            'user_id': user_id,
            'nombre': nombre,
            'unidad': unidad,
            'stock_actual': stock_actual,
            'costo_unitario': costo_unitario
        }).execute()
        return True, "Ingrediente agregado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def obtener_pedidos(user_id):
    """Obtener pedidos del usuario"""
    response = supabase.table('pedidos').select('*').eq('user_id', user_id).order('fecha', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def registrar_pedido(user_id, fecha, producto, cantidad, tipo):
    """Registrar un nuevo pedido"""
    try:
        supabase.table('pedidos').insert({
            'user_id': user_id,
            'fecha': fecha.strftime('%Y-%m-%d'),
            'producto': producto,
            'cantidad': cantidad,
            'tipo': tipo
        }).execute()
        return True, "Pedido registrado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# INTERFAZ PRINCIPAL DE LA APP
# =============================================================================

def mostrar_app_principal():
    """Interfaz principal después del login"""
    
    # Sidebar con info del usuario
    with st.sidebar:
        st.title("🍰 Mi Pastelería")
        st.write(f"**Usuario:** {st.session_state.get('email', '')}")
        if st.button("Cerrar Sesión", type="secondary"):
            logout()
        
        st.divider()
        
        # Menú de navegación
        pagina = st.radio(
            "Navegación",
            ["📊 Dashboard", "🧺 Inventario", "📦 Pedidos", "🍪 Productos", "💰 Finanzas"]
        )
    
    # Contenido principal según la página seleccionada
    if pagina == "📊 Dashboard":
        mostrar_dashboard()
    elif pagina == "🧺 Inventario":
        mostrar_inventario()
    elif pagina == "📦 Pedidos":
        mostrar_pedidos()
    elif pagina == "🍪 Productos":
        mostrar_productos()
    elif pagina == "💰 Finanzas":
        mostrar_finanzas()

def mostrar_dashboard():
    """Dashboard principal"""
    st.title("📊 Dashboard")
    st.write("¡Bienvenido a tu sistema de gestión!")
    
    user_id = st.session_state.get('user_id')
    
    # Métricas básicas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ingredientes", len(obtener_ingredientes(user_id)))
    
    with col2:
        df_pedidos = obtener_pedidos(user_id)
        st.metric("Pedidos este mes", len(df_pedidos))
    
    with col3:
        st.metric("Productos activos", 0)  # TODO: implementar

def mostrar_inventario():
    """Gestión de inventario"""
    st.title("🧺 Inventario de Ingredientes")
    
    user_id = st.session_state.get('user_id')
    
    # Formulario para agregar ingrediente
    with st.expander("➕ Agregar Nuevo Ingrediente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del ingrediente")
            unidad = st.selectbox("Unidad", ["gr", "kg", "un", "lata", "ml", "l"])
        with col2:
            stock = st.number_input("Stock actual", min_value=0.0, step=0.1)
            costo = st.number_input("Costo unitario", min_value=0.0, step=0.01)
        
        if st.button("Agregar Ingrediente"):
            if nombre:
                success, mensaje = agregar_ingrediente(user_id, nombre, unidad, stock, costo)
                if success:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.warning("El nombre es obligatorio")
    
    # Mostrar tabla de ingredientes
    df = obtener_ingredientes(user_id)
    if not df.empty:
        st.dataframe(
            df[['nombre', 'unidad', 'stock_actual', 'costo_unitario']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay ingredientes registrados. ¡Agrega el primero!")

def mostrar_pedidos():
    """Gestión de pedidos"""
    st.title("📦 Registro de Pedidos")
    
    user_id = st.session_state.get('user_id')
    
    # Formulario para registrar pedido
    with st.expander("➕ Registrar Nuevo Pedido"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today())
            producto = st.text_input("Producto")
        with col2:
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            tipo = st.selectbox("Tipo", ["Venta", "Regalo", "Muestra"])
        
        if st.button("Registrar Pedido"):
            if producto:
                success, mensaje = registrar_pedido(user_id, fecha, producto, cantidad, tipo)
                if success:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.warning("El producto es obligatorio")
    
    # Mostrar tabla de pedidos
    df = obtener_pedidos(user_id)
    if not df.empty:
        st.dataframe(
            df[['fecha', 'producto', 'cantidad', 'tipo']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay pedidos registrados")

def mostrar_productos():
    """Gestión de productos y recetas"""
    st.title("🍪 Productos y Recetas")
    st.info("🚧 En desarrollo")
    # TODO: Implementar CRUD de productos y recetas

def mostrar_finanzas():
    """Análisis financiero"""
    st.title("💰 Análisis Financiero")
    st.info("🚧 En desarrollo")
    # TODO: Implementar costos, márgenes, reportes

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Gestión Pastelería",
        page_icon="🍰",
        layout="wide"
    )
    
    # Verificar si el usuario está logueado
    if 'user' not in st.session_state:
        mostrar_login()
    else:
        # Verificar que siga teniendo acceso
        tiene_acceso, mensaje = verificar_estado_usuario(st.session_state['user_id'])
        if tiene_acceso:
            mostrar_app_principal()
        else:
            st.error(mensaje)
            st.info("Por favor contacta al administrador para renovar tu suscripción")
            if st.button("Cerrar Sesión"):
                logout()

if __name__ == "__main__":
    main()
