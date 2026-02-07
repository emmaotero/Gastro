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
    
    user_id = st.session_state.get('user_id')
    
    # Tabs para organizar
    tab1, tab2 = st.tabs(["📋 Mis Productos", "➕ Crear Producto"])
    
    with tab1:
        # Mostrar lista de productos
        st.subheader("Productos Registrados")
        
        try:
            response = supabase.table('productos').select('*').eq('user_id', user_id).eq('activo', True).execute()
            
            if response.data:
                for producto in response.data:
                    with st.expander(f"🍰 {producto['nombre']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Tipo:** {producto.get('tipo', 'N/A')}")
                            st.write(f"**Precio de venta:** ${producto.get('precio_venta', 0):,.2f}")
                            st.write(f"**Costo embalaje:** ${producto.get('costo_embalaje', 0):,.2f}")
                        
                        with col2:
                            # Obtener receta
                            receta_response = supabase.table('recetas').select('*').eq('producto_id', producto['id']).execute()
                            
                            if receta_response.data:
                                st.write("**Ingredientes:**")
                                for ingrediente in receta_response.data:
                                    st.write(f"- {ingrediente['ingrediente_nombre']}: {ingrediente['cantidad']} {ingrediente['unidad']}")
                                
                                # Calcular costo
                                costo_total = 0
                                for ing in receta_response.data:
                                    # Buscar costo del ingrediente
                                    ing_data = supabase.table('ingredientes').select('costo_unitario').eq('user_id', user_id).eq('nombre', ing['ingrediente_nombre']).execute()
                                    if ing_data.data:
                                        costo_unitario = ing_data.data[0].get('costo_unitario', 0)
                                        costo_total += ing['cantidad'] * costo_unitario
                                
                                costo_total += producto.get('costo_embalaje', 0)
                                precio_venta = producto.get('precio_venta', 0)
                                margen = precio_venta - costo_total if precio_venta > 0 else 0
                                margen_pct = (margen / precio_venta * 100) if precio_venta > 0 else 0
                                
                                st.write("---")
                                st.write(f"💰 **Costo producción:** ${costo_total:,.2f}")
                                st.write(f"💵 **Precio venta:** ${precio_venta:,.2f}")
                                st.write(f"📈 **Margen:** ${margen:,.2f} ({margen_pct:.1f}%)")
                        
                        # Botón para eliminar
                        if st.button(f"🗑️ Eliminar {producto['nombre']}", key=f"del_{producto['id']}"):
                            supabase.table('productos').delete().eq('id', producto['id']).execute()
                            st.success(f"Producto {producto['nombre']} eliminado")
                            st.rerun()
            else:
                st.info("No tenés productos registrados. ¡Creá el primero en la pestaña de al lado!")
        
        except Exception as e:
            st.error(f"Error al cargar productos: {str(e)}")
    
    with tab2:
        # Formulario para crear producto
        st.subheader("Crear Nuevo Producto")
        
        with st.form("nuevo_producto"):
            nombre = st.text_input("Nombre del Producto*", placeholder="Ej: Alfajor de Chocolate")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.text_input("Tipo", placeholder="Ej: alfajor, tarta, brownie")
                precio_venta = st.number_input("Precio de Venta", min_value=0.0, step=10.0)
            
            with col2:
                costo_embalaje = st.number_input("Costo de Embalaje", min_value=0.0, step=1.0)
                descripcion = st.text_area("Descripción (opcional)")
            
            st.write("---")
            st.subheader("Ingredientes de la Receta")
            
            # Obtener lista de ingredientes disponibles
            try:
                ingredientes_disponibles = supabase.table('ingredientes').select('nombre, unidad').eq('user_id', user_id).execute()
                lista_ingredientes = [f"{ing['nombre']} ({ing['unidad']})" for ing in ingredientes_disponibles.data] if ingredientes_disponibles.data else []
            except:
                lista_ingredientes = []
            
            # Permitir agregar múltiples ingredientes
            num_ingredientes = st.number_input("¿Cuántos ingredientes tiene?", min_value=1, max_value=20, value=3, step=1)
            
            ingredientes_receta = []
            for i in range(int(num_ingredientes)):
                st.write(f"**Ingrediente {i+1}:**")
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    if lista_ingredientes:
                        ing_seleccionado = st.selectbox(
                            "Ingrediente", 
                            lista_ingredientes, 
                            key=f"ing_{i}",
                            label_visibility="collapsed"
                        )
                        nombre_ing = ing_seleccionado.split(" (")[0]  # Extraer solo el nombre
                    else:
                        nombre_ing = st.text_input("Nombre ingrediente", key=f"ing_nombre_{i}", label_visibility="collapsed")
                
                with col2:
                    cantidad = st.number_input("Cantidad", min_value=0.0, step=0.1, key=f"cant_{i}", label_visibility="collapsed")
                
                with col3:
                    unidad = st.selectbox("Unidad", ["gr", "kg", "un", "ml", "l"], key=f"unidad_{i}", label_visibility="collapsed")
                
                if cantidad > 0:
                    ingredientes_receta.append({
                        'nombre': nombre_ing,
                        'cantidad': cantidad,
                        'unidad': unidad
                    })
            
            submitted = st.form_submit_button("✅ Crear Producto", type="primary")
            
            if submitted:
                if not nombre:
                    st.error("El nombre del producto es obligatorio")
                elif not ingredientes_receta:
                    st.error("Debés agregar al menos un ingrediente")
                else:
                    try:
                        # Crear producto
                        producto_data = {
                            'user_id': user_id,
                            'nombre': nombre,
                            'tipo': tipo if tipo else None,
                            'descripcion': descripcion if descripcion else None,
                            'precio_venta': precio_venta,
                            'costo_embalaje': costo_embalaje,
                            'activo': True
                        }
                        
                        response = supabase.table('productos').insert(producto_data).execute()
                        producto_id = response.data[0]['id']
                        
                        # Crear recetas
                        for ing in ingredientes_receta:
                            receta_data = {
                                'producto_id': producto_id,
                                'ingrediente_nombre': ing['nombre'],
                                'cantidad': ing['cantidad'],
                                'unidad': ing['unidad']
                            }
                            supabase.table('recetas').insert(receta_data).execute()
                        
                        st.success(f"✅ Producto '{nombre}' creado exitosamente con {len(ingredientes_receta)} ingredientes!")
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error al crear producto: {str(e)}")

