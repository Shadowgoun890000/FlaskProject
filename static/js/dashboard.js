// static/js/dashboard.js - VERSIÓN REACTIVA

class DashboardApp {
    constructor() {
        this.estatusChart = null;
        this.municipiosChart = null;
        this.statsElements = {
            'total_turnos': document.getElementById('total-turnos'),
            'pendientes': document.getElementById('pendientes'),
            'resueltos': document.getElementById('resueltos'),
            'total_municipios': document.getElementById('total-municipios')
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadEstadisticas();
        this.loadTurnos();

        // Iniciar actualización automática cada 5 segundos
        this.startAutoRefresh();
    }

    startAutoRefresh() {
        // Actualizar estadísticas cada 5 segundos
        setInterval(() => {
            this.updateStats();
            this.updateCharts();
        }, 5000);

        // Escuchar eventos de actualización
        document.addEventListener('turnoUpdated', () => {
            this.updateStats();
            this.updateCharts();
            this.loadTurnos(); // También actualizar la lista
        });
    }

    bindEvents() {
        // Filtros de turnos
        document.getElementById('btnFiltrar').addEventListener('click', () => this.loadTurnos());

        // Búsqueda
        document.getElementById('btnBuscar').addEventListener('click', () => this.buscarTurnos());

        // Tecla Enter en búsqueda
        document.getElementById('searchCURP').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.buscarTurnos();
        });
        document.getElementById('searchNombre').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.buscarTurnos();
        });

        // Gestión de códigos
        document.getElementById('btnGenerarCodigo').addEventListener('click', this.generarCodigoRegistro);
        document.getElementById('btnVerCodigos').addEventListener('click', this.verCodigosActivos);
    }

    // ========== ACTUALIZACIÓN REACTIVA ==========

    async updateStats() {
        try {
            const response = await fetch('/api/admin/estadisticas');
            const data = await response.json();

            // Calcular totales
            const totalTurnos = data.estatus.reduce((sum, item) => sum + item.cantidad, 0);
            const pendientes = data.estatus.find(e => e.estado === 'pendiente')?.cantidad || 0;
            const resueltos = data.estatus.find(e => e.estado === 'resuelto')?.cantidad || 0;
            const totalMunicipios = data.municipios.length;

            this.updateElement('total_turnos', totalTurnos);
            this.updateElement('pendientes', pendientes);
            this.updateElement('resueltos', resueltos);
            this.updateElement('total_municipios', totalMunicipios);

        } catch (error) {
            console.error('Error actualizando estadísticas:', error);
        }
    }

    async updateCharts() {
        try {
            const response = await fetch('/api/admin/estadisticas');
            const data = await response.json();

            // Actualizar gráficas
            if (this.estatusChart && this.municipiosChart) {
                this.updateChartData(this.estatusChart, data.estatus);
                this.updateChartData(this.municipiosChart, data.municipios);
            }
        } catch (error) {
            console.error('Error actualizando gráficas:', error);
        }
    }

    updateElement(elementId, value) {
        if (this.statsElements[elementId]) {
            const element = this.statsElements[elementId];
            const oldValue = parseInt(element.textContent) || 0;
            const newValue = value;

            // Solo actualizar si cambió el valor
            if (oldValue !== newValue) {
                element.textContent = newValue;

                // Efecto visual de actualización
                element.classList.add('updating');
                setTimeout(() => {
                    element.classList.remove('updating');
                }, 500);
            }
        }
    }

    updateChartData(chart, newData) {
        if (!chart || !newData) return;

        // Actualizar datos del chart
        if (chart.config.type === 'doughnut') {
            chart.data.datasets[0].data = newData.map(item => item.cantidad);
            chart.data.labels = newData.map(item => this.capitalize(item.estado));
        } else if (chart.config.type === 'bar') {
            chart.data.datasets[0].data = newData.map(item => item.cantidad);
            chart.data.labels = newData.map(item => this.capitalize(item.municipio));
        }

        chart.update('none'); // Actualizar sin animación
    }

    // ========== FUNCIONES EXISTENTES (MODIFICADAS) ==========

    async loadEstadisticas() {
        try {
            const response = await fetch('/api/admin/estadisticas');
            const data = await response.json();

            this.renderEstatusChart(data.estatus);
            this.renderMunicipiosChart(data.municipios);
            this.updateStats(); // Actualizar contadores también
        } catch (error) {
            console.error('Error cargando estadísticas:', error);
        }
    }

    renderEstatusChart(estatusData) {
        const ctx = document.getElementById('estatusChart').getContext('2d');
        const colors = {
            'pendiente': '#f39c12',
            'atendido': '#3498db',
            'resuelto': '#27ae60',
            'cancelado': '#e74c3c'
        };

        // Destruir chart existente
        if (this.estatusChart) {
            this.estatusChart.destroy();
        }

        this.estatusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: estatusData.map(item => this.capitalize(item.estado)),
                datasets: [{
                    data: estatusData.map(item => item.cantidad),
                    backgroundColor: estatusData.map(item => colors[item.estado] || '#95a5a6'),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderMunicipiosChart(municipiosData) {
        const ctx = document.getElementById('municipiosChart').getContext('2d');

        // Destruir chart existente
        if (this.municipiosChart) {
            this.municipiosChart.destroy();
        }

        this.municipiosChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: municipiosData.map(item => this.capitalize(item.municipio)),
                datasets: [{
                    label: 'Turnos por Municipio',
                    data: municipiosData.map(item => item.cantidad),
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    async loadTurnos() {
        try {
            const estado = document.getElementById('filterEstado').value;
            const municipio = document.getElementById('filterMunicipio').value;

            const params = new URLSearchParams();
            if (estado) params.append('estado', estado);
            if (municipio) params.append('municipio', municipio);

            const response = await fetch(`/api/admin/turnos?${params}`);
            const turnos = await response.json();

            this.renderTurnos(turnos);
        } catch (error) {
            console.error('Error cargando turnos:', error);
        }
    }

    renderTurnos(turnos) {
        const container = document.getElementById('turnosList');

        if (turnos.length === 0) {
            container.innerHTML = '<div class="text-center" style="padding: 2rem; background: white; border-radius: var(--border-radius);">No hay turnos que mostrar</div>';
            return;
        }

        container.innerHTML = turnos.map(turno => `
            <div class="turno-item" style="background: white; padding: 1rem; margin-bottom: 1rem; border-radius: var(--border-radius); border-left: 4px solid ${this.getEstadoColor(turno.estado)}">
                <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0;">Turno: ${turno.numero_turno}</h4>
                        <p style="margin: 0.25rem 0;"><strong>Usuario:</strong> ${turno.usuario.nombre_completo}</p>
                        <p style="margin: 0.25rem 0;"><strong>CURP:</strong> ${turno.usuario.curp}</p>
                        <p style="margin: 0.25rem 0;"><strong>Municipio:</strong> ${this.capitalize(turno.municipio)}</p>
                        <p style="margin: 0.25rem 0;"><strong>Asunto:</strong> ${this.capitalize(turno.asunto)}</p>
                        <p style="margin: 0.25rem 0;"><strong>Fecha:</strong> ${turno.fecha_creacion}</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="estado-badge" style="padding: 0.25rem 0.75rem; border-radius: 20px; background: ${this.getEstadoColor(turno.estado)}; color: white; font-size: 0.9rem;">
                            ${this.capitalize(turno.estado)}
                        </span>
                        <div style="margin-top: 0.5rem;">
                            <select class="form-control" style="margin-bottom: 0.5rem;" onchange="dashboard.cambiarEstado(${turno.id}, this.value)">
                                <option value="pendiente" ${turno.estado === 'pendiente' ? 'selected' : ''}>Pendiente</option>
                                <option value="atendido" ${turno.estado === 'atendido' ? 'selected' : ''}>Atendido</option>
                                <option value="resuelto" ${turno.estado === 'resuelto' ? 'selected' : ''}>Resuelto</option>
                                <option value="cancelado" ${turno.estado === 'cancelado' ? 'selected' : ''}>Cancelado</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async cambiarEstado(turnoId, nuevoEstado) {
        try {
            const response = await fetch(`/api/admin/turnos/${turnoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ estado: nuevoEstado })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Estado actualizado correctamente', 'success');

                // Disparar evento para actualización reactiva
                const event = new CustomEvent('turnoUpdated', {
                    detail: { turnoId, nuevoEstado }
                });
                document.dispatchEvent(event);

            } else {
                this.showNotification('Error al actualizar estado', 'error');
            }
        } catch (error) {
            console.error('Error cambiando estado:', error);
            this.showNotification('Error de conexión', 'error');
        }
    }

    // ========== FUNCIONES DE BÚSQUEDA (MANTENER EXISTENTES) ==========

    async buscarTurnos() {
        try {
            const curp = document.getElementById('searchCURP').value;
            const nombre = document.getElementById('searchNombre').value;

            if (!curp && !nombre) {
                alert('Ingresa al menos un criterio de búsqueda');
                return;
            }

            const params = new URLSearchParams();
            if (curp) params.append('curp', curp);
            if (nombre) params.append('nombre', nombre);

            const response = await fetch(`/api/admin/buscar?${params}`);
            const resultados = await response.json();

            this.renderResultadosBusqueda(resultados);
        } catch (error) {
            console.error('Error en búsqueda:', error);
        }
    }

    renderResultadosBusqueda(resultados) {
        const container = document.getElementById('searchResults');

        if (resultados.length === 0) {
            container.innerHTML = '<div class="text-center" style="padding: 1rem; background: #f8f9fa; border-radius: var(--border-radius);">No se encontraron resultados</div>';
            return;
        }

        container.innerHTML = `
            <h4>Resultados de la búsqueda (${resultados.length})</h4>
            ${resultados.map(turno => `
                <div class="resultado-item" style="background: #f8f9fa; padding: 1rem; margin-bottom: 0.5rem; border-radius: var(--border-radius);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <strong>${turno.usuario.nombre_completo}</strong> - ${turno.usuario.curp}
                            <br>
                            <small>Turno: ${turno.numero_turno} | ${this.capitalize(turno.municipio)} | ${this.capitalize(turno.asunto)}</small>
                        </div>
                        <span class="estado-badge" style="padding: 0.25rem 0.75rem; border-radius: 20px; background: ${this.getEstadoColor(turno.estado)}; color: white; font-size: 0.8rem;">
                            ${this.capitalize(turno.estado)}
                        </span>
                    </div>
                </div>
            `).join('')}
        `;
    }

    // ========== FUNCIONES DE GESTIÓN DE CÓDIGOS ==========

    async generarCodigoRegistro() {
        try {
            const response = await fetch('/admin/generate-code');
            const result = await response.json();

            if (result.success) {
                document.getElementById('codigosResult').innerHTML = `
                    <div class="success-message">
                        <strong>✅ ${result.message}</strong><br>
                        <code style="font-size: 1.2rem; background: #f8f9fa; padding: 10px; display: block; margin: 10px 0;">
                            ${result.code}
                        </code>
                        <p>Comparte este código con quien necesite registrarse. Válido por 24 horas.</p>
                    </div>
                `;
            } else {
                document.getElementById('codigosResult').innerHTML = `
                    <div class="error-message">❌ Error: ${result.error}</div>
                `;
            }
        } catch (error) {
            document.getElementById('codigosResult').innerHTML = `
                <div class="error-message">❌ Error de conexión</div>
            `;
        }
    }

    async verCodigosActivos() {
        try {
            const response = await fetch('/admin/active-codes');
            const result = await response.json();

            if (result.success) {
                if (result.active_codes === 0) {
                    document.getElementById('codigosResult').innerHTML = `
                        <div class="info-message">No hay códigos activos</div>
                    `;
                } else {
                    let html = `<div class="success-message"><strong>📋 Códigos Activos: ${result.active_codes}</strong><br>`;

                    for (const [code, data] of Object.entries(result.codes)) {
                        const expires = new Date(data.expires_at).toLocaleString();
                        html += `
                            <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                                <strong>Código:</strong> <code>${code}</code><br>
                                <strong>Expira:</strong> ${expires}<br>
                                <strong>Usos restantes:</strong> ${data.max_uses}
                            </div>
                        `;
                    }

                    html += `</div>`;
                    document.getElementById('codigosResult').innerHTML = html;
                }
            } else {
                document.getElementById('codigosResult').innerHTML = `
                    <div class="error-message">❌ Error: ${result.error}</div>
                `;
            }
        } catch (error) {
            document.getElementById('codigosResult').innerHTML = `
                <div class="error-message">❌ Error de conexión</div>
            `;
        }
    }

    // ========== FUNCIONES AUXILIARES ==========

    getEstadoColor(estado) {
        const colores = {
            'pendiente': '#f39c12',
            'atendido': '#3498db',
            'resuelto': '#27ae60',
            'cancelado': '#e74c3c'
        };
        return colores[estado] || '#95a5a6';
    }

    capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Utilidad para tabla simple con editar/eliminar
function renderTabla(items, onUpdate, onDelete) {
  const cont = document.createElement('div');
  const table = document.createElement('table');
  table.className = 'table';
  table.style.width = '100%';
  table.innerHTML = `
    <thead><tr>
      <th>ID</th><th>Clave</th><th>Nombre</th><th>Activo</th><th>Acciones</th>
    </tr></thead>
    <tbody></tbody>`;
  const tbody = table.querySelector('tbody');

  items.forEach(it => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${it.id}</td>
      <td><input type="text" value="${it.clave}" data-field="clave" class="form-control"></td>
      <td><input type="text" value="${it.nombre}" data-field="nombre" class="form-control"></td>
      <td><input type="checkbox" ${it.activo ? 'checked' : ''} data-field="activo"></td>
      <td>
        <button class="btn btn-primary btn-sm" data-action="save">Guardar</button>
        <button class="btn btn-outline btn-sm" data-action="delete">Eliminar</button>
      </td>`;
    tr.querySelector('[data-action="save"]').onclick = () => {
      const clave = tr.querySelector('[data-field="clave"]').value.trim();
      const nombre = tr.querySelector('[data-field="nombre"]').value.trim();
      const activo = tr.querySelector('[data-field="activo"]').checked;
      onUpdate(it.id, {clave, nombre, activo});
    };
    tr.querySelector('[data-action="delete"]').onclick = () => onDelete(it.id);
    tbody.appendChild(tr);
  });

  cont.appendChild(table);
  return cont;
}

// ----- NIVELES -----
async function cargarNiveles() {
  const r = await fetch('/admin/catalogos/niveles');
  const datos = await r.json();
  const tabla = renderTabla(
    datos,
    async (id, payload) => {
      await fetch(`/admin/catalogos/niveles/${id}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      await cargarNiveles();
    },
    async (id) => {
      await fetch(`/admin/catalogos/niveles/${id}`, { method: 'DELETE' });
      await cargarNiveles();
    }
  );
  const host = document.getElementById('tablaNiveles');
  host.innerHTML = '';
  host.appendChild(tabla);
}

document.getElementById('formNivel')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const payload = {
    clave: document.getElementById('nivelClave').value,
    nombre: document.getElementById('nivelNombre').value,
    activo: true
  };
  await fetch('/admin/catalogos/niveles', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  e.target.reset();
  await cargarNiveles();
});

// ----- MUNICIPIOS -----
async function cargarMunicipios() {
  const r = await fetch('/admin/catalogos/municipios');
  const datos = await r.json();
  const tabla = renderTabla(
    datos,
    async (id, payload) => {
      await fetch(`/admin/catalogos/municipios/${id}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      await cargarMunicipios();
    },
    async (id) => {
      await fetch(`/admin/catalogos/municipios/${id}`, { method: 'DELETE' });
      await cargarMunicipios();
    }
  );
  const host = document.getElementById('tablaMunicipios');
  host.innerHTML = '';
  host.appendChild(tabla);
}
document.getElementById('formMunicipio')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const payload = {
    clave: document.getElementById('munClave').value,
    nombre: document.getElementById('munNombre').value,
    activo: true
  };
  await fetch('/admin/catalogos/municipios', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  e.target.reset();
  await cargarMunicipios();
});

// ----- ASUNTOS -----
async function cargarAsuntos() {
  const r = await fetch('/admin/catalogos/asuntos');
  const datos = await r.json();
  const tabla = renderTabla(
    datos,
    async (id, payload) => {
      await fetch(`/admin/catalogos/asuntos/${id}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
      await cargarAsuntos();
    },
    async (id) => {
      await fetch(`/admin/catalogos/asuntos/${id}`, { method: 'DELETE' });
      await cargarAsuntos();
    }
  );
  const host = document.getElementById('tablaAsuntos');
  host.innerHTML = '';
  host.appendChild(tabla);
}
document.getElementById('formAsunto')?.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const payload = {
    clave: document.getElementById('asuntoClave').value,
    nombre: document.getElementById('asuntoNombre').value,
    activo: true
  };
  await fetch('/admin/catalogos/asuntos', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  e.target.reset();
  await cargarAsuntos();
});

// Carga cuando se abre la pestaña "Catálogos"
document.getElementById('tab-catalogos')?.addEventListener('click', async ()=>{
  await Promise.all([cargarNiveles(), cargarMunicipios(), cargarAsuntos()]);
});

// Inicializar dashboard
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardApp();
});