#!/usr/bin/env python3
"""
Script de inicio para el servidor API desde el directorio backend
"""
import uvicorn
import os
import sys
from pathlib import Path

# Asegurar que estamos en el directorio correcto
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

# Agregar el directorio backend al path
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print(f"Iniciando servidor desde: {backend_dir}")
    print(f"Directorio de trabajo: {os.getcwd()}")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
