from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from flask_migrate import Migrate
import random
import os
from datetime import datetime
from fpdf import FPDF
import tempfile
import re
import base64
import io
import qrcode
from PIL import Image

# Importar configuración
from Config.config import config
from registro.auth import registration_manager

# Importar módulos
from registro.models.database import init_db, db
from registro.models.usuario import Usuario
from registro.models.turno import Turno
from registro.models.administrador import Administrador
from registro.models.secuencia_turno import SecuenciaTurno
from registro.usuario.viewset.viewset import UsuarioView
from registro.turno.viewset.viewset import TurnoView
from registro.usuario.serializer.serializer import usuario_schema
from registro.turno.serializer.serializer import turno_schema
from registro.models.catalogo_nivel import CatalogoNivel
from registro.models.catalogo_municipio import CatalogoMunicipio
from registro.models.catalogo_asunto import CatalogoAsunto

# Importar sistema de autenticación
from registro.auth.session_manager import SessionManager, login_required, QRGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-para-sesiones'  # Cambiar en producción

# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Inicializar base de datos
init_db(app)

migrate = Migrate(app, db)

# Instanciar views
usuario_view = UsuarioView()
turno_view = TurnoView()
session_manager = SessionManager()


@app.before_request
def check_authentication():
    """Verificar autenticación antes de cada request"""
    # Rutas que NO requieren autenticación
    public_routes = [
        'login', 'logout', 'publico', 'generar_turno',
        'descargar_pdf', 'static', 'index', 'register_admin'
    ]

    # Si la ruta actual no es pública y el usuario no está logueado
    if request.endpoint and request.endpoint not in public_routes:
        if not session_manager.is_logged_in():
            # Si es una ruta administrativa, redirigir al login
            if request.endpoint and 'admin' in request.endpoint:
                return redirect(url_for('login'))

    # Actualizar última actividad para sesiones activas
    if session_manager.is_logged_in():
        session['last_activity'] = datetime.now().isoformat()


# =============================================================================
# CLASE TurnoPDF MEJORADA CON QR
# =============================================================================

class TurnoPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'COMPROBANTE DE TURNO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_qr_code(self, qr_data, x=None, y=None, size=40):
        """Agregar código QR al PDF"""
        try:
            # Generar QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Guardar temporalmente
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "temp_qr.png")
            qr_img.save(temp_path)

            # Posicionamiento
            if x is None:
                x = (self.w - size) / 2
            if y is None:
                y = self.get_y()

            # Insertar imagen
            self.image(temp_path, x=x, y=y, w=size)

            # Limpiar archivo temporal
            os.unlink(temp_path)

            return size

        except Exception as e:
            print(f"Error generando QR: {e}")
            return 0


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def obtener_siguiente_turno(municipio):
    """
    Obtiene el siguiente número de turno consecutivo para un municipio
    """
    try:
        # Buscar o crear secuencia para el municipio
        secuencia = SecuenciaTurno.query.filter_by(municipio=municipio).first()

        if not secuencia:
            secuencia = SecuenciaTurno(municipio=municipio, siguiente_numero=1)
            db.session.add(secuencia)
            db.session.flush()  # Para obtener el ID sin commit
        else:
            secuencia.siguiente_numero += 1
            secuencia.fecha_actualizacion = datetime.utcnow()

        # Formatear número de turno: MUNICIPIO-0001
        numero_turno = f"{municipio.upper()}-{secuencia.siguiente_numero:04d}"

        return numero_turno

    except Exception as e:
        db.session.rollback()
        print(f"Error en secuencia de turno: {e}")
        # Fallback: generar número aleatorio
        return f"{municipio.upper()}-{random.randint(1000, 9999)}"


