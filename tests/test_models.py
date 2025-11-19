import pytest
from unittest.mock import Mock, patch
from datetime import datetime


class TestUsuarioModel:
    """Pruebas para el modelo Usuario - VERSIÓN CON MOCKS"""

    def test_usuario_creation(self, sample_usuario_data):
        """Test: Creación de usuario válido"""
        from registro.models.usuario import Usuario

        # Crear usuario con datos de ejemplo
        usuario = Usuario(**sample_usuario_data)

        # Verificar que los atributos se asignaron correctamente
        assert usuario.curp == 'TEST123456HDFABC01'
        assert usuario.nombre_completo == 'Juan Pérez García'
        assert usuario.nombre == 'Juan'
        assert usuario.paterno == 'Pérez'
        assert usuario.materno == 'García'
        assert usuario.telefono == '1234567890'
        assert usuario.celular == '0987654321'
        assert usuario.correo == 'juan@example.com'

    def test_usuario_repr(self, sample_usuario_data):
        """Test: Representación del usuario"""
        from registro.models.usuario import Usuario

        usuario = Usuario(**sample_usuario_data)
        repr_str = repr(usuario)
        assert 'Usuario' in repr_str
        assert 'TEST123456HDFABC01' in repr_str


class TestTurnoModel:
    """Pruebas para el modelo Turno - VERSIÓN CON MOCKS"""

    def test_turno_creation(self, sample_turno_data):
        """Test: Creación de turno válido"""
        from registro.models.turno import Turno

        turno = Turno(
            numero_turno='AGUASCALIENTES-0001',
            usuario_id=1,
            **sample_turno_data
        )

        assert turno.numero_turno == 'AGUASCALIENTES-0001'
        assert turno.nivel == 'primaria'
        assert turno.municipio == 'aguascalientes'
        assert turno.asunto == 'inscripcion'
        assert turno.estado == 'pendiente'
        assert turno.usuario_id == 1

    def test_turno_repr(self, sample_turno_data):
        """Test: Representación del turno"""
        from registro.models.turno import Turno

        turno = Turno(
            numero_turno='AGUASCALIENTES-0001',
            usuario_id=1,
            **sample_turno_data
        )

        repr_str = repr(turno)
        assert 'Turno' in repr_str
        assert 'AGUASCALIENTES-0001' in repr_str


class TestAdministradorModel:
    """Pruebas para el modelo Administrador - VERSIÓN CON MOCKS"""

    def test_admin_creation(self, sample_admin_data):
        """Test: Creación de administrador válido"""
        from registro.models.administrador import Administrador

        admin = Administrador(
            username=sample_admin_data['username'],
            email=sample_admin_data['email'],
            nombre_completo=sample_admin_data['nombre_completo'],
            rol=sample_admin_data['rol']
        )
        admin.set_password(sample_admin_data['password'])

        assert admin.username == 'testadmin'
        assert admin.email == 'admin@test.com'
        assert admin.nombre_completo == 'Administrador Test'
        assert admin.rol == 'operador'
        assert admin.activo == True
        assert admin.check_password('testpass123') == True
        assert admin.check_password('wrongpassword') == False

    def test_admin_password_validation(self):
        """Test: Validación de contraseña"""
        from registro.models.administrador import Administrador

        admin = Administrador(
            username='testuser',
            email='test@test.com',
            nombre_completo='Test User'
        )

        # Contraseña muy corta
        with pytest.raises(ValueError):
            admin.set_password('123')

    def test_admin_username_validation(self):
        """Test: Validación de username"""
        from registro.models.administrador import Administrador

        # Username válido
        is_valid, msg = Administrador.validate_username('user123')
        assert is_valid == True

        # Username muy corto
        is_valid, msg = Administrador.validate_username('ab')
        assert is_valid == False

        # Username con caracteres inválidos
        is_valid, msg = Administrador.validate_username('user@test')
        assert is_valid == False


class TestCatalogosModels:
    """Pruebas para modelos de catálogos - VERSIÓN CON MOCKS"""

    def test_catalogo_nivel_creation(self):
        """Test: Creación de nivel"""
        from registro.models.catalogo_nivel import CatalogoNivel

        nivel = CatalogoNivel(
            clave='primaria',
            nombre='Primaria',
            activo=True
        )

        assert nivel.clave == 'primaria'
        assert nivel.nombre == 'Primaria'
        assert nivel.activo == True

        # Probar el método to_dict
        nivel_dict = nivel.to_dict()
        assert nivel_dict['clave'] == 'primaria'
        assert nivel_dict['nombre'] == 'Primaria'
        assert nivel_dict['activo'] == True

    def test_catalogo_municipio_creation(self):
        """Test: Creación de municipio"""
        from registro.models.catalogo_municipio import CatalogoMunicipio

        municipio = CatalogoMunicipio(
            clave='aguascalientes',
            nombre='Aguascalientes',
            activo=True
        )

        assert municipio.clave == 'aguascalientes'
        assert municipio.nombre == 'Aguascalientes'

    def test_catalogo_asunto_creation(self):
        """Test: Creación de asunto"""
        from registro.models.catalogo_asunto import CatalogoAsunto

        asunto = CatalogoAsunto(
            clave='inscripcion',
            nombre='Inscripción',
            activo=True
        )

        assert asunto.clave == 'inscripcion'
        assert asunto.nombre == 'Inscripción'