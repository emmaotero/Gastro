"""
Panel de Administrador
Para gestionar clientes, suspender/activar cuentas, ver estadísticas
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import pandas as pd

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

SUPABASE_URL = "TU_SUPABASE_URL"
SUPABASE_KEY = "TU_SUPABASE_ANON_KEY"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# Email del super admin (TU EMAIL)
ADMIN_EMAIL = "tu_email@ejemplo.com"  # CAMBIAR POR TU EMAIL

# =============================================================================
# FUNCIONES DE ADMIN
# =============================================================================

def verificar_admin(email):
    """Verifica si el usuario es administrador"""
    return email == ADMIN_EMAIL

def obtener_todos_usuarios():
    """Obtener lista de todos los clientes"""
    response = supabase.table('users').select('*').order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def cambiar_estado_usuario(user_id, nuevo_estado):
    """Cambiar estado de un usuario (activar/suspender)"""
    try:
        supabase.table('users').update({'estado': nuevo_estado}).eq('id', user_id).execute()
        return True, f"Estado cambiado a {nuevo_estado}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def extender_suscripcion(user_id, dias):
    """Extender la suscripción de un usuario"""
    try:
        # Obtener fecha actual de vencimiento
        response = supabase.table('users').select('fecha_vencimiento').eq('id', user_id).execute()
        
        if response.data:
            fecha_actual = response.data[0].get('fecha_vencimiento')
            if fecha_actual:
                nueva_fecha = datetime.strptime(fecha_actual, '%Y-%m-%d').date() + timedelta(days=dias)
            else:
                nueva_fecha = date.today() + timedelta(days=dias)
        else:
            nueva_fecha = date.today() + timedelta(days=dias)
        
        supabase.table('users').update({
            'fecha_vencimiento': nueva_fecha.strftime('%Y-%m-%d')
        }).eq('id', user_id).execute()
        
        return True, f"Suscripción extendida hasta {nueva_fecha}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def obtener_estadisticas():
    """Obtener estadísticas generales"""
    df = obtener_todos_usuarios()
    if df.empty:
        return {
            'total': 0,
            'activos': 0,
            'suspendidos': 0,
            'prueba': 0
        }
    
    return {
        'total': len(df),
        'activos': len(df[df['estado'] == 'activo']),
        'suspendidos': len(df[df['estado'] == 'suspendido']),
        'prueba': len(df[df['estado'] == 'prueba'])
    }

def login_admin(email, password):
    """Login de administrador"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and verificar_admin(email):
            st.session_state['admin_user'] = response.user
            st.session_state['admin_email'] = email
            return True, "Login admin exitoso"
        return False, "No tienes permisos de administrador"
    except Exception as e:
        return False, f"Error: {str(e)}"

def logout_admin():
    """Cerrar sesión de admin"""
    supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# =============================================================================
# INTERFAZ DE LOGIN ADMIN
# =============================================================================

def mostrar_login_admin():
    """Pantalla de login para administrador"""
    st.title("🔐 Panel de Administrador")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Acceso Restringido")
        email = st.text_input("Email de Administrador")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary", use_container_width=True):
            if email and password:
                success, mensaje = login_admin(email, password)
                if success:
                    st.success(mensaje)
                    st.rerun()
                else:
                    st.error(mensaje)
            else:
                st.warning("Completa todos los campos")

# =============================================================================
# INTERFAZ PRINCIPAL DEL ADMIN
# =============================================================================

def mostrar_panel_admin():
    """Panel principal de administración"""
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Admin Panel")
        st.write(f"**Admin:** {st.session_state.get('admin_email', '')}")
        if st.button("Cerrar Sesión"):
            logout_admin()
        
        st.divider()
        
        pagina = st.radio(
            "Menú",
            ["📊 Dashboard", "👥 Gestión de Clientes", "📈 Estadísticas"]
        )
    
    # Contenido
    if pagina == "📊 Dashboard":
        mostrar_dashboard_admin()
    elif pagina == "👥 Gestión de Clientes":
        mostrar_gestion_clientes()
    elif pagina == "📈 Estadísticas":
        mostrar_estadisticas_admin()

