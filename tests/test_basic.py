"""
Test básico para verificar que el framework funciona
"""
import sys
import os


def test_basic():
    """Test básico que siempre pasa"""
    print("✅ Test básico ejecutándose")
    assert 1 + 1 == 2


def test_imports():
    """Test para verificar que los imports funcionan"""
    try:
        # Intentar importar módulos principales
        from registro.models.usuario import Usuario
        from registro.models.turno import Turno
        from registro.auth.session_manager import SessionManager

        print("✅ Todos los imports funcionan correctamente")
        assert True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        assert False, f"Error de importación: {e}"


def test_environment():
    """Test para verificar el entorno"""
    print(f"Python path: {sys.path}")
    print(f"Directorio actual: {os.getcwd()}")
    assert True