#!/usr/bin/env python3
"""
Script para ejecutar el servidor de desarrollo
"""
import uvicorn
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