def mostrar_dashboard_admin():
    """Dashboard principal del admin"""
    st.title("📊 Dashboard Administrativo")
    
    stats = obtener_estadisticas()
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clientes", stats['total'])
    with col2:
        st.metric("✅ Activos", stats['activos'])
    with col3:
        st.metric("⏸️ Suspendidos", stats['suspendidos'])
    with col4:
        st.metric("🔄 En Prueba", stats['prueba'])
    
    st.divider()
    
    # Tabla de usuarios recientes
    st.subheader("Últimos Clientes Registrados")
    df = obtener_todos_usuarios()
    if not df.empty:
        df_recientes = df.head(10)
        st.dataframe(
            df_recientes[['nombre_negocio', 'email', 'estado', 'fecha_creacion']],
            use_container_width=True,
            hide_index=True
        )

def mostrar_gestion_clientes():
    """Gestión de clientes"""
    st.title("👥 Gestión de Clientes")
    
    df = obtener_todos_usuarios()
    
    if df.empty:
        st.info("No hay clientes registrados aún")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.selectbox(
            "Filtrar por estado",
            ["Todos", "activo", "suspendido", "prueba"]
        )
    
    # Aplicar filtro
    if filtro_estado != "Todos":
        df_filtrado = df[df['estado'] == filtro_estado]
    else:
        df_filtrado = df
    
    st.write(f"**{len(df_filtrado)} clientes encontrados**")
    
    # Mostrar cada cliente con acciones
    for idx, cliente in df_filtrado.iterrows():
        with st.expander(f"🏪 {cliente['nombre_negocio']} - {cliente['email']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Estado actual:** {cliente['estado']}")
                st.write(f"**Contacto:** {cliente.get('nombre_contacto', 'N/A')}")
                st.write(f"**Teléfono:** {cliente.get('telefono', 'N/A')}")
                st.write(f"**Fecha registro:** {cliente['fecha_creacion']}")
                
                vencimiento = cliente.get('fecha_vencimiento')
                if vencimiento:
                    st.write(f"**Vence:** {vencimiento}")
                
                if cliente.get('notas'):
                    st.write(f"**Notas:** {cliente['notas']}")
            
            with col2:
                st.subheader("Acciones")
                
                # Cambiar estado
                nuevo_estado = st.selectbox(
                    "Cambiar estado",
                    ["activo", "suspendido", "prueba"],
                    index=["activo", "suspendido", "prueba"].index(cliente['estado']),
                    key=f"estado_{cliente['id']}"
                )
                
                if st.button("Aplicar cambio de estado", key=f"btn_estado_{cliente['id']}"):
                    success, mensaje = cambiar_estado_usuario(cliente['id'], nuevo_estado)
                    if success:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)
                
                st.divider()
                
                # Extender suscripción
                dias = st.number_input(
                    "Extender suscripción (días)",
                    min_value=1,
                    value=30,
                    step=1,
                    key=f"dias_{cliente['id']}"
                )
                
                if st.button("Extender suscripción", key=f"btn_extend_{cliente['id']}"):
                    success, mensaje = extender_suscripcion(cliente['id'], dias)
                    if success:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)

def mostrar_estadisticas_admin():
    """Estadísticas y reportes"""
    st.title("📈 Estadísticas")
    
    df = obtener_todos_usuarios()
    
    if df.empty:
        st.info("No hay datos para mostrar")
        return
    
    # Gráfico de distribución por estado
    st.subheader("Distribución de Clientes por Estado")
    estado_counts = df['estado'].value_counts()
    st.bar_chart(estado_counts)
    
    # Tabla completa
    st.subheader("Tabla Completa de Clientes")
    st.dataframe(
        df[['nombre_negocio', 'email', 'nombre_contacto', 'estado', 'fecha_creacion', 'fecha_vencimiento']],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# MAIN
# =============================================================================

def main():
    st.set_page_config(
        page_title="Admin Panel",
        page_icon="⚙️",
        layout="wide"
    )
    
    if 'admin_user' not in st.session_state:
        mostrar_login_admin()
    else:
        mostrar_panel_admin()

if __name__ == "__main__":
    main()
