import secrets
from datetime import datetime, timedelta


class RegistrationManager:
    def __init__(self):
        self.registration_codes = {}  # En producción, usar base de datos

    def generate_registration_code(self, expires_hours=24):
        """Generar código de registro único"""
        code = secrets.token_hex(8).upper()  # Código de 16 caracteres
        expires_at = datetime.now() + timedelta(hours=expires_hours)

        self.registration_codes[code] = {
            'expires_at': expires_at,
            'used': False,
            'max_uses': 1  # Por defecto, un solo uso
        }

        print(f"🔑 DEBUG: Código generado: {code}")
        print(f"🔑 DEBUG: Códigos en memoria: {list(self.registration_codes.keys())}")

        return code

    def validate_registration_code(self, code):
        """Validar código de registro"""
        print(f"🔑 DEBUG: Validando código: {code}")
        print(f"🔑 DEBUG: Códigos disponibles: {list(self.registration_codes.keys())}")

        if code not in self.registration_codes:
            print(f"🔑 DEBUG: Código no encontrado en registro")
            return False, 'Código de registro inválido'

        code_data = self.registration_codes[code]

        if code_data['used']:
            print(f"🔑 DEBUG: Código ya usado")
            return False, 'Este código ya ha sido utilizado'

        if datetime.now() > code_data['expires_at']:
            print(f"🔑 DEBUG: Código expirado")
            return False, 'Este código ha expirado'

        print(f"🔑 DEBUG: Código válido")
        return True, 'Código válido'

    def mark_code_used(self, code):
        """Marcar código como utilizado"""
        print(f"🔑 DEBUG: Marcando código como usado: {code}")
        if code in self.registration_codes:
            self.registration_codes[code]['used'] = True
            print(f"🔑 DEBUG: Código marcado como usado exitosamente")

    def get_active_codes(self):
        """Obtener códigos activos"""
        active_codes = {}
        for code, data in self.registration_codes.items():
            if not data['used'] and datetime.now() <= data['expires_at']:
                active_codes[code] = data
        return active_codes