def mostrar_finanzas():
    """Análisis financiero"""
    st.title("💰 Análisis Financiero")
    st.info("🚧 En desarrollo")
    # TODO: Implementar costos, márgenes, reportes
def registrar_compra(user_id, fecha, ingrediente, cantidad, unidad, total, costo_unitario, proveedor):
    """Registra una compra Y actualiza el stock + precio UEPS"""
    try:
        # 1. Registrar la compra en historial
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
        
        # 2. Actualizar stock del ingrediente
        # Buscar si el ingrediente existe
        ing_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente).execute()
        
        if ing_response.data:
            # Existe → actualizar
            ing_actual = ing_response.data[0]
            nuevo_stock = ing_actual['stock_actual'] + cantidad
            nuevo_comprado = ing_actual['comprado'] + cantidad
            
            supabase.table('ingredientes').update({
                'stock_actual': nuevo_stock,
                'comprado': nuevo_comprado,
                'costo_unitario': costo_unitario,  # UEPS: último precio
                'precio_compra': total,
                'cantidad_compra': cantidad
            }).eq('id', ing_actual['id']).execute()
        else:
            # No existe → crear
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
    """Obtener historial de compras"""
    response = supabase.table('compras').select('*').eq('user_id', user_id).order('fecha', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def mostrar_compras():
    """Sección mejorada de compras"""
    st.title("🛒 Compras de Insumos")
    
    user_id = st.session_state.get('user_id')
    
    tab1, tab2 = st.tabs(["➕ Registrar Compra", "📋 Historial"])
    
    with tab1:
        st.subheader("Nueva Compra de Insumos")
        
        with st.form("nueva_compra"):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("Fecha de Compra", value=date.today())
                
                # Obtener ingredientes existentes
                try:
                    ings = supabase.table('ingredientes').select('nombre, unidad').eq('user_id', user_id).execute()
                    lista_ings = [ing['nombre'] for ing in ings.data] if ings.data else []
                except:
                    lista_ings = []
                
                # Opción: seleccionar existente o agregar nuevo
                usar_existente = st.checkbox("Usar ingrediente existente", value=True if lista_ings else False)
                
                if usar_existente and lista_ings:
                    ingrediente = st.selectbox("Ingrediente", lista_ings)
                    # Obtener unidad del ingrediente
                    ing_data = supabase.table('ingredientes').select('unidad').eq('user_id', user_id).eq('nombre', ingrediente).execute()
                    unidad = ing_data.data[0]['unidad'] if ing_data.data else 'gr'
                    st.info(f"Unidad: {unidad}")
                else:
                    ingrediente = st.text_input("Nombre del Ingrediente")
                    unidad = st.selectbox("Unidad", ["gr", "kg", "un", "ml", "l", "lata"])
            
            with col2:
                cantidad = st.number_input("Cantidad Comprada", min_value=0.0, step=1.0)
                total = st.number_input("Total Pagado ($)", min_value=0.0, step=1.0)
                proveedor = st.text_input("Proveedor (opcional)")
            
            # Calcular costo unitario automáticamente
            if cantidad > 0 and total > 0:
                costo_unitario = total / cantidad
                st.info(f"💰 Costo unitario: ${costo_unitario:.2f} por {unidad}")
            else:
                costo_unitario = 0
            
            submitted = st.form_submit_button("✅ Registrar Compra", type="primary")
            
            if submitted:
                if not ingrediente or cantidad <= 0:
                    st.error("Completá todos los campos obligatorios")
                else:
                    success, mensaje = registrar_compra(
                        user_id, fecha, ingrediente, cantidad, unidad, 
                        total, costo_unitario, proveedor
                    )
                    
                    if success:
                        st.success(mensaje)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(mensaje)
    
    with tab2:
        st.subheader("Historial de Compras")
        
        df = obtener_compras(user_id)
        
        if not df.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                if 'ingrediente' in df.columns:
                    ingredientes_unicos = ['Todos'] + sorted(df['ingrediente'].unique().tolist())
                    filtro_ing = st.selectbox("Filtrar por ingrediente", ingredientes_unicos)
            
            with col2:
                if 'fecha' in df.columns:
                    fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
            
            # Aplicar filtros
            df_filtrado = df.copy()
            if filtro_ing != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['ingrediente'] == filtro_ing]
            
            if 'fecha' in df_filtrado.columns:
                df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
                df_filtrado = df_filtrado[df_filtrado['fecha'] >= pd.Timestamp(fecha_desde)]
            
            # Mostrar métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Compras", len(df_filtrado))
            with col2:
                total_gastado = df_filtrado['total'].sum() if 'total' in df_filtrado.columns else 0
                st.metric("Total Gastado", f"${total_gastado:,.2f}")
            with col3:
                ingredientes_distintos = df_filtrado['ingrediente'].nunique() if 'ingrediente' in df_filtrado.columns else 0
                st.metric("Ingredientes Distintos", ingredientes_distintos)
            
            # Tabla
            st.dataframe(
                df_filtrado[['fecha', 'ingrediente', 'cantidad', 'unidad', 'total', 'costo_unitario', 'proveedor']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay compras registradas. ¡Registrá la primera!")
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
