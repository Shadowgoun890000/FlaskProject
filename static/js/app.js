class TurnoApp {
    constructor() {
        this.form = document.getElementById('turnoForm');
        this.modal = document.getElementById('confirmModal');
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupValidation();
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Cerrar modal
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Validación en tiempo real
        const inputs = this.form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    setupValidation() {
        // Configurar reglas de validación
        this.validationRules = {
            nombreCompleto: { required: true, minLength: 3 },
            curp: { required: true, pattern: /^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}$/ },
            nombre: { required: true },
            paterno: { required: true },
            celular: { required: true, pattern: /^[0-9]{10}$/ },
            correo: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
            nivel: { required: true },
            municipio: { required: true },
            asunto: { required: true }
        };
    }

    validateField(field) {
        const rules = this.validationRules[field.name];
        if (!rules) return true;

        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        if (rules.required && !value) {
            isValid = false;
            errorMessage = 'Este campo es obligatorio';
        } else if (rules.pattern && value && !rules.pattern.test(value.toUpperCase())) {
            isValid = false;
            errorMessage = 'Formato inválido';
        } else if (rules.minLength && value.length < rules.minLength) {
            isValid = false;
            errorMessage = `Mínimo ${rules.minLength} caracteres`;
        }

        this.setFieldError(field, isValid, errorMessage);
        return isValid;
    }

    setFieldError(field, isValid, message) {
        const errorElement = field.parentNode.querySelector('.error-message');

        if (!isValid) {
            field.classList.add('error');
            if (errorElement) {
                errorElement.textContent = message;
            } else {
                const errorMsg = document.createElement('span');
                errorMsg.className = 'error-message';
                errorMsg.textContent = message;
                field.parentNode.appendChild(errorMsg);
            }
        } else {
            field.classList.remove('error');
            if (errorElement) {
                errorElement.remove();
            }
        }
    }

    clearFieldError(field) {
        field.classList.remove('error');
        const errorElement = field.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }

    validateForm() {
        let isValid = true;
        const fields = this.form.querySelectorAll('input, select');

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    async handleSubmit(e) {
        e.preventDefault();

        if (!this.validateForm()) {
            this.showNotification('Por favor, corrige los errores en el formulario', 'error');
            return;
        }

        this.showLoading(true);

        try {
            const formData = new FormData(this.form);
            const response = await fetch('/generar_turno', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result);
            } else {
                this.handleErrors(result.errors);
            }
        } catch (error) {
            this.showNotification('Error de conexión. Intenta nuevamente.', 'error');
            console.error('Error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    showSuccess(result) {
        // Actualizar panel de información
        document.getElementById('turnoNumero').textContent = result.numero_turno;
        document.getElementById('fechaGeneracion').textContent = new Date().toLocaleString();
        document.getElementById('pdfDownload').href = result.pdf_url;

        // Mostrar sección de éxito
        document.getElementById('turnoSuccess').classList.remove('hidden');
        document.getElementById('turnoInitial').classList.add('hidden');

        // Mostrar modal de confirmación
        this.showModal();

        // Reiniciar formulario
        this.form.reset();

        this.showNotification('Turno generado exitosamente', 'success');
    }

    handleErrors(errors) {
        if (typeof errors === 'object') {
            Object.keys(errors).forEach(fieldName => {
                const field = this.form.querySelector(`[name="${fieldName}"]`);
                if (field) {
                    this.setFieldError(field, false, errors[fieldName]);
                }
            });
        } else {
            this.showNotification(errors || 'Error al generar el turno', 'error');
        }
    }

    showModal() {
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    showLoading(show) {
        const submitBtn = this.form.querySelector('button[type="submit"]');

        if (show) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="spinner"></div>Generando turno...';
            this.form.classList.add('loading');
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generar Turno';
            this.form.classList.remove('loading');
        }
    }

    showNotification(message, type = 'info') {
        // Crear notificación toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        // Estilos para el toast
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        `;

        if (type === 'success') {
            toast.style.background = '#27ae60';
        } else if (type === 'error') {
            toast.style.background = '#e74c3c';
        } else {
            toast.style.background = '#3498db';
        }

        document.body.appendChild(toast);

        // Remover después de 5 segundos
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TurnoApp();
});

// Agregar estilos de animación para las notificaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);