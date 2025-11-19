#!/usr/bin/env python3
"""
Script para ejecutar pruebas unitarias
"""

import sys
import os
import pytest


def run_tests():
    """Ejecutar todas las pruebas"""
    print("🔬 Ejecutando pruebas unitarias...")

    # Asegurarnos de que estamos en el directorio correcto
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print(f"📁 Directorio de trabajo: {project_root}")

    # Verificar que existe el directorio tests
    tests_dir = os.path.join(project_root, 'tests')
    if not os.path.exists(tests_dir):
        print(f"❌ Error: No se encuentra el directorio 'tests' en {tests_dir}")
        sys.exit(1)

    print(f"✅ Directorio de tests encontrado: {tests_dir}")

    # Verificar que hay archivos de test
    test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
    print(f"📄 Archivos de test encontrados: {len(test_files)}")
    for test_file in test_files:
        print(f"   - {test_file}")

    # Argumentos para pytest
    args = [
        'tests/',  # Directorio de tests
        '-v',  # Verboso
        '--tb=short',  # Traceback corto
        '--cov=app',  # Cobertura para app
        '--cov=registro',  # Cobertura para registro
        '--cov-report=term-missing',  # Reporte de cobertura
        '-W', 'ignore::DeprecationWarning',  # Ignorar warnings de deprecación
    ]

    try:
        exit_code = pytest.main(args)

        if exit_code == 0:
            print("✅ ¡Todas las pruebas pasaron!")
        else:
            print(f"❌ Algunas pruebas fallaron (código: {exit_code})")

        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_tests()