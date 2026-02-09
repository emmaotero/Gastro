"""
App de Gestión para Pastelerías - VERSIÓN MEJORADA
Con edición, conversión de unidades y exportación a Excel
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import pandas as pd
import io

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

SUPABASE_URL = "TU_SUPABASE_URL"
SUPABASE_KEY = "TU_SUPABASE_ANON_KEY"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# =============================================================================
# UTILIDADES - CONVERSIÓN DE UNIDADES
# =============================================================================

def normalizar_unidad(cantidad, unidad_origen, unidad_destino):
    """Convierte entre unidades compatibles"""
    # Conversiones de peso
    conversiones_peso = {
        ('kg', 'gr'): 1000,
        ('gr', 'kg'): 0.001,
        ('kg', 'kg'): 1,
        ('gr', 'gr'): 1
    }
    
    # Conversiones de volumen
    conversiones_volumen = {
        ('l', 'ml'): 1000,
        ('ml', 'l'): 0.001,
        ('l', 'l'): 1,
        ('ml', 'ml'): 1
    }
    
    # Intentar conversión
    if (unidad_origen, unidad_destino) in conversiones_peso:
        return cantidad * conversiones_peso[(unidad_origen, unidad_destino)]
    elif (unidad_origen, unidad_destino) in conversiones_volumen:
        return cantidad * conversiones_volumen[(unidad_origen, unidad_destino)]
    else:
        # Si no son compatibles, devolver sin cambios
        return cantidad

def unidades_compatibles(unidad1, unidad2):
    """Verifica si dos unidades son compatibles para conversión"""
    pesos = ['gr', 'kg']
    volumenes = ['ml', 'l']
    
    return (unidad1 in pesos and unidad2 in pesos) or \
           (unidad1 in volumenes and unidad2 in volumenes) or \
           unidad1 == unidad2

# =============================================================================
# UTILIDADES - EXPORTACIÓN
# =============================================================================

def exportar_a_excel(df, nombre_hoja):
    """Exporta un DataFrame a Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=nombre_hoja, index=False)
    output.seek(0)
    return output

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
            
            if estado == 'suspendido':
                return False, "Tu cuenta ha sido suspendida. Contacta al administrador."
            
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
    """Registro de nuevo usuario"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            supabase.table('users').insert({
                'id': response.user.id,
                'email': email,
                'nombre_negocio': nombre_negocio,
                'nombre_contacto': nombre_contacto,
                'telefono': telefono,
                'estado': 'prueba'
            }).execute()
            
            return True, "Registro exitoso. Tu cuenta está pendiente de aprobación."
        return False, "Error al crear usuario"
    except Exception as e:
        return False, f"Error en registro: {str(e)}"

# =============================================================================
# INTERFAZ DE LOGIN
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
# FUNCIONES DE NEGOCIO - INVENTARIO
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
            'costo_unitario': costo_unitario,
            'comprado': 0,
            'consumido': 0
        }).execute()
        return True, "Ingrediente agregado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def actualizar_ingrediente(ingrediente_id, nombre, unidad, stock_actual, costo_unitario):
    """Actualizar un ingrediente existente"""
    try:
        supabase.table('ingredientes').update({
            'nombre': nombre,
            'unidad': unidad,
            'stock_actual': stock_actual,
            'costo_unitario': costo_unitario
        }).eq('id', ingrediente_id).execute()
        return True, "Ingrediente actualizado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_ingrediente(ingrediente_id):
    """Eliminar un ingrediente"""
    try:
        supabase.table('ingredientes').delete().eq('id', ingrediente_id).execute()
        return True, "Ingrediente eliminado"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# FUNCIONES DE NEGOCIO - COMPRAS
# =============================================================================

def registrar_compra(user_id, fecha, ingrediente, cantidad, unidad, total, costo_unitario, proveedor):
    """Registra una compra Y actualiza el stock + precio UEPS"""
    try:
        # 1. Registrar compra
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
        
        # 2. Actualizar o crear ingrediente
        ing_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente).execute()
        
        if ing_response.data:
            # Existe - actualizar
            ing_actual = ing_response.data[0]
            unidad_ing = ing_actual['unidad']
            
            # Convertir unidades si es necesario
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
            # No existe - crear
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

def actualizar_compra(compra_id, fecha, ingrediente, cantidad, unidad, total, costo_unitario, proveedor):
    """Actualizar una compra existente"""
    try:
        supabase.table('compras').update({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'ingrediente': ingrediente,
            'cantidad': cantidad,
            'unidad': unidad,
            'total': total,
            'costo_unitario': costo_unitario,
            'proveedor': proveedor
        }).eq('id', compra_id).execute()
        return True, "Compra actualizada"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_compra(compra_id):
    """Eliminar una compra"""
    try:
        supabase.table('compras').delete().eq('id', compra_id).execute()
        return True, "Compra eliminada"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# FUNCIONES DE NEGOCIO - PEDIDOS
# =============================================================================

def registrar_pedido_con_descuento(user_id, fecha, producto_nombre, cantidad, tipo, precio_unitario, cliente):
    """Registra pedido Y descuenta ingredientes del stock según receta"""
    try:
        # 1. Buscar producto
        producto_response = supabase.table('productos').select('*').eq('user_id', user_id).eq('nombre', producto_nombre).execute()
        
        if not producto_response.data:
            return False, f"Producto '{producto_nombre}' no encontrado."
        
        producto = producto_response.data[0]
        producto_id = producto['id']
        
        # 2. Obtener receta
        receta_response = supabase.table('recetas').select('*').eq('producto_id', producto_id).execute()
        
        if not receta_response.data:
            return False, f"El producto '{producto_nombre}' no tiene receta."
        
        # 3. Verificar stock
        faltantes = []
        for ingrediente in receta_response.data:
            cantidad_necesaria = ingrediente['cantidad'] * cantidad
            
            stock_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente['ingrediente_nombre']).execute()
            
            if stock_response.data:
                ing_actual = stock_response.data[0]
                stock_actual = ing_actual['stock_actual']
                unidad_ing = ing_actual['unidad']
                
                # Convertir si es necesario
                cantidad_convertida = normalizar_unidad(cantidad_necesaria, ingrediente['unidad'], unidad_ing)
                
                if stock_actual < cantidad_convertida:
                    faltantes.append(f"{ingrediente['ingrediente_nombre']}: necesitás {cantidad_convertida:.2f} {unidad_ing}, tenés {stock_actual:.2f}")
            else:
                faltantes.append(f"{ingrediente['ingrediente_nombre']}: no está en inventario")
        
        if faltantes:
            return False, "Stock insuficiente:\n" + "\n".join(faltantes)
        
        # 4. Registrar pedido
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
        
        # 5. Descontar stock
        for ingrediente in receta_response.data:
            cantidad_a_descontar = ingrediente['cantidad'] * cantidad
            
            ing_response = supabase.table('ingredientes').select('*').eq('user_id', user_id).eq('nombre', ingrediente['ingrediente_nombre']).execute()
            
            if ing_response.data:
                ing_actual = ing_response.data[0]
                unidad_ing = ing_actual['unidad']
                
                # Convertir si es necesario
                cantidad_convertida = normalizar_unidad(cantidad_a_descontar, ingrediente['unidad'], unidad_ing)
                
                nuevo_stock = ing_actual['stock_actual'] - cantidad_convertida
                nuevo_consumido = ing_actual['consumido'] + cantidad_convertida
                
                supabase.table('ingredientes').update({
                    'stock_actual': nuevo_stock,
                    'consumido': nuevo_consumido
                }).eq('id', ing_actual['id']).execute()
        
        return True, f"Pedido registrado y stock actualizado ({cantidad} unidades de {producto_nombre})."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def obtener_pedidos(user_id):
    """Obtener pedidos"""
    response = supabase.table('pedidos').select('*').eq('user_id', user_id).order('fecha', desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def actualizar_pedido(pedido_id, fecha, producto, cantidad, tipo, precio_unitario, cliente):
    """Actualizar un pedido"""
    try:
        total = precio_unitario * cantidad if precio_unitario else None
        supabase.table('pedidos').update({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'producto': producto,
            'cantidad': cantidad,
            'tipo': tipo,
            'precio_unitario': precio_unitario,
            'total': total,
            'cliente': cliente
        }).eq('id', pedido_id).execute()
        return True, "Pedido actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_pedido(pedido_id):
    """Eliminar un pedido"""
    try:
        supabase.table('pedidos').delete().eq('id', pedido_id).execute()
        return True, "Pedido eliminado"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# FUNCIONES DE NEGOCIO - PRODUCTOS
# =============================================================================

def actualizar_producto(producto_id, nombre, tipo, precio_venta, costo_embalaje, descripcion):
    """Actualizar un producto"""
    try:
        supabase.table('productos').update({
            'nombre': nombre,
            'tipo': tipo,
            'precio_venta': precio_venta,
            'costo_embalaje': costo_embalaje,
            'descripcion': descripcion
        }).eq('id', producto_id).execute()
        return True, "Producto actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"

# =============================================================================
# INTERFAZ PRINCIPAL
# =============================================================================

def mostrar_app_principal():
    """Interfaz principal"""
    
    with st.sidebar:
        st.title("🍰 Mi Pastelería")
        st.write(f"**Usuario:** {st.session_state.get('email', '')}")
        if st.button("Cerrar Sesión", type="secondary"):
            logout()
        
        st.divider()
        
        pagina = st.radio(
            "Navegación",
            ["📊 Dashboard", "🧺 Inventario", "🛒 Compras", "📦 Pedidos", "🍪 Productos", "💵 Calculadora Precios", "💰 Finanzas"]
        )
    
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
    elif pagina == "💵 Calculadora Precios":
        mostrar_calculadora_precios()
    elif pagina == "💰 Finanzas":
        mostrar_finanzas()

def mostrar_dashboard():
    """Dashboard principal"""
    st.title("📊 Dashboard")
    st.write("¡Bienvenido a tu sistema de gestión!")
    
    user_id = st.session_state.get('user_id')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ingredientes", len(obtener_ingredientes(user_id)))
    
    with col2:
        df_pedidos = obtener_pedidos(user_id)
        st.metric("Pedidos este mes", len(df_pedidos))
    
    with col3:
        try:
            productos = supabase.table('productos').select('*', count='exact').eq('user_id', user_id).execute()
            st.metric("Productos activos", productos.count if productos.count else 0)
        except:
            st.metric("Productos activos", 0)
    
    with col4:
        df_compras = obtener_compras(user_id)
        total_compras = df_compras['total'].sum() if not df_compras.empty and 'total' in df_compras.columns else 0
        st.metric("Invertido en stock", f"${total_compras:,.0f}")

def mostrar_inventario():
    """Gestión de inventario CON EDICIÓN"""
    st.title("🧺 Inventario de Ingredientes")
    
    user_id = st.session_state.get('user_id')
    
    # Botón de exportar
    df_all = obtener_ingredientes(user_id)
    if not df_all.empty:
        excel_file = exportar_a_excel(df_all, "Inventario")
        st.download_button(
            label="📥 Exportar Inventario a Excel",
            data=excel_file,
            file_name=f"inventario_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Agregar nuevo
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
    
    # Listar y editar
    st.subheader("Ingredientes Registrados")
    df = obtener_ingredientes(user_id)
    
    if not df.empty:
        for idx, row in df.iterrows():
            with st.expander(f"📦 {row['nombre']} - Stock: {row['stock_actual']} {row['unidad']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Modo edición
                    edit_nombre = st.text_input("Nombre", value=row['nombre'], key=f"edit_nombre_{row['id']}")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        edit_unidad = st.selectbox("Unidad", ["gr", "kg", "un", "lata", "ml", "l"], 
                                                   index=["gr", "kg", "un", "lata", "ml", "l"].index(row['unidad']) if row['unidad'] in ["gr", "kg", "un", "lata", "ml", "l"] else 0,
                                                   key=f"edit_unidad_{row['id']}")
                    with col_b:
                        edit_stock = st.number_input("Stock", value=float(row['stock_actual']), step=0.1, key=f"edit_stock_{row['id']}")
                    with col_c:
                        edit_costo = st.number_input("Costo", value=float(row['costo_unitario']), step=0.01, key=f"edit_costo_{row['id']}")
                
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("💾 Guardar", key=f"save_{row['id']}", type="primary"):
                        success, mensaje = actualizar_ingrediente(row['id'], edit_nombre, edit_unidad, edit_stock, edit_costo)
                        if success:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
                    
                    if st.button("🗑️ Eliminar", key=f"del_ing_{row['id']}"):
                        success, mensaje = eliminar_ingrediente(row['id'])
                        if success:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
    else:
        st.info("No hay ingredientes. ¡Agrega el primero!")

def mostrar_compras():
    """Compras CON EDICIÓN"""
    st.title("🛒 Compras de Insumos")
    
    user_id = st.session_state.get('user_id')
    
    tab1, tab2 = st.tabs(["➕ Registrar Compra", "📋 Historial"])
    
    with tab1:
        st.subheader("Nueva Compra")
        
        with st.form("nueva_compra"):
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
                    st.info(f"Unidad: {unidad}")
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        ingrediente = st.text_input("Ingrediente nuevo")
                    with col_b:
                        unidad = st.selectbox("Unidad", ["gr", "kg", "un", "ml", "l", "lata"])
            
            with col2:
                cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0)
                total = st.number_input("Total ($)", min_value=0.0, step=1.0)
                proveedor = st.text_input("Proveedor (opcional)")
            
            if cantidad > 0 and total > 0:
                costo_unitario = total / cantidad
                st.info(f"💰 Costo unitario: ${costo_unitario:.2f} por {unidad}")
            else:
                costo_unitario = 0
            
            submitted = st.form_submit_button("✅ Registrar", type="primary")
            
            if submitted:
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
        st.subheader("Historial de Compras")
        
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
            
            # Mostrar con opción de editar
            for idx, row in df.head(20).iterrows():  # Mostrar últimas 20
                with st.expander(f"🛒 {row['fecha']} - {row['ingrediente']} ({row['cantidad']} {row['unidad']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        edit_fecha = st.date_input("Fecha", value=pd.to_datetime(row['fecha']).date(), key=f"comp_fecha_{row['id']}")
                        edit_ing = st.text_input("Ingrediente", value=row['ingrediente'], key=f"comp_ing_{row['id']}")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            edit_cant = st.number_input("Cantidad", value=float(row['cantidad']), key=f"comp_cant_{row['id']}")
                        with col_b:
                            edit_unidad = st.selectbox("Unidad", ["gr", "kg", "un", "ml", "l"], 
                                                       index=["gr", "kg", "un", "ml", "l"].index(row['unidad']) if row['unidad'] in ["gr", "kg", "un", "ml", "l"] else 0,
                                                       key=f"comp_unidad_{row['id']}")
                        with col_c:
                            edit_total = st.number_input("Total", value=float(row['total']) if pd.notna(row['total']) else 0.0, key=f"comp_total_{row['id']}")
                        
                        edit_prov = st.text_input("Proveedor", value=row.get('proveedor', ''), key=f"comp_prov_{row['id']}")
                    
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("💾 Guardar", key=f"save_comp_{row['id']}", type="primary"):
                            costo_unit = edit_total / edit_cant if edit_cant > 0 else 0
                            success, mensaje = actualizar_compra(row['id'], edit_fecha, edit_ing, edit_cant, edit_unidad, edit_total, costo_unit, edit_prov)
                            if success:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        
                        if st.button("🗑️", key=f"del_comp_{row['id']}"):
                            success, mensaje = eliminar_compra(row['id'])
                            if success:
                                st.success(mensaje)
                                st.rerun()
        else:
            st.info("No hay compras")

def mostrar_pedidos():
    """Pedidos CON EDICIÓN"""
    st.title("📦 Pedidos")
    
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
            st.warning("⚠️ Creá productos primero en la sección Productos.")
            return
        
        with st.form("nuevo_pedido"):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("Fecha", value=date.today())
                producto = st.selectbox("Producto", lista_productos)
                cantidad = st.number_input("Cantidad", min_value=1, step=1)
            
            with col2:
                tipo = st.selectbox("Tipo", ["Venta", "Regalo", "Muestra"])
                precio_unitario = st.number_input("Precio Unitario", min_value=0.0, step=10.0)
                cliente = st.text_input("Cliente (opcional)")
            
            if producto:
                try:
                    prod_data = supabase.table('productos').select('*').eq('user_id', user_id).eq('nombre', producto).execute()
                    if prod_data.data:
                        precio_sugerido = prod_data.data[0].get('precio_venta', 0)
                        st.info(f"💡 Precio sugerido: ${precio_sugerido:,.2f}")
                except:
                    pass
            
            submitted = st.form_submit_button("✅ Registrar Pedido", type="primary")
            
            if submitted:
                if not producto or cantidad <= 0:
                    st.error("Completá campos obligatorios")
                else:
                    with st.spinner("Procesando..."):
                        success, mensaje = registrar_pedido_con_descuento(user_id, fecha, producto, cantidad, tipo.lower(), precio_unitario, cliente)
                        if success:
                            st.success(mensaje)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(mensaje)
    
    with tab2:
        st.subheader("Historial")
        df = obtener_pedidos(user_id)
        
        if not df.empty:
            # Exportar
            excel_file = exportar_a_excel(df, "Pedidos")
            st.download_button(
                label="📥 Exportar a Excel",
                data=excel_file,
                file_name=f"pedidos_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Mostrar con opción de editar
            for idx, row in df.head(20).iterrows():
                with st.expander(f"📦 {row['fecha']} - {row['producto']} (x{row['cantidad']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        edit_fecha = st.date_input("Fecha", value=pd.to_datetime(row['fecha']).date(), key=f"ped_fecha_{row['id']}")
                        edit_prod = st.text_input("Producto", value=row['producto'], key=f"ped_prod_{row['id']}")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            edit_cant = st.number_input("Cantidad", value=int(row['cantidad']), key=f"ped_cant_{row['id']}")
                        with col_b:
                            edit_tipo = st.selectbox("Tipo", ["venta", "regalo", "muestra"], 
                                                     index=["venta", "regalo", "muestra"].index(row['tipo']) if row['tipo'] in ["venta", "regalo", "muestra"] else 0,
                                                     key=f"ped_tipo_{row['id']}")
                        with col_c:
                            edit_precio = st.number_input("Precio Unit.", value=float(row['precio_unitario']) if pd.notna(row['precio_unitario']) else 0.0, key=f"ped_precio_{row['id']}")
                        
                        edit_cliente = st.text_input("Cliente", value=row.get('cliente', ''), key=f"ped_cliente_{row['id']}")
                    
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("💾 Guardar", key=f"save_ped_{row['id']}", type="primary"):
                            success, mensaje = actualizar_pedido(row['id'], edit_fecha, edit_prod, edit_cant, edit_tipo, edit_precio, edit_cliente)
                            if success:
                                st.success(mensaje)
                                st.rerun()
                            else:
                                st.error(mensaje)
                        
                        if st.button("🗑️", key=f"del_ped_{row['id']}"):
                            success, mensaje = eliminar_pedido(row['id'])
                            if success:
                                st.success(mensaje)
                                st.rerun()
        else:
            st.info("No hay pedidos")

def mostrar_productos():
    """Productos CON EDICIÓN"""
    st.title("🍪 Productos y Recetas")
    
    user_id = st.session_state.get('user_id')
    
    tab1, tab2 = st.tabs(["📋 Mis Productos", "➕ Crear Producto"])
    
    with tab1:
        st.subheader("Productos Registrados")
        
        try:
            response = supabase.table('productos').select('*').eq('user_id', user_id).eq('activo', True).execute()
            
            if response.data:
                for producto in response.data:
                    with st.expander(f"🍰 {producto['nombre']}"):
                        # Modo lectura/edición
                        if f"edit_mode_{producto['id']}" not in st.session_state:
                            st.session_state[f"edit_mode_{producto['id']}"] = False
                        
                        edit_mode = st.session_state[f"edit_mode_{producto['id']}"]
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if edit_mode:
                                # Modo edición
                                edit_nombre = st.text_input("Nombre", value=producto['nombre'], key=f"prod_nombre_{producto['id']}")
                                edit_tipo = st.text_input("Tipo", value=producto.get('tipo', ''), key=f"prod_tipo_{producto['id']}")
                                edit_precio = st.number_input("Precio venta", value=float(producto.get('precio_venta', 0)), key=f"prod_precio_{producto['id']}")
                                edit_embalaje = st.number_input("Costo embalaje", value=float(producto.get('costo_embalaje', 0)), key=f"prod_emb_{producto['id']}")
                                edit_desc = st.text_area("Descripción", value=producto.get('descripcion', ''), key=f"prod_desc_{producto['id']}")
                            else:
                                # Modo lectura
                                st.write(f"**Tipo:** {producto.get('tipo', 'N/A')}")
                                st.write(f"**Precio de venta:** ${producto.get('precio_venta', 0):,.2f}")
                                st.write(f"**Costo embalaje:** ${producto.get('costo_embalaje', 0):,.2f}")
                                if producto.get('descripcion'):
                                    st.write(f"**Descripción:** {producto['descripcion']}")
                        
                        with col2:
                            if edit_mode:
                                if st.button("💾 Guardar", key=f"save_prod_{producto['id']}", type="primary"):
                                    success, mensaje = actualizar_producto(producto['id'], edit_nombre, edit_tipo, edit_precio, edit_embalaje, edit_desc)
                                    if success:
                                        st.success(mensaje)
                                        st.session_state[f"edit_mode_{producto['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                                
                                if st.button("❌ Cancelar", key=f"cancel_prod_{producto['id']}"):
                                    st.session_state[f"edit_mode_{producto['id']}"] = False
                                    st.rerun()
                            else:
                                if st.button("✏️ Editar", key=f"edit_prod_{producto['id']}"):
                                    st.session_state[f"edit_mode_{producto['id']}"] = True
                                    st.rerun()
                                
                                if st.button("🗑️ Eliminar", key=f"del_prod_{producto['id']}"):
                                    supabase.table('productos').delete().eq('id', producto['id']).execute()
                                    st.success("Producto eliminado")
                                    st.rerun()
                        
                        # Mostrar receta e info adicional
                        if not edit_mode:
                            receta_response = supabase.table('recetas').select('*').eq('producto_id', producto['id']).execute()
                            
                            if receta_response.data:
                                st.write("---")
                                st.write("**Ingredientes:**")
                                for ingrediente in receta_response.data:
                                    st.write(f"- {ingrediente['ingrediente_nombre']}: {ingrediente['cantidad']} {ingrediente['unidad']}")
                                
                                # Calcular costo
                                costo_total = 0
                                for ing in receta_response.data:
                                    ing_data = supabase.table('ingredientes').select('costo_unitario, unidad').eq('user_id', user_id).eq('nombre', ing['ingrediente_nombre']).execute()
                                    if ing_data.data:
                                        costo_unitario = ing_data.data[0].get('costo_unitario', 0)
                                        unidad_ing = ing_data.data[0].get('unidad', ing['unidad'])
                                        
                                        # Convertir si es necesario
                                        cantidad_convertida = normalizar_unidad(ing['cantidad'], ing['unidad'], unidad_ing)
                                        costo_total += cantidad_convertida * costo_unitario
                                
                                costo_total += producto.get('costo_embalaje', 0)
                                precio_venta = producto.get('precio_venta', 0)
                                margen = precio_venta - costo_total if precio_venta > 0 else 0
                                margen_pct = (margen / precio_venta * 100) if precio_venta > 0 else 0
                                
                                st.write("---")
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("💰 Costo", f"${costo_total:,.2f}")
                                with col_b:
                                    st.metric("💵 Precio", f"${precio_venta:,.2f}")
                                with col_c:
                                    st.metric("📈 Margen", f"{margen_pct:.1f}%")
            else:
                st.info("No tenés productos. ¡Creá el primero!")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Crear Nuevo Producto")
        
        with st.form("nuevo_producto"):
            nombre = st.text_input("Nombre*")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.text_input("Tipo")
                precio_venta = st.number_input("Precio de Venta", min_value=0.0, step=10.0)
            with col2:
                costo_embalaje = st.number_input("Costo Embalaje", min_value=0.0, step=1.0)
                descripcion = st.text_area("Descripción (opcional)")
            
            st.write("---")
            st.subheader("Ingredientes")
            
            try:
                ingredientes_disponibles = supabase.table('ingredientes').select('nombre, unidad').eq('user_id', user_id).execute()
                lista_ingredientes = [f"{ing['nombre']} ({ing['unidad']})" for ing in ingredientes_disponibles.data] if ingredientes_disponibles.data else []
            except:
                lista_ingredientes = []
            
            num_ingredientes = st.number_input("¿Cuántos ingredientes?", min_value=1, max_value=20, value=3, step=1)
            
            ingredientes_receta = []
            for i in range(int(num_ingredientes)):
                st.write(f"**Ingrediente {i+1}:**")
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    if lista_ingredientes:
                        ing_seleccionado = st.selectbox("Ingrediente", lista_ingredientes, key=f"ing_{i}", label_visibility="collapsed")
                        nombre_ing = ing_seleccionado.split(" (")[0]
                    else:
                        nombre_ing = st.text_input("Ingrediente", key=f"ing_nombre_{i}", label_visibility="collapsed")
                
                with col2:
                    cantidad = st.number_input("Cantidad", min_value=0.0, step=0.1, key=f"cant_{i}", label_visibility="collapsed")
                with col3:
                    unidad = st.selectbox("Unidad", ["gr", "kg", "un", "ml", "l"], key=f"unidad_{i}", label_visibility="collapsed")
                
                if cantidad > 0:
                    ingredientes_receta.append({'nombre': nombre_ing, 'cantidad': cantidad, 'unidad': unidad})
            
            submitted = st.form_submit_button("✅ Crear Producto", type="primary")
            
            if submitted:
                if not nombre:
                    st.error("El nombre es obligatorio")
                elif not ingredientes_receta:
                    st.error("Agregá al menos un ingrediente")
                else:
                    try:
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
                        
                        for ing in ingredientes_receta:
                            receta_data = {
                                'producto_id': producto_id,
                                'ingrediente_nombre': ing['nombre'],
                                'cantidad': ing['cantidad'],
                                'unidad': ing['unidad']
                            }
                            supabase.table('recetas').insert(receta_data).execute()
                        
                        st.success(f"✅ Producto '{nombre}' creado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

def mostrar_calculadora_precios():
    """Calculadora de precios y márgenes"""
    st.title("💵 Calculadora de Precios")
    st.write("Calculá el precio de venta ideal según tus costos y margen deseado")
    
    user_id = st.session_state.get('user_id')
    
    # Obtener productos
    try:
        productos_response = supabase.table('productos').select('*').eq('user_id', user_id).eq('activo', True).execute()
        productos = productos_response.data if productos_response.data else []
    except:
        productos = []
    
    if not productos:
        st.warning("No tenés productos creados. Andá a la sección Productos para crear uno.")
        return
    
    # Selector de producto
    nombres_productos = [p['nombre'] for p in productos]
    producto_seleccionado = st.selectbox("Seleccioná un producto:", nombres_productos)
    
    # Obtener datos del producto
    producto = next((p for p in productos if p['nombre'] == producto_seleccionado), None)
    
    if producto:
        st.write("---")
        
        # Calcular costo base
        receta_response = supabase.table('recetas').select('*').eq('producto_id', producto['id']).execute()
        
        costo_ingredientes = 0
        if receta_response.data:
            for ing in receta_response.data:
                ing_data = supabase.table('ingredientes').select('costo_unitario, unidad').eq('user_id', user_id).eq('nombre', ing['ingrediente_nombre']).execute()
                if ing_data.data:
                    costo_unitario = ing_data.data[0].get('costo_unitario', 0)
                    unidad_ing = ing_data.data[0].get('unidad', ing['unidad'])
                    cantidad_convertida = normalizar_unidad(ing['cantidad'], ing['unidad'], unidad_ing)
                    costo_ingredientes += cantidad_convertida * costo_unitario
        
        costo_embalaje = producto.get('costo_embalaje', 0)
        
        # Inputs adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Costos")
            st.metric("Costo Ingredientes", f"${costo_ingredientes:,.2f}")
            st.metric("Costo Embalaje", f"${costo_embalaje:,.2f}")
            
            costos_extras = st.number_input(
                "Costos Extras (luz, gas, mano de obra, etc.)",
                min_value=0.0,
                step=10.0,
                help="Agregá cualquier costo adicional que quieras incluir"
            )
            
            costo_total = costo_ingredientes + costo_embalaje + costos_extras
            st.metric("**COSTO TOTAL**", f"${costo_total:,.2f}")
        
        with col2:
            st.subheader("Precio de Venta")
            
            # Opción 1: Por margen
            margen_deseado = st.slider("Margen de Ganancia (%)", min_value=0, max_value=200, value=50, step=5)
            
            precio_venta_calculado = costo_total * (1 + margen_deseado / 100)
            
            st.metric("Precio Calculado", f"${precio_venta_calculado:,.2f}")
            st.metric("Ganancia por Unidad", f"${precio_venta_calculado - costo_total:,.2f}")
            
            # Opción 2: Precio manual
            st.write("---")
            st.write("O ingresá un precio manual:")
            precio_manual = st.number_input("Precio de Venta Manual", min_value=0.0, value=precio_venta_calculado, step=10.0)
            
            if precio_manual > 0:
                margen_real = ((precio_manual - costo_total) / precio_manual * 100) if precio_manual > 0 else 0
                ganancia_real = precio_manual - costo_total
                
                st.metric("Margen Real", f"{margen_real:.1f}%")
                st.metric("Ganancia Real", f"${ganancia_real:,.2f}")
        
        # Simulador de pedido
        st.write("---")
        st.subheader("💰 Simulador de Pedido")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cantidad_pedido = st.number_input("Cantidad de unidades", min_value=1, value=10, step=1)
        
        with col2:
            precio_usar = st.radio("Usar precio:", ["Calculado", "Manual"])
            precio_final = precio_venta_calculado if precio_usar == "Calculado" else precio_manual
        
        with col3:
            st.write("")
            st.write("")
            st.metric("Precio Unitario", f"${precio_final:,.2f}")
        
        # Resultados del pedido
        costo_total_pedido = costo_total * cantidad_pedido
        ingreso_total_pedido = precio_final * cantidad_pedido
        ganancia_total_pedido = ingreso_total_pedido - costo_total_pedido
        
        st.write("### Resultado del Pedido:")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Unidades", cantidad_pedido)
        with col2:
            st.metric("Costo Total", f"${costo_total_pedido:,.2f}")
        with col3:
            st.metric("Ingreso Total", f"${ingreso_total_pedido:,.2f}")
        with col4:
            st.metric("**Ganancia**", f"${ganancia_total_pedido:,.2f}", delta=f"{((ganancia_total_pedido/costo_total_pedido)*100):.1f}%")
        
        # Botón para actualizar precio en el producto
        st.write("---")
        if st.button(f"💾 Guardar ${precio_final:,.2f} como precio de venta de '{producto['nombre']}'", type="primary"):
            try:
                supabase.table('productos').update({'precio_venta': precio_final}).eq('id', producto['id']).execute()
                st.success(f"Precio actualizado a ${precio_final:,.2f}")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def mostrar_finanzas():
    """Análisis financiero"""
    st.title("💰 Análisis Financiero")
    st.info("🚧 En desarrollo - próximamente gráficos y reportes avanzados")

# =============================================================================
# MAIN
# =============================================================================

def main():
    st.set_page_config(
        page_title="Gestión Pastelería",
        page_icon="🍰",
        layout="wide"
    )
    
    if 'user' not in st.session_state:
        mostrar_login()
    else:
        tiene_acceso, mensaje = verificar_estado_usuario(st.session_state['user_id'])
        if tiene_acceso:
            mostrar_app_principal()
        else:
            st.error(mensaje)
            st.info("Contacta al administrador")
            if st.button("Cerrar Sesión"):
                logout()

if __name__ == "__main__":
    main()