def validar_datos(datos):
    errores = {}

    # Validar campos obligatorios
    campos_obligatorios = [
        'nombre_completo', 'curp', 'nombre', 'paterno',
        'celular', 'correo', 'nivel', 'municipio', 'asunto'
    ]

    for campo in campos_obligatorios:
        if not datos.get(campo) or not datos.get(campo).strip():
            errores[campo] = 'Este campo es obligatorio'

    # Validar formato CURP
    if datos.get('curp'):
        curp = datos['curp'].upper().strip()
        curp_pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9A-Z]$'
        if not re.match(curp_pattern, curp):
            errores['curp'] = 'Formato de CURP inválido'

    # Validar teléfono y celular
    if datos.get('telefono'):
        telefono = datos['telefono'].strip()
        if telefono and (not telefono.isdigit() or len(telefono) != 10):
            errores['telefono'] = 'El teléfono debe contener exactamente 10 números'

    if datos.get('celular'):
        celular = datos['celular'].strip()
        if not celular.isdigit() or len(celular) != 10:
            errores['celular'] = 'El celular debe contener exactamente 10 números'

    # Validar email
    if datos.get('correo'):
        correo = datos['correo'].strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, correo):
            errores['correo'] = 'Formato de correo electrónico inválido'

    return errores


def generar_pdf_comprobante(datos, numero_turno):
    pdf = TurnoPDF()
    pdf.add_page()

    # Información del turno
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'COMPROBANTE DE TURNO', 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Número de Turno: {numero_turno}', 0, 1)
    pdf.cell(0, 10, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(10)

    # Datos del solicitante
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Datos del Solicitante:', 0, 1)
    pdf.set_font('Arial', '', 11)

    pdf.cell(0, 8, f'Nombre completo: {datos["nombre_completo"]}', 0, 1)
    pdf.cell(0, 8, f'CURP: {datos["curp"]}', 0, 1)
    pdf.cell(0, 8, f'Nombre: {datos["nombre"]}', 0, 1)
    pdf.cell(0, 8, f'Apellido Paterno: {datos["paterno"]}', 0, 1)
    if datos['materno']:
        pdf.cell(0, 8, f'Apellido Materno: {datos["materno"]}', 0, 1)

    pdf.cell(0, 8, f'Teléfono: {datos["telefono"] or "No proporcionado"}', 0, 1)
    pdf.cell(0, 8, f'Celular: {datos["celular"]}', 0, 1)
    pdf.cell(0, 8, f'Correo: {datos["correo"]}', 0, 1)
    pdf.ln(10)

    # Información académica
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Información Académica:', 0, 1)
    pdf.set_font('Arial', '', 11)

    niveles = {
        'preescolar': 'Preescolar',
        'primaria': 'Primaria',
        'secundaria': 'Secundaria',
        'bachillerato': 'Bachillerato',
        'licenciatura': 'Licenciatura',
        'posgrado': 'Posgrado'
    }

    municipios = {
        'aguascalientes': 'Aguascalientes',
        'zacatecas': 'Zacatecas',
        'jalisco': 'Jalisco',
        'guanajuato': 'Guanajuato',
        'san-luis-potosi': 'San Luis Potosí'
    }

    asuntos = {
        'inscripcion': 'Inscripción',
        'reinscripcion': 'Reinscripción',
        'certificacion': 'Certificación',
        'tramite-documentos': 'Trámite de documentos',
        'informacion': 'Información general'
    }

    pdf.cell(0, 8, f'Nivel: {niveles.get(datos["nivel"], datos["nivel"])}', 0, 1)
    pdf.cell(0, 8, f'Municipio: {municipios.get(datos["municipio"], datos["municipio"])}', 0, 1)
    pdf.cell(0, 8, f'Asunto: {asuntos.get(datos["asunto"], datos["asunto"])}', 0, 1)
    pdf.ln(10)

    # Generar y agregar código QR con la CURP
    try:
        qr_data = f"CURP: {datos['curp']}\nTurno: {numero_turno}\nFecha: {datetime.now().strftime('%d/%m/%Y')}\nNombre: {datos['nombre_completo']}"
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Código QR de verificación:', 0, 1)
        pdf.ln(5)

        # Agregar QR usando el método de la clase
        qr_size = pdf.add_qr_code(qr_data, size=40)
        pdf.ln(qr_size + 5)

    except Exception as e:
        print(f"Error generando QR en PDF: {e}")
        pdf.cell(0, 10, 'Error generando código QR', 0, 1)

    # Guardar PDF
    temp_dir = tempfile.gettempdir()
    pdf_filename = f"comprobante_turno_{numero_turno}.pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)
    pdf.output(pdf_path)

    return pdf_path


def generate_captcha():
    """Generar texto CAPTCHA aleatorio"""
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    captcha_text = ''.join(random.choice(characters) for _ in range(6))
    return captcha_text, captcha_text  # Texto y respuesta


# =============================================================================
# RUTAS DE REGISTRO DE ADMINISTRADORES
# =============================================================================

@app.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    """Registro de nuevo administrador"""
    # Si ya está logueado, redirigir al dashboard
    if session_manager.is_logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            data = request.form
            registration_code = data.get('registration_code', '').strip().upper()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            nombre_completo = data.get('nombre_completo', '').strip()

            print(f"🔍 DEBUG: Código recibido: {registration_code}")
            print(f"🔍 DEBUG: Usuario: {username}")
            print(f"🔍 DEBUG: Email: {email}")

            # Validar código de registro
            is_valid, code_message = registration_manager.validate_registration_code(registration_code)
            print(f"🔍 DEBUG: Validación código: {is_valid} - {code_message}")
            print(f"🔍 DEBUG: Códigos activos: {registration_manager.get_active_codes()}")

            if not is_valid:
                flash(f'Error en código de registro: {code_message}', 'error')
                return render_template('register.html')

            # Validar que las contraseñas coincidan
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('register.html')

            # Validar username
            is_valid_username, username_msg = Administrador.validate_username(username)
            if not is_valid_username:
                flash(f'Error en usuario: {username_msg}', 'error')
                return render_template('register.html')

            # Validar email
            is_valid_email, email_msg = Administrador.validate_email(email)
            if not is_valid_email:
                flash(f'Error en email: {email_msg}', 'error')
                return render_template('register.html')

            # Verificar si el usuario ya existe
            if Administrador.query.filter_by(username=username).first():
                flash('Este nombre de usuario ya está en uso', 'error')
                return render_template('register.html')

            if Administrador.query.filter_by(email=email).first():
                flash('Este correo electrónico ya está registrado', 'error')
                return render_template('register.html')

            # Crear nuevo administrador
            nuevo_admin = Administrador(
                username=username,
                email=email,
                nombre_completo=nombre_completo,
                rol='operador'  # Por defecto, rol operador
            )
            nuevo_admin.set_password(password)

            db.session.add(nuevo_admin)
            print(f"🔍 DEBUG: Administrador creado - {username}")

            # Marcar código como utilizado
            registration_manager.mark_code_used(registration_code)
            print(f"🔍 DEBUG: Código marcado como usado: {registration_code}")

            db.session.commit()
            print("🔍 DEBUG: Commit realizado en la base de datos")

            flash('✅ Cuenta de administrador creada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))

        except ValueError as e:
            print(f"🔍 DEBUG: ValueError: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            print(f"🔍 DEBUG: Exception: {str(e)}")
            print(f"🔍 DEBUG: Tipo de excepción: {type(e)}")
            import traceback
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            flash(f'Error al crear la cuenta: {str(e)}', 'error')

    return render_template('register.html')


@app.route('/admin/generate-code')
@login_required
def generate_registration_code():
    """Generar código de registro (solo para administradores logueados)"""
    try:
        code = registration_manager.generate_registration_code()

        # Log de quién generó el código
        admin_username = session_manager.get_admin_username()
        print(f"Código generado por {admin_username}: {code}")

        return jsonify({
            'success': True,
            'code': code,
            'message': f'Código generado: {code} - Válido por 24 horas'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/active-codes')
@login_required
def get_active_codes():
    """Obtener códigos activos (solo para administradores)"""
    active_codes = registration_manager.get_active_codes()
    return jsonify({
        'success': True,
        'active_codes': len(active_codes),
        'codes': active_codes
    })


# =============================================================================
# RUTAS PÚBLICAS
# =============================================================================

@app.route('/')
def index():
    """Página principal - Redirige según sesión activa"""
    if session_manager.is_logged_in():
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/publico')
def publico():
    """Formulario público - Siempre accesible"""
    is_logged_in = session_manager.is_logged_in()
    admin_username = session_manager.get_admin_username() if is_logged_in else None
    return render_template('formulario.html',
                         is_logged_in=is_logged_in,
                         admin_username=admin_username)

def _public_list(Model):
    # Solo activos; orden alfabético
    objs = Model.query.filter_by(activo=True).order_by(Model.nombre.asc()).all()
    return jsonify([o.to_dict() for o in objs])

@app.route('/api/catalogos/niveles', methods=['GET'])
def public_niveles():
    return _public_list(CatalogoNivel)

@app.route('/api/catalogos/municipios', methods=['GET'])
def public_municipios():
    return _public_list(CatalogoMunicipio)

@app.route('/api/catalogos/asuntos', methods=['GET'])
def public_asuntos():
    return _public_list(CatalogoAsunto)

@app.route('/publico/modificar')
def modificar_turno_form():
    """Formulario para modificar turno (público)"""
    is_logged_in = session_manager.is_logged_in()
    admin_username = session_manager.get_admin_username() if is_logged_in else None
    return render_template('modificar_turno.html',
                         is_logged_in=is_logged_in,
                         admin_username=admin_username)

@app.route('/admin')
def admin_redirect():
    """Redirección para /admin"""
    if session_manager.is_logged_in():
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/generar_turno', methods=['POST'])
def generar_turno():
    try:
        # Iniciar transacción
        db.session.begin_nested()

        # Obtener datos del formulario
        datos = {
            'nombre_completo': request.form.get('nombreCompleto', '').strip(),
            'curp': request.form.get('curp', '').strip().upper(),
            'nombre': request.form.get('nombre', '').strip(),
            'paterno': request.form.get('paterno', '').strip(),
            'materno': request.form.get('materno', '').strip(),
            'telefono': request.form.get('telefono', '').strip(),
            'celular': request.form.get('celular', '').strip(),
            'correo': request.form.get('correo', '').strip().lower(),
            'nivel': request.form.get('nivel', '').strip(),
            'municipio': request.form.get('municipio', '').strip(),
            'asunto': request.form.get('asunto', '').strip()
        }

        # Validaciones del servidor
        errores = validar_datos(datos)
        if errores:
            db.session.rollback()
            return jsonify({'success': False, 'errors': errores})

        # Verificar si ya existe un usuario con la misma CURP y turno pendiente
        usuario_existente = Usuario.query.filter_by(curp=datos['curp']).first()

        if usuario_existente:
            # Verificar si ya tiene un turno pendiente para el mismo municipio y asunto
            turno_duplicado = Turno.query.filter_by(
                usuario_id=usuario_existente.id,
                municipio=datos['municipio'],
                asunto=datos['asunto'],
                estado='pendiente'
            ).first()

            if turno_duplicado:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Ya tiene un turno pendiente ({turno_duplicado.numero_turno}) para este municipio y asunto. No puede generar otro hasta que sea atendido.'
                })

        # Buscar o crear usuario
        if not usuario_existente:
            usuario_data = {
                'curp': datos['curp'],
                'nombre_completo': datos['nombre_completo'],
                'nombre': datos['nombre'],
                'paterno': datos['paterno'],
                'materno': datos['materno'],
                'telefono': datos['telefono'],
                'celular': datos['celular'],
                'correo': datos['correo']
            }
            usuario_existente = usuario_schema.load(usuario_data)
            db.session.add(usuario_existente)
            db.session.flush()  # Para obtener el ID

        # Generar turno consecutivo
        numero_turno = obtener_siguiente_turno(datos['municipio'])

        # Verificar duplicidad de número de turno
        turno_existente = Turno.query.filter_by(numero_turno=numero_turno).first()
        if turno_existente:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Error al generar turno. Por favor, intente nuevamente.'
            })

        # Crear turno
        turno = Turno(
            numero_turno=numero_turno,
            nivel=datos['nivel'],
            municipio=datos['municipio'],
            asunto=datos['asunto'],
            usuario_id=usuario_existente.id,
            estado='pendiente'
        )

        db.session.add(turno)
        db.session.commit()

        # Generar PDF
        pdf_path = generar_pdf_comprobante(datos, numero_turno)

        return jsonify({
            'success': True,
            'numero_turno': numero_turno,
            'turno_id': turno.id,
            'usuario_id': usuario_existente.id,
            'pdf_url': f'/descargar_pdf/{os.path.basename(pdf_path)}',
            'message': 'Turno generado exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        # Capturar error de duplicidad de primary key
        if 'duplicate key value' in str(e).lower() or 'unique constraint' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'El turno ya existe en el sistema. Por favor, verifique sus datos e intente nuevamente.'
            })
        return jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'})


@app.route('/descargar_pdf/<filename>')
def descargar_pdf(filename):
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, filename)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return "Archivo no encontrado", 404


