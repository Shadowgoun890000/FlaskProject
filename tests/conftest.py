import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path para los imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


@pytest.fixture(scope='function')
def app():
    """Configuración de la aplicación para pruebas - VERSIÓN CORREGIDA"""
    # Configurar una base de datos temporal para pruebas
    db_fd, db_path = tempfile.mkstemp()

    # Importar y configurar la aplicación real desde app.py
    import app as main_app

    # Crear una copia de la aplicación con configuración de testing
    from flask import Flask
    from registro.models.database import db

    # Crear una nueva aplicación Flask para testing
    flask_app = Flask(__name__,
                      template_folder='../templates',  # ← CORRECCIÓN IMPORTANTE
                      static_folder='../static'
                      )

    # Configuración de testing con base de datos SQLite temporal
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'TEMPLATES_AUTO_RELOAD': True
    })

    # Inicializar la base de datos
    db.init_app(flask_app)

    # IMPORTANTE: Registrar las rutas copiando el sistema de rutas de la app principal
    # Esto evita problemas de importación circular
    with main_app.app.app_context():
        for rule in main_app.app.url_map.iter_rules():
            if rule.endpoint != 'static':
                view_func = main_app.app.view_functions[rule.endpoint]
                flask_app.add_url_rule(
                    rule.rule,
                    endpoint=rule.endpoint,
                    view_func=view_func,
                    methods=rule.methods
                )

    # Crear tablas en contexto de aplicación
    with flask_app.app_context():
        db.create_all()

        yield flask_app

        # Limpieza
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def client(app):
    """Cliente de pruebas"""
    return app.test_client()


# Fixtures de datos de ejemplo (mantener igual)
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