# Constantes del proyecto para evitar strings hardcodeados

# Grupos de usuarios
ADMIN_GROUP = "Administrador"
SELLER_GROUP = "Vendedor"

# Estados de venta
SELL_STATE_PENDING = "Pendiente"
SELL_STATE_COMPLETED = "Completado"
SELL_STATE_CANCELLED = "Cancelado"

# Tipos de pago
PAYMENT_TYPE_CASH = "Efectivo"
PAYMENT_TYPE_CARD = "Tarjeta"
PAYMENT_TYPE_TRANSFER = "Transferencia"

# Mensajes de éxito
SUCCESS_PRODUCT_SAVED = "Producto guardado con éxito"
SUCCESS_PRODUCT_UPDATED = "Producto actualizado con éxito"
SUCCESS_PRODUCT_DELETED = "Producto eliminado con éxito"
SUCCESS_STOCK_UPDATED = "Stock actualizado"
SUCCESS_STOCK_CREATED = "Nuevo stock creado"
SUCCESS_USER_ASSIGNED = "Usuario asignado a grupo con éxito"
SUCCESS_SELL_CREATED = "Venta registrada con éxito"

# Mensajes de error
ERROR_PRODUCT_EXISTS = "El producto ya existe"
ERROR_PRODUCT_NOT_FOUND = "El producto no existe"
ERROR_DATABASE_ERROR = "Error en la base de datos"
ERROR_INVALID_FORM = "Por favor, corrige los errores en el formulario"
ERROR_PERMISSION_DENIED = "No tienes permisos para realizar esta acción"

# URLs de redirección
LOGIN_URL = "accounts/login"
MAIN_URL = "main"
ERROR_URL = "error"

# Cache keys
CACHE_KEY_ALL_PRODUCTS = "all_products"
CACHE_KEY_STOCK_LIST = "stock_list"
CACHE_KEY_USER_GROUPS = "user_groups_{}"

# Cache timeout (en segundos)
CACHE_TIMEOUT_SHORT = 60 * 5     # 5 minutos
CACHE_TIMEOUT_MEDIUM = 60 * 15   # 15 minutos
CACHE_TIMEOUT_LONG = 60 * 60     # 1 hora

# Paginación
PRODUCTS_PER_PAGE = 25
SELLS_PER_PAGE = 20
STOCK_PER_PAGE = 30
