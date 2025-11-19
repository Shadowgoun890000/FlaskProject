import pytest
from unittest.mock import Mock, patch
from tests.test_utils import app_functions

class TestTurnoLogic:
    """Pruebas para la lógica de turnos - VERSIÓN CORREGIDA"""

    def test_obtener_siguiente_turno_nueva_secuencia(self, app):
        """Test: Obtener siguiente turno con nueva secuencia - CORREGIDO"""
        with app.app_context():
            from registro.models.secuencia_turno import SecuenciaTurno
            from registro.models.database import db

            # Asegurarse de que no existe una secuencia para 'aguascalientes'
            secuencia_existente = SecuenciaTurno.query.filter_by(municipio='aguascalientes').first()
            if secuencia_existente:
                db.session.delete(secuencia_existente)
                db.session.commit()

            numero_turno = app_functions['obtener_siguiente_turno']('aguascalientes')

            # Verificar que se creó la secuencia
            secuencia = SecuenciaTurno.query.filter_by(municipio='aguascalientes').first()
            assert secuencia is not None
            # CORRECCIÓN: La primera vez devuelve 1 y la secuencia queda en 2 para el próximo
            assert secuencia.siguiente_numero == 2
            assert numero_turno == 'AGUASCALIENTES-0001'

    def test_obtener_siguiente_turno_existente(self, app):
        """Test: Obtener siguiente turno con secuencia existente - CORREGIDO"""
        with app.app_context():
            from registro.models.secuencia_turno import SecuenciaTurno
            from registro.models.database import db

            # Crear una secuencia existente
            secuencia = SecuenciaTurno(municipio='aguascalientes', siguiente_numero=5)
            db.session.add(secuencia)
            db.session.commit()

            numero_turno = app_functions['obtener_siguiente_turno']('aguascalientes')

            # Verificar que se incrementó la secuencia
            secuencia_actualizada = SecuenciaTurno.query.filter_by(municipio='aguascalientes').first()
            assert secuencia_actualizada.siguiente_numero == 6
            # CORRECCIÓN: Usa el número actual (5) y luego incrementa a 6
            assert numero_turno == 'AGUASCALIENTES-0005'

    @patch('app.random.randint')
    def test_obtener_siguiente_turno_fallback(self, mock_randint, app):
        """Test: Fallback cuando hay error en la secuencia - CORREGIDO"""
        with app.app_context():
            mock_randint.return_value = 9999

            # Forzar error en la base de datos durante el COMMIT (no durante flush)
            with patch('registro.models.database.db.session.commit', side_effect=Exception('DB Error')):
                # También forzar error en flush para nueva secuencia
                with patch('registro.models.database.db.session.flush', side_effect=Exception('DB Error')):
                    numero_turno = app_functions['obtener_siguiente_turno']('test')

            # CORRECCIÓN: El fallback debe usar el número aleatorio
            assert numero_turno == 'TEST-9999'

    @patch('app.TurnoPDF')
    @patch('app.qrcode.QRCode')
    @patch('app.tempfile.gettempdir')
    def test_generar_pdf_comprobante(self, mock_tempdir, mock_qr, mock_pdf, app):
        """Test: Generación de PDF de comprobante"""
        with app.app_context():
            from app import generar_pdf_comprobante

            # Mock del directorio temporal
            mock_tempdir.return_value = '/tmp'

            # Mock del PDF
            mock_pdf_instance = Mock()
            mock_pdf.return_value = mock_pdf_instance

            # Mock del QR
            mock_qr_instance = Mock()
            mock_qr.return_value = mock_qr_instance

            datos = {
                'nombre_completo': 'Juan Pérez García',
                'curp': 'TEST123456HDFABC01',
                'nombre': 'Juan',
                'paterno': 'Pérez',
                'materno': 'García',
                'telefono': '1234567890',
                'celular': '0987654321',
                'correo': 'juan@example.com',
                'nivel': 'primaria',
                'municipio': 'aguascalientes',
                'asunto': 'inscripcion'
            }

            numero_turno = 'AGUASCALIENTES-0001'

            pdf_path = generar_pdf_comprobante(datos, numero_turno)

            assert pdf_path is not None
            assert 'comprobante_turno_AGUASCALIENTES-0001.pdf' in pdf_path


class TestTurnoRoutes:
    """Pruebas para rutas de turnos - VERSIÓN CORREGIDA"""

    def test_publico_route(self, client):
        """Test: Ruta pública carga correctamente"""
        response = client.get('/publico')
        assert response.status_code == 200

    def test_catalogos_routes(self, client):
        """Test: Rutas de catálogos responden"""
        routes = [
            '/api/catalogos/niveles',
            '/api/catalogos/municipios',
            '/api/catalogos/asuntos'
        ]

        for route in routes:
            response = client.get(route)
            assert response.status_code == 200

    @patch('app.validar_datos')
    @patch('app.obtener_siguiente_turno')
    @patch('app.generar_pdf_comprobante')
    def test_generar_turno_success(self, mock_pdf, mock_turno, mock_validar, client, app):
        """Test: Generación exitosa de turno"""
        with app.app_context():
            # Mocks
            mock_validar.return_value = {}  # Sin errores
            mock_turno.return_value = 'AGUASCALIENTES-0003'
            mock_pdf.return_value = '/tmp/comprobante.pdf'

            response = client.post('/generar_turno', data={
                'nombreCompleto': 'Juan Pérez García',
                'curp': 'TEST123456HDFABC01',
                'nombre': 'Juan',
                'paterno': 'Pérez',
                'materno': 'García',
                'telefono': '1234567890',
                'celular': '0987654321',
                'correo': 'juan@example.com',
                'nivel': 'primaria',
                'municipio': 'aguascalientes',
                'asunto': 'inscripcion'
            })

            # Verificar respuesta exitosa
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True

    @patch('app.validar_datos')
    def test_generar_turno_validation_errors(self, mock_validar, client):
        """Test: Errores de validación en generación de turno"""
        mock_validar.return_value = {
            'curp': 'Formato de CURP inválido',
            'correo': 'Formato de correo inválido'
        }

        response = client.post('/generar_turno', data={})

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == False
        assert 'errors' in data