# =============================================================================
# RUTAS PARA MODIFICACIÓN PÚBLICA DE TURNOS
# =============================================================================
@app.route('/publico/buscar_turno', methods=['POST'])
def buscar_turno_publico():
    """Buscar turno por CURP y número para modificación"""
    try:
        curp = request.form.get('curp', '').strip().upper()
        numero_turno = request.form.get('numero_turno', '').strip().upper()

        if not curp or not numero_turno:
            return jsonify({'success': False, 'error': 'CURP y número de turno son obligatorios'})

        # Buscar turno con el usuario asociado
        turno = Turno.query.filter_by(numero_turno=numero_turno).join(Usuario).filter(Usuario.curp == curp).first()

        if not turno:
            return jsonify({'success': False, 'error': 'No se encontró el turno con los datos proporcionados'})

        # Solo permitir modificación si está pendiente
        if turno.estado != 'pendiente':
            return jsonify({
                'success': False,
                'error': f'No se puede modificar un turno con estado "{turno.estado}". Solo se permiten turnos pendientes.'
            })

        # Preparar datos para el formulario
        datos_turno = {
            'numero_turno': turno.numero_turno,
            'curp': turno.usuario.curp,
            'nombre_completo': turno.usuario.nombre_completo,
            'nombre': turno.usuario.nombre,
            'paterno': turno.usuario.paterno,
            'materno': turno.usuario.materno or '',
            'telefono': turno.usuario.telefono or '',
            'celular': turno.usuario.celular,
            'correo': turno.usuario.correo,
            'nivel': turno.nivel,
            'municipio': turno.municipio,
            'asunto': turno.asunto,
            'fecha_creacion': turno.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        }

        return jsonify({'success': True, 'turno': datos_turno})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error en la búsqueda: {str(e)}'})


