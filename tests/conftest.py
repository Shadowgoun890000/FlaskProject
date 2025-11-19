import pytest
import os
import sys
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path para los imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(scope='function')
def app():
    """Configuración de la aplicación para pruebas - VERSIÓN SIMPLIFICADA"""
    # Mockear todas las dependencias de base de datos antes de importar
    with patch('registro.models.database.db') as mock_db:
        with patch('registro.models.database.init_db'):
            with patch('app.registration_manager'):
                with patch('app.session_manager'):
                    # Mock para evitar problemas con SQLAlchemy en los serializers
                    mock_db.session = Mock()

                    # Ahora importar la aplicación
                    from app import app as flask_app

                    # Configuración de testing
                    flask_app.config.update({
                        'TESTING': True,
                        'SECRET_KEY': 'test-secret-key',
                        'WTF_CSRF_ENABLED': False
                    })

                    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Cliente de pruebas"""
    return app.test_client()


@pytest.fixture
def mock_db():
    """Mock de la base de datos para tests que lo necesiten"""
    with patch('registro.models.database.db') as mock:
        mock.session = Mock()
        yield mock


@pytest.fixture
def mock_session():
    """Mock de sesión de base de datos"""
    with patch('registro.models.database.db.session') as mock:
        yield mock


# Los fixtures de datos de ejemplo se mantienen igual
@pytest.fixture
def sample_usuario_data():
    return {
        'curp': 'TEST123456HDFABC01',
        'nombre_completo': 'Juan Pérez García',
        'nombre': 'Juan',
        'paterno': 'Pérez',
        'materno': 'García',
        'telefono': '1234567890',
        'celular': '0987654321',
        'correo': 'juan@example.com'
    }


@pytest.fixture
def sample_turno_data():
    return {
        'nivel': 'primaria',
        'municipio': 'aguascalientes',
        'asunto': 'inscripcion',
        'estado': 'pendiente'
    }


@pytest.fixture
def sample_admin_data():
    return {
        'username': 'testadmin',
        'email': 'admin@test.com',
        'password': 'testpass123',
        'nombre_completo': 'Administrador Test',
        'rol': 'operador'
    }