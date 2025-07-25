import logging
import sys
from pathlib import Path

# Configuración de logging
def setup_logging(level=logging.INFO):
    """
    Configura el sistema de logging para la aplicación
    """
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    return root_logger

# Utilidades para archivos
def ensure_directory(path: str) -> Path:
    """
    Asegura que un directorio existe, creándolo si es necesario
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def get_file_size_mb(file_path: str) -> float:
    """
    Obtiene el tamaño de un archivo en MB
    """
    return Path(file_path).stat().st_size / (1024 * 1024)

def clean_text(text: str) -> str:
    """
    Limpia texto para procesamiento
    """
    if not text:
        return ""
    
    # Remover caracteres de control
    cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Normalizar espacios
    cleaned = ' '.join(cleaned.split())
    
    return cleaned