@app.route('/publico/actualizar_turno', methods=['POST'])
def actualizar_turno_publico():
    """Actualizar turno desde la interfaz pública"""
    try:
        data = request.form
        curp = data.get('curp', '').strip().upper()
        numero_turno = data.get('numero_turno', '').strip().upper()

        # Buscar turno y usuario
        turno = Turno.query.filter_by(numero_turno=numero_turno).join(Usuario).filter(Usuario.curp == curp).first()

        if not turno:
            return jsonify({'success': False, 'error': 'Turno no encontrado'})

        if turno.estado != 'pendiente':
            return jsonify({'success': False, 'error': 'Solo se pueden modificar turnos pendientes'})

        # Validar datos
        datos_actualizados = {
            'nombre_completo': data.get('nombreCompleto', '').strip(),
            'curp': curp,
            'nombre': data.get('nombre', '').strip(),
            'paterno': data.get('paterno', '').strip(),
            'materno': data.get('materno', '').strip(),
            'telefono': data.get('telefono', '').strip(),
            'celular': data.get('celular', '').strip(),
            'correo': data.get('correo', '').strip().lower(),
            'nivel': data.get('nivel', '').strip(),
            'municipio': data.get('municipio', '').strip(),
            'asunto': data.get('asunto', '').strip()
        }

        # Validaciones
        errores = validar_datos(datos_actualizados)
        if errores:
            return jsonify({'success': False, 'errors': errores})

        # Actualizar usuario
        usuario = turno.usuario
        usuario.nombre_completo = datos_actualizados['nombre_completo']
        usuario.nombre = datos_actualizados['nombre']
        usuario.paterno = datos_actualizados['paterno']
        usuario.materno = datos_actualizados['materno']
        usuario.telefono = datos_actualizados['telefono']
        usuario.celular = datos_actualizados['celular']
        usuario.correo = datos_actualizados['correo']
        usuario.fecha_actualizacion = datetime.utcnow()

        # Actualizar turno (solo algunos campos)
        turno.nivel = datos_actualizados['nivel']
        turno.municipio = datos_actualizados['municipio']
        turno.asunto = datos_actualizados['asunto']

        db.session.commit()

        # Generar nuevo PDF
        pdf_path = generar_pdf_comprobante(datos_actualizados, numero_turno)

        return jsonify({
            'success': True,
            'message': 'Turno actualizado correctamente',
            'pdf_url': f'/descargar_pdf/{os.path.basename(pdf_path)}',
            'numero_turno': numero_turno
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error al actualizar: {str(e)}'})

# =============================================================================
# RUTAS DE AUTENTICACIÓN
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        captcha_input = request.form.get('captcha_input', '').upper()
        captcha_answer = request.form.get('captcha_answer', '')

        # Validar CAPTCHA
        if captcha_input != captcha_answer:
            flash('Código CAPTCHA incorrecto')
            captcha_text, captcha_answer = generate_captcha()
            return render_template('login.html', captcha_text=captcha_text, captcha_answer=captcha_answer)

        # Validar administrador
        admin = Administrador.query.filter_by(username=username, activo=True).first()
        if admin and admin.check_password(password):
            session_manager.login_admin(admin.id, admin.username)
            admin.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas')

    captcha_text, captcha_answer = generate_captcha()
    return render_template('login.html', captcha_text=captcha_text, captcha_answer=captcha_answer)


@app.route('/admin/logout')
def logout():
    """Cerrar sesión y redirigir adecuadamente"""
    username = session_manager.get_admin_username()
    session_manager.logout_admin()
    flash(f'Sesión cerrada correctamente. Hasta pronto {username}!', 'info')
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@login_required
def dashboard():
    # Estadísticas para el dashboard
    stats = {
        'total_turnos': Turno.query.count(),
        'pendientes': Turno.query.filter_by(estado='pendiente').count(),
        'resueltos': Turno.query.filter_by(estado='resuelto').count(),
        'total_municipios': db.session.query(Turno.municipio).distinct().count()
    }

    municipios = ['aguascalientes', 'zacatecas', 'jalisco', 'guanajuato', 'san-luis-potosi']

    return render_template('dashboard.html',
                           stats=stats,
                           municipios=municipios,
                           admin_username=session_manager.get_admin_username())


# =============================================================================
# API PARA DASHBOARD
# =============================================================================

@app.route('/api/admin/turnos')
@login_required
def api_admin_turnos():
    """Obtener turnos para el dashboard con filtros"""
    estado = request.args.get('estado', '')
    municipio = request.args.get('municipio', '')

    query = Turno.query.join(Usuario)

    if estado:
        query = query.filter(Turno.estado == estado)
    if municipio:
        query = query.filter(Turno.municipio == municipio)

    turnos = query.order_by(Turno.fecha_creacion.desc()).limit(50).all()

    result = []
    for turno in turnos:
        result.append({
            'id': turno.id,
            'numero_turno': turno.numero_turno,
            'estado': turno.estado,
            'municipio': turno.municipio,
            'asunto': turno.asunto,
            'fecha_creacion': turno.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'usuario': {
                'nombre_completo': turno.usuario.nombre_completo,
                'curp': turno.usuario.curp,
                'celular': turno.usuario.celular
            }
        })

    return jsonify(result)


@app.route('/api/admin/buscar')
@login_required
def api_admin_buscar():
    """Búsqueda de turnos por CURP o nombre"""
    curp = request.args.get('curp', '')
    nombre = request.args.get('nombre', '')

    query = Turno.query.join(Usuario)

    if curp:
        query = query.filter(Usuario.curp.ilike(f'%{curp}%'))
    if nombre:
        query = query.filter(Usuario.nombre_completo.ilike(f'%{nombre}%'))

    resultados = query.order_by(Turno.fecha_creacion.desc()).limit(20).all()

    result = []
    for turno in resultados:
        result.append({
            'id': turno.id,
            'numero_turno': turno.numero_turno,
            'estado': turno.estado,
            'municipio': turno.municipio,
            'asunto': turno.asunto,
            'fecha_creacion': turno.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'usuario': {
                'nombre_completo': turno.usuario.nombre_completo,
                'curp': turno.usuario.curp,
                'celular': turno.usuario.celular,
                'correo': turno.usuario.correo
            }
        })

    return jsonify(result)


@app.route('/api/admin/turnos/<int:turno_id>', methods=['PUT'])
@login_required
def api_admin_actualizar_turno(turno_id):
    """Actualizar estado de turno"""
    try:
        turno = Turno.query.get_or_404(turno_id)
        data = request.get_json()

        if 'estado' in data:
            turno.estado = data['estado']
            if data['estado'] in ['atendido', 'resuelto']:
                turno.atendido_por = session_manager.get_admin_id()
                turno.fecha_atencion = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': 'Turno actualizado correctamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/estadisticas')
@login_required
def api_admin_estadisticas():
    """Estadísticas para gráficas"""
    # Datos para gráfica de estatus
    estatus_data = db.session.query(
        Turno.estado,
        db.func.count(Turno.id)
    ).group_by(Turno.estado).all()

    # Datos para gráfica de municipios
    municipios_data = db.session.query(
        Turno.municipio,
        db.func.count(Turno.id)
    ).group_by(Turno.municipio).all()

    return jsonify({
        'estatus': [{'estado': e[0], 'cantidad': e[1]} for e in estatus_data],
        'municipios': [{'municipio': m[0], 'cantidad': m[1]} for m in municipios_data]
    })


# =============================================================================
# RUTAS API REST EXISTENTES (mantener compatibilidad)
# =============================================================================

@app.route('/api/usuarios', methods=['GET', 'POST'])
def api_usuarios():
    if request.method == 'GET':
        return usuario_view.get_usuarios()
    elif request.method == 'POST':
        return usuario_view.create_usuario()


@app.route('/api/usuarios/<int:usuario_id>', methods=['GET', 'PUT', 'DELETE'])
def api_usuario(usuario_id):
    if request.method == 'GET':
        return usuario_view.get_usuario(usuario_id)
    elif request.method == 'PUT':
        return usuario_view.update_usuario(usuario_id)
    elif request.method == 'DELETE':
        return usuario_view.delete_usuario(usuario_id)


@app.route('/api/turnos', methods=['GET', 'POST'])
def api_turnos():
    if request.method == 'GET':
        return turno_view.get_turnos()
    elif request.method == 'POST':
        return turno_view.create_turno()


@app.route('/api/turnos/<int:turno_id>', methods=['GET', 'PUT', 'DELETE'])
def api_turno(turno_id):
    if request.method == 'GET':
        return turno_view.get_turno(turno_id)
    elif request.method == 'PUT':
        return turno_view.update_turno(turno_id)
    elif request.method == 'DELETE':
        return turno_view.delete_turno(turno_id)


def _crud_list(Model):
    objs = Model.query.order_by(Model.nombre.asc()).all()
    return jsonify([o.to_dict() for o in objs])

def _crud_create(Model, data):
    obj = Model(clave=data.get('clave','').strip().lower(),
                nombre=data.get('nombre','').strip(),
                activo=bool(data.get('activo', True)))
    db.session.add(obj)
    db.session.commit()
    return jsonify(obj.to_dict()), 201

def _crud_update(Model, item_id, data):
    obj = Model.query.get_or_404(item_id)
    if 'clave' in data: obj.clave = data['clave'].strip().lower()
    if 'nombre' in data: obj.nombre = data['nombre'].strip()
    if 'activo' in data: obj.activo = bool(data['activo'])
    db.session.commit()
    return jsonify(obj.to_dict())

def _crud_delete(Model, item_id):
    obj = Model.query.get_or_404(item_id)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({"success": True})

# --------- NIVELES ---------
@app.route('/admin/catalogos/niveles', methods=['GET'])
@login_required
def list_niveles():
    return _crud_list(CatalogoNivel)

@app.route('/admin/catalogos/niveles', methods=['POST'])
@login_required
def create_nivel():
    return _crud_create(CatalogoNivel, request.get_json() or {})

@app.route('/admin/catalogos/niveles/<int:item_id>', methods=['PATCH','PUT'])
@login_required
def update_nivel(item_id):
    return _crud_update(CatalogoNivel, item_id, request.get_json() or {})

@app.route('/admin/catalogos/niveles/<int:item_id>', methods=['DELETE'])
@login_required
def delete_nivel(item_id):
    return _crud_delete(CatalogoNivel, item_id)

# --------- MUNICIPIOS ---------
@app.route('/admin/catalogos/municipios', methods=['GET'])
@login_required
def list_municipios():
    return _crud_list(CatalogoMunicipio)

@app.route('/admin/catalogos/municipios', methods=['POST'])
@login_required
def create_municipio():
    return _crud_create(CatalogoMunicipio, request.get_json() or {})

@app.route('/admin/catalogos/municipios/<int:item_id>', methods=['PATCH','PUT'])
@login_required
def update_municipio(item_id):
    return _crud_update(CatalogoMunicipio, item_id, request.get_json() or {})

@app.route('/admin/catalogos/municipios/<int:item_id>', methods=['DELETE'])
@login_required
def delete_municipio(item_id):
    return _crud_delete(CatalogoMunicipio, item_id)

# --------- ASUNTOS ---------
@app.route('/admin/catalogos/asuntos', methods=['GET'])
@login_required
def list_asuntos():
    return _crud_list(CatalogoAsunto)

@app.route('/admin/catalogos/asuntos', methods=['POST'])
@login_required
def create_asunto():
    return _crud_create(CatalogoAsunto, request.get_json() or {})

@app.route('/admin/catalogos/asuntos/<int:item_id>', methods=['PATCH','PUT'])
@login_required
def update_asunto(item_id):
    return _crud_update(CatalogoAsunto, item_id, request.get_json() or {})

@app.route('/admin/catalogos/asuntos/<int:item_id>', methods=['DELETE'])
@login_required
def delete_asunto(item_id):
    return _crud_delete(CatalogoAsunto, item_id)

# =============================================================================
# INICIO DE LA APLICACIÓN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)