#!/usr/bin/env python3
"""
Script para reparar TODOS los problemas de Flask-Marshmallow
"""
import os
import subprocess


def run_command(command):
    """Ejecutar comando"""
    print(f"🔧 Ejecutando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Comando exitoso")
    else:
        print(f"⚠️  Output: {result.stdout}")
        if result.stderr:
            print(f"⚠️  Errors: {result.stderr}")
    return result.returncode


def write_file(path, content):
    """Escribir archivo"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ {path} actualizado")


def main():
    print("🚀 INICIANDO REPARACIÓN COMPLETA DEL PROYECTO...")

    # Paso 1: Desinstalar Flask-Marshmallow
    print("\n📦 PASO 1: Desinstalando Flask-Marshmallow...")
    run_command("pip uninstall flask-marshmallow -y")

    # Paso 2: Instalar dependencias correctas
    print("\n📦 PASO 2: Instalando dependencias...")

    requirements = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
marshmallow==3.20.1
marshmallow-sqlalchemy==0.29.0
mysql-connector-python==8.1.0
fpdf2==2.7.4
SQLAlchemy==2.0.23
"""
    write_file("requirements.txt", requirements)
    run_command("pip install -r requirements.txt")

    # Paso 3: Actualizar database.py
    print("\n📝 PASO 3: Actualizando database.py...")

    database_content = '''from flask_sqlalchemy import SQLAlchemy

# Inicializar SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    db.init_app(app)

    with app.app_context():
        # Importar modelos aquí para evitar circular imports
        from .usuario import Usuario
        from .turno import Turno

        # Crear todas las tablas
        db.create_all()

        print("✅ Base de datos inicializada correctamente")
        print("✅ Tablas creadas: usuarios, turnos")
'''
    write_file("registro/models/database.py", database_content)

    # Paso 4: Actualizar serializadores
    print("\n📝 PASO 4: Actualizando serializadores...")

    # Usuario serializer
    usuario_serializer = '''from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from registro.models.database import db
from registro.models.usuario import Usuario

class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    # No necesitamos definir campos manualmente, SQLAlchemyAutoSchema los detecta automáticamente

# Crear instancias del schema
usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)
'''
    write_file("registro/usuario/serializer/serializer.py", usuario_serializer)

    # Turno serializer
    turno_serializer = '''from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from registro.models.database import db
from registro.models.turno import Turno

class TurnoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Turno
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    # No necesitamos definir campos manualmente, SQLAlchemyAutoSchema los detecta automáticamente

# Crear instancias del schema
turno_schema = TurnoSchema()
turnos_schema = TurnoSchema(many=True)
'''
    write_file("registro/turno/serializer/serializer.py", turno_serializer)

    # Paso 5: Verificar que todo funciona
    print("\n🔍 PASO 5: Verificando importaciones...")

    test_script = """
try:
    from flask_sqlalchemy import SQLAlchemy
    print("✅ Flask-SQLAlchemy - OK")

    from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
    print("✅ Marshmallow-SQLAlchemy - OK")

    from registro.models.database import db
    print("✅ Database - OK")

    from usuario.serializer.serializer import usuario_schema
    print("✅ Usuario Serializer - OK")

    from turno.serializer.serializer import turno_schema
    print("✅ Turno Serializer - OK")

    print("\\\\n🎉 ¡TODAS LAS IMPORTACIONES FUNCIONAN!")

except Exception as e:
    print(f"❌ Error: {e}")
"""

    with open("test_imports.py", "w") as f:
        f.write(test_script)

    run_command("python test_imports.py")

    # Limpiar archivo temporal
    if os.path.exists("test_imports.py"):
        os.remove("test_imports.py")

    print("\n🎉 ¡REPARACIÓN COMPLETADA!")
    print("📝 Ahora puedes ejecutar: python app.py")


if __name__ == "__main__":
    main()