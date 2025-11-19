import pytest
from unittest.mock import Mock, patch
from flask import session


class TestSessionManager:
    """Pruebas para el SessionManager - VERSIÓN INDEPENDIENTE"""

    def test_session_manager_singleton(self):
        """Test: SessionManager es singleton"""
        from registro.auth.session_manager import SessionManager
        manager1 = SessionManager()
        manager2 = SessionManager()
        assert manager1 is manager2

    def test_login_logout(self):
        """Test: Login y logout de administrador - SIN FIXTURE"""
        # Crear una aplicación de prueba mínima
        from flask import Flask
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret'

        with test_app.test_request_context():
            from registro.auth.session_manager import SessionManager
            session_manager = SessionManager()

            # Simular login
            session_manager.login_admin(1, 'testadmin')
            assert session.get('logged_in') == True
            assert session.get('admin_id') == 1
            assert session.get('admin_username') == 'testadmin'

            # Verificar estado login
            assert session_manager.is_logged_in() == True
            assert session_manager.get_admin_id() == 1
            assert session_manager.get_admin_username() == 'testadmin'

            # Simular logout
            session_manager.logout_admin()
            assert session.get('logged_in') is None

    def test_not_logged_in(self):
        """Test: Estado cuando no hay sesión activa - SIN FIXTURE"""
        from flask import Flask
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret'

        with test_app.test_request_context():
            from registro.auth.session_manager import SessionManager
            session_manager = SessionManager()

            # Limpiar sesión
            session.clear()
            assert session_manager.is_logged_in() == False
            assert session_manager.get_admin_id() is None
            assert session_manager.get_admin_username() is None


class TestRegistrationManager:
    """Pruebas para el RegistrationManager - VERSIÓN INDEPENDIENTE"""

    def test_generate_registration_code(self):
        """Test: Generación de código de registro"""
        from registro.auth.registration_manager import RegistrationManager
        manager = RegistrationManager()
        code = manager.generate_registration_code()

        assert code is not None
        assert len(code) == 16

    def test_validate_registration_code(self):
        """Test: Validación de código de registro"""
        from registro.auth.registration_manager import RegistrationManager
        manager = RegistrationManager()
        code = manager.generate_registration_code()

        # Código válido
        is_valid, message = manager.validate_registration_code(code)
        assert is_valid == True

        # Código inválido
        is_valid, message = manager.validate_registration_code('INVALIDO')
        assert is_valid == False

    def test_mark_code_used(self):
        """Test: Marcar código como usado"""
        from registro.auth.registration_manager import RegistrationManager
        manager = RegistrationManager()
        code = manager.generate_registration_code()

        # Marcar como usado
        manager.mark_code_used(code)

        # Verificar que ya no es válido
        is_valid, message = manager.validate_registration_code(code)
        assert is_valid == False

    def test_get_active_codes(self):
        """Test: Obtener códigos activos"""
        from registro.auth.registration_manager import RegistrationManager
        manager = RegistrationManager()

        # Generar varios códigos
        code1 = manager.generate_registration_code()
        code2 = manager.generate_registration_code()

        # Marcar uno como usado
        manager.mark_code_used(code1)

        active_codes = manager.get_active_codes()
        assert code2 in active_codes
        assert code1 not in active_codes


class TestAuthenticationRoutes:
    """Pruebas para rutas de autenticación - VERSIÓN CORREGIDA"""

    def test_login_page(self, client):
        """Test: Página de login carga correctamente - CORREGIDO"""
        # Verificar que el template existe antes de hacer la petición
        import os
        template_path = os.path.join(os.path.dirname(__file__), '../templates/login.html')
        assert os.path.exists(template_path), f"Template no encontrado: {template_path}"

        response = client.get('/admin/login')
        assert response.status_code == 200

    def test_logout_redirect(self, client):
        """Test: Logout redirige correctamente - CORREGIDO"""
        response = client.get('/admin/logout', follow_redirects=True)
        # Puede redirigir al login (302) o mostrar la página de login (200)
        assert response.status_code in [200, 302]

    def test_login_invalid_captcha(self, client):
        """Test: Login con CAPTCHA inválido - CORREGIDO"""
        response = client.post('/admin/login', data={
            'username': 'testadmin',
            'password': 'testpass',
            'captcha_input': 'WRONG',
            'captcha_answer': 'CORRECT'
        })

        assert response.status_code == 200
        # Verificar que se muestra mensaje de error (puede estar en la respuesta)
        assert b'error' in response.data.lower() or b'incorrecto' in response.data.lower()