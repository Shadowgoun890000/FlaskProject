"""
Configuración para tests
"""
import os
import sys

# Agregar el directorio raíz al path para imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configuración específica para tests
TEST_CONFIG = {
    'TESTING': True,
    'SECRET_KEY': 'test-secret-key',
    'WTF_CSRF_ENABLED': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}