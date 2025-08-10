# PsysMsql - Sistema de Gestión de Ventas 🛍️

**PsysMsql** es una aplicación web completa de gestión de ventas desarrollada con Django que permite administrar productos, stock, ventas y usuarios con diferentes roles y permisos.

## 🚀 Características Principales

### 📦 Gestión de Productos
- ✅ Registro de nuevos productos
- ✅ Visualización de todos los productos
- ✅ Actualización de información de productos
- ✅ Eliminación de productos
- ✅ Búsqueda de productos por nombre

### 📊 Control de Stock
- ✅ Gestión de inventario en tiempo real
- ✅ Registro y actualización de cantidades disponibles
- ✅ Visualización de stock actual por producto

### 💰 Sistema de Ventas
- ✅ Registro de ventas con detalles completos
- ✅ Múltiples métodos de pago
- ✅ Cálculo automático de totales
- ✅ Historial completo de ventas
- ✅ Envío automático de confirmaciones por email

### 👥 Gestión de Usuarios
- ✅ Sistema de autenticación completo
- ✅ Roles diferenciados (Administrador/Vendedor)
- ✅ Permisos específicos por funcionalidad
- ✅ Registro de nuevos usuarios
- ✅ Dashboard personalizado por rol

### 📧 Notificaciones
- ✅ Envío automático de emails de confirmación de ventas
- ✅ Procesamiento asíncrono con Celery
- ✅ Integración con Redis para cola de tareas

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2.4** - Framework web principal
- **MySQL** - Base de datos relacional
- **Celery 5.5.3** - Procesamiento asíncrono de tareas
- **Redis** - Broker de mensajes para Celery
- **django-vite** - Integración con Vite para desarrollo

### Frontend
- **Vite 6.3.5** - Build tool y servidor de desarrollo
- **TailwindCSS 4.1.6** - Framework CSS utilitario
- **JavaScript** - Funcionalidades interactivas

### Librerías Adicionales
- **phonenumber-field** - Validación de números telefónicos
- **python-dotenv** - Manejo de variables de entorno
- **mysqlclient** - Conector MySQL para Python

## 📋 Requisitos del Sistema

- Python 3.8+
- MySQL 8.0+
- Redis Server
- Node.js 16+ (para Vite)
- npm o yarn

## 🔧 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/FranciscoDJVI/work-personal.git
cd work-personal/PsysMsql
```

### 2. Configurar Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Crea un archivo `.env` en el directorio raíz del proyecto:
```env
PASSWORD_BD=tu_password_mysql
```

### 4. Configurar Base de Datos MySQL
```sql
CREATE DATABASE Psys;
CREATE USER 'tu_usuario'@'localhost' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON Psys.* TO 'tu_usuario'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Instalar Dependencias de Frontend
```bash
npm install
```

### 8. Configurar Redis (para Celery)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Descargar desde https://redis.io/download
```

## 🚀 Ejecutar la Aplicación

### 1. Iniciar el Servidor Django
```bash
python manage.py runserver
```

### 2. Iniciar Vite para Desarrollo (Terminal separada)
```bash
npm run dev
```

### 3. Iniciar Celery Worker (Terminal separada)
```bash
celery -A PsysMsql worker --loglevel=info
```

### 4. Iniciar Redis Server (Terminal separada)
```bash
redis-server
```

La aplicación estará disponible en: `http://localhost:8000`

## 👥 Roles y Permisos

### Administrador
- ✅ Acceso completo a todas las funcionalidades
- ✅ Gestión de productos (CRUD)
- ✅ Gestión de stock
- ✅ Gestión de ventas
- ✅ Gestión de usuarios
- ✅ Acceso al panel administrativo

### Vendedor
- ✅ Registro de ventas
- ✅ Consulta de productos y stock
- ✅ Envío de confirmaciones de venta
- ❌ Sin acceso a gestión de productos
- ❌ Sin acceso a gestión de usuarios

## 📊 Estructura de la Base de Datos

### Modelos Principales
- **Products**: Información de productos (nombre, precio, descripción)
- **Stock**: Control de inventario por producto
- **Sell**: Registro de ventas realizadas
- **SellProducts**: Detalles de productos vendidos
- **RegistersellDetail**: Detalles completos de cada venta
- **Clients**: Información de clientes

## 🎨 Capturas de Pantalla

### Dashboard Administrativo
*Panel principal para administradores con acceso completo*

### Gestión de Productos
*Interfaz para registrar, actualizar y eliminar productos*

### Sistema de Ventas
*Proceso completo de venta con cálculo automático de totales*

### Control de Stock
*Monitoreo en tiempo real del inventario*

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Notas de Desarrollo

### Comandos Útiles
```bash
# Crear nueva migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Compilar assets de producción
npm run build

# Ejecutar tests
python manage.py test

# Recopilar archivos estáticos
python manage.py collectstatic
```

### Configuración de Producción
Para despliegue en producción, asegúrate de:
- Cambiar `DEBUG = False` en settings.py
- Configurar `ALLOWED_HOSTS`
- Usar variables de entorno para datos sensibles
- Configurar un servidor web (Nginx + Gunicorn)
- Configurar HTTPS

## 🐛 Solución de Problemas

### Error de Conexión MySQL
- Verificar que MySQL esté ejecutándose
- Confirmar credenciales en el archivo `.env`
- Verificar permisos del usuario de base de datos

### Error de Redis/Celery
- Confirmar que Redis esté ejecutándose
- Verificar la URL del broker en settings.py
- Reiniciar el worker de Celery

### Error de Vite
- Ejecutar `npm install` para instalar dependencias
- Verificar que Node.js esté instalado correctamente
- Confirmar que el puerto 5173 esté disponible

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Francisco Vanegas**
- GitHub: [@FranciscoDJVI](https://github.com/FranciscoDJVI)
- Email: vanegasfrancisco415@gmail.com

---

⭐ **¡Si este proyecto te ha sido útil, no olvides darle una estrella!** ⭐

*Desarrollado con 💙 como proyecto de aprendizaje del framework Django*
