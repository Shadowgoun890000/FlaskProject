import pytest
from unittest.mock import Mock, patch


class TestAdminRoutes:
    """Pruebas para rutas administrativas - VERSIÓN SIMPLIFICADA"""

    def test_dashboard_requires_login(self, client):
        """Test: Dashboard requiere autenticación - CORREGIDO"""
        response = client.get('/admin/dashboard', follow_redirects=False)
        # Debería redirigir al login (302) o dar no autorizado (401)
        assert response.status_code in [302, 401]

    def test_admin_turnos_api_requires_login(self, client):
        """Test: API de turnos requiere autenticación - CORREGIDO"""
        response = client.get('/api/admin/turnos', follow_redirects=False)
        # Puede ser 401 (no autorizado) o 302 (redirección)
        assert response.status_code in [401, 302]

    def test_buscar_turno_publico(self, client):
        """Test: Búsqueda pública de turnos"""
        response = client.post('/publico/buscar_turno', data={
            'curp': 'TEST123456HDFABC01',
            'numero_turno': 'AGUASCALIENTES-0001'
        })

        assert response.status_code == 200

    def test_descargar_pdf_not_found(self, client):
        """Test: Descarga de PDF no encontrado"""
        response = client.get('/descargar_pdf/archivo_inexistente.pdf')
        assert response.status_code == 404


class TestCRUDRoutes:
    """Pruebas para rutas CRUD de catálogos - VERSIÓN SIMPLIFICADA"""

    def test_catalogos_crud_routes_require_login(self, client):
        """Test: Rutas CRUD de catálogos requieren login - CORREGIDO"""
        catalogos = ['niveles', 'municipios', 'asuntos']

        for catalogo in catalogos:
            # Listar (debería requerir login)
            response = client.get(f'/admin/catalogos/{catalogo}', follow_redirects=False)
            assert response.status_code in [401, 302]  # No autorizado o redirección