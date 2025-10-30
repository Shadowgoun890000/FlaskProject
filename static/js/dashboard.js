class DashboardApp {
    constructor() {
        this.init();
    }

    init() {
        this.loadEstadisticas();
        this.loadTurnos();
        this.bindEvents();
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
    }

    async loadEstadisticas() {
        try {
            const response = await fetch('/api/admin/estadisticas');
            const data = await response.json();

            this.renderEstatusChart(data.estatus);
            this.renderMunicipiosChart(data.municipios);
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

        new Chart(ctx, {
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

        new Chart(ctx, {
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
                this.loadTurnos();
                this.loadEstadisticas(); // Actualizar gráficas
            } else {
                this.showNotification('Error al actualizar estado', 'error');
            }
        } catch (error) {
            console.error('Error cambiando estado:', error);
            this.showNotification('Error de conexión', 'error');
        }
    }

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
        // Reutilizar la función de notificación existente o crear una nueva
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

// Inicializar dashboard
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardApp();
});