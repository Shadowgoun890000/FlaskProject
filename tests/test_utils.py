"""
Utilidades para tests que necesitan funciones de app.py
"""
import sys
import os

# Agregar el directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def import_app_functions():
    """Importar funciones desde app.py"""
    try:
        from app import (
            obtener_siguiente_turno,
            validar_datos,
            generar_pdf_comprobante,
            generate_captcha
        )
        return {
            'obtener_siguiente_turno': obtener_siguiente_turno,
            'validar_datos': validar_datos,
            'generar_pdf_comprobante': generar_pdf_comprobante,
            'generate_captcha': generate_captcha
        }
    except ImportError as e:
        print(f"Error importando funciones de app: {e}")
        return None

# Pre-importar funciones para uso en tests
app_functions = import_app_functions()