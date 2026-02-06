# 🍰 Sistema de Gestión para Pastelerías

Sistema web gratuito para gestión de stock, pedidos, recetas y costos de producción para emprendimientos gastronómicos.

## 🎯 Características

### Para Clientes (Pastelerías)
- ✅ Gestión de inventario de ingredientes
- ✅ Registro de compras con historial
- ✅ Control de pedidos (ventas, regalos, muestras)
- ✅ Recetas con cálculo automático de costos
- ✅ Dashboard con métricas clave
- ✅ 100% gratuito para usar

### Para Administrador (Vos)
- ✅ Panel de control centralizado
- ✅ Gestión de múltiples clientes
- ✅ Control de acceso (activar/suspender)
- ✅ Gestión de suscripciones mensuales
- ✅ Estadísticas y reportes

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                   USUARIOS (Clientes)                   │
│                                                         │
│  🏪 Pastelería A    🏪 Pastelería B    🏪 Pastelería C │
└────────────┬──────────────────┬──────────────┬─────────┘
             │                  │              │
             └──────────┬───────┴──────┬───────┘
                        │              │
                   ┌────▼──────────────▼────┐
                   │   Streamlit Cloud      │
                   │   (Frontend Gratis)    │
                   └────────────┬───────────┘
                                │
                   ┌────────────▼───────────┐
                   │   Supabase             │
                   │   (Backend + DB Gratis)│
                   │   - PostgreSQL         │
                   │   - Autenticación      │
                   │   - Row Level Security │
                   └────────────────────────┘
```

## 📁 Estructura del Proyecto

```
📦 proyecto
├── 📄 app.py                    # Aplicación principal (clientes)
├── 📄 admin_panel.py            # Panel de administración
├── 📄 migrar_datos.py           # Script de migración desde Excel
├── 📄 requirements.txt          # Dependencias Python
├── 📄 GUIA_IMPLEMENTACION.md    # Guía paso a paso completa
├── 📄 database_design.md        # Diseño de base de datos
└── 📄 README.md                 # Este archivo
```

## 🚀 Quick Start

### 1. Clonar o descargar archivos
```bash
# Opción A: Si está en GitHub
git clone <tu-repo>

# Opción B: Descargar archivos directamente
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Supabase
- Seguí la `GUIA_IMPLEMENTACION.md` paso a paso
- Creá tu proyecto en Supabase
- Ejecutá los scripts SQL
- Copiá tus credenciales

### 4. Configurar variables
Editá `app.py` y `admin_panel.py`:
```python
SUPABASE_URL = "tu-url-aqui"
SUPABASE_KEY = "tu-key-aqui"
```

### 5. Ejecutar localmente
```bash
# App principal (puerto 8501)
streamlit run app.py

# Panel admin (puerto 8502)
streamlit run admin_panel.py
```

### 6. Desplegar online
- Subí a GitHub
- Conectá con Streamlit Cloud
- ¡Listo!

## 📚 Documentación

- **[GUIA_IMPLEMENTACION.md](GUIA_IMPLEMENTACION.md)** - Guía completa paso a paso
- **[database_design.md](database_design.md)** - Esquema de base de datos
- **migrar_datos.py** - Para migrar datos desde Excel existente

## 💡 Casos de Uso

### Flujo Cliente
1. Cliente se registra en la app
2. Recibe email de confirmación
3. Admin aprueba su cuenta
4. Cliente accede y gestiona su pastelería:
   - Carga ingredientes
   - Registra compras
   - Crea productos/recetas
   - Registra pedidos
   - Ve reportes de costos

### Flujo Administrador
1. Revisás nuevos registros diariamente
2. Aprobás clientes legítimos
3. Gestionás renovaciones mensuales:
   - Cliente paga → extendés suscripción
   - Cliente no paga → suspendés acceso
4. Monitoreás uso y estadísticas

## 💰 Costos

### Gratis para empezar:
- **Supabase Free Tier**
  - 50,000 usuarios activos/mes
  - 500 MB base de datos
  - 1 GB transferencia
  - Backups automáticos

- **Streamlit Cloud Free**
  - Hosting ilimitado
  - Despliegue automático
  - SSL incluido

### Cuándo pagar:
- Supabase: $25/mes cuando superes límites free
- Típicamente necesario con 100+ clientes activos simultáneos

## 🔐 Seguridad

- ✅ Autenticación segura con Supabase Auth
- ✅ Row Level Security (cada cliente ve solo sus datos)
- ✅ Contraseñas hasheadas
- ✅ HTTPS/SSL automático
- ✅ Validaciones server-side
- ✅ Control de acceso por estado de cuenta

## 🛠️ Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Backend**: Supabase
- **Base de Datos**: PostgreSQL (en Supabase)
- **Autenticación**: Supabase Auth
- **Hosting**: Streamlit Cloud
- **Lenguaje**: Python 3.9+

## 📊 Modelo de Datos

### Tablas principales:
- `users` - Datos de clientes
- `ingredientes` - Inventario por cliente
- `compras` - Historial de compras
- `productos` - Catálogo de productos
- `recetas` - Ingredientes por producto
- `pedidos` - Registro de pedidos/ventas

Ver [database_design.md](database_design.md) para el esquema completo.

## 🔄 Migración desde Excel

Si ya tenés datos en Excel (como el ejemplo de Pastelería Lupi):

```bash
python migrar_datos.py
```

El script:
1. Lee tu archivo Excel
2. Migra ingredientes, compras, pedidos
3. Crea productos y recetas
4. Preserva todo tu historial

## 🎨 Personalización

### Agregar nuevas funcionalidades:
1. Agregá columnas/tablas en Supabase
2. Actualizá las políticas RLS
3. Modificá `app.py` para la nueva UI
4. Testeá localmente
5. Desplegá

### Ejemplos de features adicionales:
- Reportes PDF
- Gráficos avanzados
- Alertas de stock bajo
- Integración WhatsApp
- Exportar a Excel
- Multi-idioma

## 🐛 Troubleshooting

### La app no se conecta a Supabase
→ Verificá URL y KEY en el código

### Usuario no puede ver sus datos
→ Revisá las políticas RLS en Supabase

### Error "User already registered"
→ El email ya existe en Auth de Supabase

### App muy lenta
→ Revisá índices en la base de datos

## 📞 Soporte

Para ayuda con la implementación:
1. Revisá la [GUIA_IMPLEMENTACION.md](GUIA_IMPLEMENTACION.md)
2. Consultá la documentación de [Supabase](https://supabase.com/docs)
3. Revisá la docs de [Streamlit](https://docs.streamlit.io)

## 🚦 Roadmap

- [x] Sistema básico de autenticación
- [x] CRUD de ingredientes
- [x] CRUD de pedidos
- [x] Panel de administrador
- [ ] Cálculo automático de costos
- [ ] Dashboard con gráficos
- [ ] Exportar reportes PDF
- [ ] Notificaciones por email
- [ ] App móvil nativa
- [ ] Integración con pagos

## 📄 Licencia

Este proyecto es de código abierto. Podés usarlo, modificarlo y distribuirlo libremente para tus clientes.

---

**Desarrollado con ❤️ para emprendimientos gastronómicos**
