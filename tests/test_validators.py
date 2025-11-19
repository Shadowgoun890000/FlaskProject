import pytest
from app import validar_datos
from tests.test_utils import app_functions


class TestValidators:
    """Pruebas para funciones de validación"""

    def test_validar_datos_completos(self):
        """Test: Validación con datos completos y válidos"""
        datos_validos = {
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

        errores = app_functions['validar_datos'](datos_validos)
        assert errores == {}

    def test_validar_datos_campos_obligatorios(self):
        """Test: Validación con campos obligatorios faltantes"""
        datos_incompletos = {
            'nombre_completo': '',
            'curp': '',
            'nombre': 'Juan',
            'paterno': 'Pérez',
            'celular': '0987654321',
            'correo': 'juan@example.com',
            'nivel': 'primaria',
            'municipio': 'aguascalientes',
            'asunto': 'inscripcion'
        }

        errores = validar_datos(datos_incompletos)
        assert 'nombre_completo' in errores
        assert 'curp' in errores

    def test_validar_curp_invalida(self):
        """Test: Validación de CURP inválida"""
        datos = {
            'nombre_completo': 'Juan Pérez',
            'curp': 'CURP-INVALIDA',
            'nombre': 'Juan',
            'paterno': 'Pérez',
            'celular': '0987654321',
            'correo': 'juan@example.com',
            'nivel': 'primaria',
            'municipio': 'aguascalientes',
            'asunto': 'inscripcion'
        }

        errores = validar_datos(datos)
        assert 'curp' in errores

    def test_validar_email_invalido(self):
        """Test: Validación de email inválido"""
        datos = {
            'nombre_completo': 'Juan Pérez',
            'curp': 'TEST123456HDFABC01',
            'nombre': 'Juan',
            'paterno': 'Pérez',
            'celular': '0987654321',
            'correo': 'email-invalido',
            'nivel': 'primaria',
            'municipio': 'aguascalientes',
            'asunto': 'inscripcion'
        }

        errores = validar_datos(datos)
        assert 'correo' in errores

    def test_validar_telefono_invalido(self):
        """Test: Validación de teléfono inválido"""
        datos = {
            'nombre_completo': 'Juan Pérez',
            'curp': 'TEST123456HDFABC01',
            'nombre': 'Juan',
            'paterno': 'Pérez',
            'telefono': '123',  # Muy corto
            'celular': '0987654321',
            'correo': 'juan@example.com',
            'nivel': 'primaria',
            'municipio': 'aguascalientes',
            'asunto': 'inscripcion'
        }

        errores = validar_datos(datos)
        assert 'telefono' in errores

    def test_validar_celular_invalido(self):
        """Test: Validación de celular inválido"""
        datos = {
            'nombre_completo': 'Juan Pérez',
            'curp': 'TEST123456HDFABC01',
            'nombre': 'Juan',
            'paterno': 'Pérez',
            'celular': '123',  # Muy corto
            'correo': 'juan@example.com',
            'nivel': 'primaria',
            'municipio': 'aguascalientes',
            'asunto': 'inscripcion'
        }

        errores = validar_datos(datos)
        assert 'celular' in errores