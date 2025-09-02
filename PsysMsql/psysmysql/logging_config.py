import logging
import os
from datetime import datetime
import time


class ColoredFormatter(logging.Formatter):

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "ENDC": "\033[0m",  # Reset
    }

    def format(self, record):
        # Agregar colores si es terminal
        if hasattr(record, "levelname"):
            color = self.COLORS.get(record.levelname, self.COLORS["ENDC"])
            record.levelname = f"{color}{record.levelname}{self.COLORS['ENDC']}"

        return super().format(record)


def setup_logging():
    """
    Configura el sistema de logging para el proyecto
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Configuración básica
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Handler para archivo
            logging.FileHandler(
                os.path.join(
                    log_dir, f'psysmysql_{datetime.now().strftime("%Y%m%d")}.log'
                )
            ),
            # Handler para consola con colores
            logging.StreamHandler(),
        ],
    )

    # Configurar handler de consola con colores
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Logger principal
    logger = logging.getLogger("psysmysql")
    logger.setLevel(logging.DEBUG)

    return logger


def get_logger(name):
    """
    Obtiene un logger específico para un módulo

    Args:
        name (str): Nombre del módulo/clase

    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(f"psysmysql.{name}")


# Loggers específicos por funcionalidad
def get_product_logger():
    """Logger para operaciones de productos"""
    return get_logger("products")


def get_sell_logger():
    """Logger para operaciones de ventas"""
    return get_logger("sells")


def get_auth_logger():
    """Logger para autenticación y autorización"""
    return get_logger("auth")


def get_api_logger():
    """Logger para API calls y AJAX"""
    return get_logger("api")


def get_cache_logger():
    """Logger para operaciones de cache"""
    return get_logger("cache")


def get_db_logger():
    """Logger para operaciones de base de datos"""
    return get_logger("database")


def get_clients_logger():
    """Logger para operaciones de clientes"""
    return get_logger("clientes")


# Decorator para logging de funciones
def log_function_call(logger=None):
    """
    Decorator para log automático de llamadas a funciones

    Usage:
        @log_function_call()
        def my_function():
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger("functions")
            func_name = f"{func.__module__}.{func.__name__}"

            try:
                func_logger.info(f"Iniciando {func_name}")
                result = func(*args, **kwargs)
                func_logger.info(f"Completado {func_name}")
                return result
            except Exception as e:
                func_logger.error(f"Error en {func_name}: {str(e)}")
                raise

        return wrapper

    return decorator


# Decorator para timing de funciones
def log_execution_time(logger=None):
    """
    Decorator para medir tiempo de ejecución
    """
    import time

    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger("performance")
            func_name = f"{func.__module__}.{func.__name__}"

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = start_time - time.time()
                func_logger.info(f"{func_name} ejecutado en {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                func_logger.error(
                    f"{func_name} falló después de {execution_time:.3f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator


# Context manager para logging de operaciones
class LogOperation:

    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or get_logger("operations")
        self.start_time: float

    def __enter__(self):

        self.start_time = time.time()
        self.logger.info(f"Iniciando: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        duration = self.start_time - time.time()
        if exc_type is None:
            self.logger.info(f"Completado: {self.operation_name} ({duration:.3f}s)")
        else:
            self.logger.error(
                f"Error en: {self.operation_name} ({duration:.3f}s): {str(exc_val)}"
            )

        return False  # No suprimir excepciones


# Inicializar logging
setup_logging()
