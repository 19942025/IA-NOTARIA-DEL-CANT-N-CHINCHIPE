import json
import random
import re
import time
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def generate_id() -> int:
    return int(time.time() * 1000) + random.randint(0, 999)


class LocalDatabase:
    def __init__(self):
        self.db = {}
        self.reset()

    def reset(self) -> None:
        self.db = {
            'users': [],
            'clients': [],
            'procedures': [],
            'document_types': [],
            'templates': [],
            'documents': [],
            'document_versions': [],
            'notifications': [],
            'audit_logs': [],
            'ai_conversations': [],
            'ai_messages': []
        }
        self.seed_demo_data()

    def get_collection(self, name: str) -> List[Dict[str, Any]]:
        return self.db.get(name, [])

    def find_by_id(self, collection: str, id_value: Any) -> Optional[Dict[str, Any]]:
        return next((item for item in self.get_collection(collection) if item['id'] == id_value), None)

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return next(
            (item for item in self.get_collection(collection) if all(item.get(k) == v for k, v in query.items())),
            None
        )

    def find_many(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [item for item in self.get_collection(collection) if all(item.get(k) == v for k, v in query.items())]

    def insert(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if collection not in self.db:
            self.db[collection] = []

        new_item = {
            'id': data.get('id', generate_id()),
            'createdAt': data.get('createdAt', now_iso()),
            **data
        }
        self.db[collection].append(new_item)
        return new_item

    def update(self, collection: str, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        item = self.find_by_id(collection, id_value)
        if not item:
            return None
        item.update({**data, 'updatedAt': now_iso()})
        return item

    def delete(self, collection: str, id_value: Any) -> bool:
        original = self.get_collection(collection)
        new_list = [item for item in original if item['id'] != id_value]
        if len(new_list) == len(original):
            return False
        self.db[collection] = new_list
        return True

    def seed_demo_data(self) -> None:
        demo_users = [
            {'id': 1, 'username': 'admin', 'password': 'password', 'fullname': 'Dr. Ramiro Toro (Admin)', 'role': 'ADMINISTRADOR', 'active': True},
            {'id': 2, 'username': 'personal', 'password': 'password', 'fullname': 'Ing. Sofía Jumbo', 'role': 'PERSONAL_NOTARIAL', 'active': True},
            {'id': 3, 'username': 'notario', 'password': 'password', 'fullname': 'Dr. Patricio Ordóñez (Notario)', 'role': 'NOTARIO', 'active': True}
        ]
        for user in demo_users:
            self.insert('users', user)

        demo_clients = [
            {'id': 101, 'cedula': '1900123454', 'names': 'Juan Carlos', 'surnames': 'Pérez Medina', 'dob': '1985-05-12', 'maritalStatus': 'SOLTERO', 'nationality': 'Ecuatoriana', 'address': 'Av. Progreso y Loja, Zumba', 'phone': '0987654321', 'email': 'juan.perez@example.com', 'notes': 'Cliente frecuente, agricultor de la zona.'},
            {'id': 102, 'cedula': '1104567894', 'names': 'María Augusta', 'surnames': 'Ortiz Cevallos', 'dob': '1990-11-23', 'maritalStatus': 'CASADO', 'nationality': 'Ecuatoriana', 'address': 'Calle 12 de Febrero, Zumba', 'phone': '0991234567', 'email': 'maria.ortiz@example.com', 'notes': 'Requiere agilidad en trámites por viaje.'},
            {'id': 103, 'cedula': '1723456784', 'names': 'José Vicente', 'surnames': 'Guerrero Silva', 'dob': '1972-04-05', 'maritalStatus': 'DIVORCIADO', 'nationality': 'Ecuatoriana', 'address': 'Barrio El Progreso, Chito', 'phone': '0982345678', 'email': 'jose.guerrero@example.com', 'notes': 'Propietario de finca cafetalera.'}
        ]
        for client in demo_clients:
            self.insert('clients', client)

        demo_doc_types = [
            {'id': 1, 'name': 'Poder Especial / General', 'description': 'Autorización legal otorgada a un tercero para gestionar asuntos legales o comerciales.', 'active': True},
            {'id': 2, 'name': 'Declaración Juramentada', 'description': 'Manifestación escrita bajo juramento sobre hechos de conocimiento del declarante.', 'active': True},
            {'id': 3, 'name': 'Autorización de Viaje de Menores', 'description': 'Permiso notarial que otorgan los padres para la salida del país de sus hijos.', 'active': True},
            {'id': 4, 'name': 'Contrato de Compraventa Vehicular', 'description': 'Acuerdo de transferencia de propiedad de un vehículo automotor entre comparecientes.', 'active': True},
            {'id': 5, 'name': 'Acta de Reconocimiento de Firma', 'description': 'Certificación notarial de que las firmas en un documento privado corresponden a los comparecientes.', 'active': True}
        ]
        for doc_type in demo_doc_types:
            self.insert('document_types', doc_type)

        demo_templates = [
            {
                'id': 201,
                'name': 'Plantilla de Poder Especial',
                'description': 'Poder especial estándar para representación judicial o administrativa en Zumba.',
                'typeId': 1,
                'version': '1.0',
                'active': True,
                'updatedAt': now_iso(),
                'updatedBy': 'Dr. Ramiro Toro (Admin)',
                'variables': ['COMPARECIENTE', 'CEDULA_COMPARECIENTE', 'APODERADO', 'CEDULA_APODERADO', 'OBJETO_PODER', 'CIUDAD', 'FECHA'],
                'content': (
                    'CONSTITUCIÓN DE PODER ESPECIAL\n'
                    'En la ciudad de {{CIUDAD}}, Cantón Chinchipe, Provincia de Zamora Chinchipe, República del Ecuador, a los {{FECHA}}, ante mí, Dr. Patricio Ordóñez, Notario Público de este Cantón, comparece de manera libre y voluntaria el/la señor(a) {{COMPARECIENTE}}, portador(a) de la cédula de ciudadanía No. {{CEDULA_COMPARECIENTE}}, de estado civil soltero, de nacionalidad ecuatoriana, domiciliado en este cantón, persona legalmente capaz para contratar y obligarse, a quien de conocer doy fe; y, manifiesta que otorga PODER ESPECIAL amplio y suficiente, cuanto en derecho sea necesario, a favor del/la señor(a) {{APODERADO}}, con cédula de ciudadanía No. {{CEDULA_APODERADO}}, para que en su nombre y representación realice las siguientes gestiones y actos administrativos:\n'
                    '-------------------------------------------------------------------------------------\n'
                    '{{OBJETO_PODER}}\n'
                    '-------------------------------------------------------------------------------------\n'
                    'El/la mandatario(a) queda facultado(a) para realizar todas las diligencias necesarias, firmar solicitudes, minutas, actas públicas y privadas relacionadas directamente con este encargo. El compareciente se ratifica en el contenido de este instrumento público.\n'
                    'Para constancia y validez, firma conjuntamente con el suscrito Notario.'
                )
            }
        ]
        for template in demo_templates:
            self.insert('templates', template)


class AuditService:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def log(self, user: Dict[str, Any], action: str, details: str, ip: str = '127.0.0.1') -> None:
        self.db.insert('audit_logs', {
            'userId': user['id'],
            'username': user['username'],
            'role': user['role'],
            'action': action,
            'timestamp': now_iso(),
            'details': details,
            'ip': ip
        })

    def get_action_badge_class(self, action: str) -> str:
        mapping = {
            'INICIO_SESION': 'badge-success',
            'CERRAR_SESION': 'badge-secondary',
            'CAMBIO_ROL_DEBUG': 'badge-warning',
            'CREACION_CLIENTE': 'badge-info',
            'EDICION_CLIENTE': 'badge-info',
            'ELIMINACION_CLIENTE': 'badge-danger',
            'CREACION_TRAMITE': 'badge-info',
            'EDICION_TRAMITE': 'badge-info',
            'ELIMINACION_TRAMITE': 'badge-danger',
            'CREACION_PLANTILLA': 'badge-success',
            'EDICION_PLANTILLA': 'badge-warning',
            'ESTADO_PLANTILLA': 'badge-secondary',
            'GENERACION_BORRADOR': 'badge-success',
            'EDICION_MANUAL_DOCUMENTO': 'badge-warning',
            'ENVIO_A_REVISION': 'badge-info',
            'APROBACION_DOCUMENTO': 'badge-success',
            'RECHAZO_DOCUMENTO': 'badge-danger',
            'DESCARGA_WORD': 'badge-secondary',
            'IMPRESION_PDF': 'badge-secondary'
        }
        return mapping.get(action, 'badge-secondary')

    def get_role_badge_class(self, role: str) -> str:
        mapping = {
            'ADMINISTRADOR': 'badge-danger',
            'PERSONAL_NOTARIAL': 'badge-info',
            'NOTARIO': 'badge-success'
        }
        return mapping.get(role, 'badge-secondary')


class AuthService:
    def __init__(self, db: LocalDatabase, audit: AuditService):
        self.db = db
        self.audit = audit
        self.current_user: Optional[Dict[str, Any]] = None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user

    def login(self, username: str, password: str) -> Dict[str, Any]:
        user = self.db.find_one('users', {'username': username, 'active': True})
        if not user:
            raise ValueError('El usuario no existe o está inactivo.')
        if user['password'] != password:
            raise ValueError('Contraseña incorrecta.')

        session_user = {
            'id': user['id'],
            'username': user['username'],
            'fullname': user['fullname'],
            'role': user['role'],
            'token': f'mock-jwt-token-{random.randint(1000, 9999)}'
        }
        self.current_user = session_user
        self.audit.log(user=session_user, action='INICIO_SESION', details=f'Usuario {username} inició sesión en el sistema.', ip=f'192.168.10.{random.randint(2,20)}')
        return session_user

    def logout(self) -> None:
        if not self.current_user:
            return
        self.audit.log(user=self.current_user, action='CERRAR_SESION', details=f'Usuario {self.current_user["username"]} cerró sesión.', ip='192.168.10.15')
        self.current_user = None

    def has_role(self, allowed_roles: List[str]) -> bool:
        user = self.get_current_user()
        return bool(user and user['role'] in allowed_roles)

    def debug_switch_role(self, role: str) -> Optional[Dict[str, Any]]:
        user_map = {
            'ADMINISTRADOR': {'id': 1, 'username': 'admin', 'fullname': 'Dr. Ramiro Toro (Admin)', 'role': 'ADMINISTRADOR'},
            'PERSONAL_NOTARIAL': {'id': 2, 'username': 'personal', 'fullname': 'Ing. Sofía Jumbo', 'role': 'PERSONAL_NOTARIAL'},
            'NOTARIO': {'id': 3, 'username': 'notario', 'fullname': 'Dr. Patricio Ordóñez (Notario)', 'role': 'NOTARIO'}
        }
        selected = user_map.get(role)
        if not selected:
            return None
        session_user = {**selected, 'token': f'debug-role-switch-{role}'}
        self.current_user = session_user
        self.audit.log(user=session_user, action='CAMBIO_ROL_DEBUG', details=f'Cambiado de rol a {role} para pruebas rápidas.', ip='127.0.0.1')
        return session_user


class ClientService:
    def __init__(self, db: LocalDatabase, audit: AuditService):
        self.db = db
        self.audit = audit

    @staticmethod
    def validate_cedula_ecuatoriana(cedula: str) -> bool:
        cedula = cedula.strip()
        if len(cedula) != 10 or not cedula.isdigit():
            return False

        provincia = int(cedula[:2])
        if (provincia < 1 or provincia > 24) and provincia != 30:
            return False

        tercer_digito = int(cedula[2])
        if tercer_digito >= 6:
            return False

        coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        suma = 0
        for i in range(9):
            valor = int(cedula[i]) * coeficientes[i]
            if valor >= 10:
                valor -= 9
            suma += valor

        verificador = int(cedula[9])
        decena_superior = ((suma + 9) // 10) * 10
        digito_calculado = decena_superior - suma
        if digito_calculado == 10:
            digito_calculado = 0
        return digito_calculado == verificador

    def save_client(self, user: Dict[str, Any], client_data: Dict[str, Any]) -> Dict[str, Any]:
        cedula = client_data.get('cedula', '').strip()
        if not cedula or not client_data.get('names') or not client_data.get('surnames'):
            raise ValueError('Cédula, Nombres y Apellidos son obligatorios.')
        if not self.validate_cedula_ecuatoriana(cedula):
            raise ValueError('Cédula de identidad ecuatoriana inválida.')

        existing = self.db.find_one('clients', {'cedula': cedula})
        if existing and existing.get('id') != client_data.get('id'):
            raise ValueError('Ya existe un cliente con esta cédula de identidad.')

        if client_data.get('id'):
            saved = self.db.update('clients', client_data['id'], client_data)
            self.audit.log(user=user, action='EDICION_CLIENTE', details=f'Editó datos del cliente {client_data["names"]} {client_data["surnames"]} (C.I. {cedula})')
            return saved

        new_client = self.db.insert('clients', client_data)
        self.audit.log(user=user, action='CREACION_CLIENTE', details=f'Creó cliente nuevo {client_data["names"]} {client_data["surnames"]} (C.I. {cedula})')
        return new_client

    def delete_client(self, user: Dict[str, Any], client_id: Any) -> bool:
        proc_list = self.db.find_many('procedures', {'clientId': client_id})
        if proc_list:
            raise ValueError('No se puede eliminar el cliente porque tiene trámites activos registrados.')
        client = self.db.find_by_id('clients', client_id)
        if not client:
            return False
        success = self.db.delete('clients', client_id)
        if success:
            self.audit.log(user=user, action='ELIMINACION_CLIENTE', details=f'Eliminó cliente {client["names"]} {client["surnames"]} (C.I. {client["cedula"]})')
        return success

    def get_client_details(self, client_id: Any) -> Optional[Dict[str, Any]]:
        return self.db.find_by_id('clients', client_id)


class ProcedureService:
    def __init__(self, db: LocalDatabase, audit: AuditService):
        self.db = db
        self.audit = audit

    def generate_code(self) -> str:
        procedures = self.db.get_collection('procedures')
        year = datetime.utcnow().year
        prefix = f'TRA-{year}-'
        max_num = 0
        for p in procedures:
            if p.get('code', '').startswith(prefix):
                try:
                    num = int(p['code'][len(prefix):])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        return f'{prefix}{str(max_num + 1).zfill(4)}'

    def save_procedure(self, user: Dict[str, Any], procedure_data: Dict[str, Any]) -> Dict[str, Any]:
        if not procedure_data.get('clientId') or not procedure_data.get('typeId') or not procedure_data.get('date'):
            raise ValueError('Por favor completa los campos obligatorios del trámite.')

        if procedure_data.get('id'):
            existing = self.db.find_by_id('procedures', procedure_data['id'])
            if not existing:
                raise ValueError('Trámite no encontrado.')
            updated = self.db.update('procedures', procedure_data['id'], procedure_data)
            self.audit.log(user=user, action='EDICION_TRAMITE', details=f'Editó trámite {existing["code"]}. Nuevo Estado: {procedure_data.get("status")}.')
            return updated

        code = self.generate_code()
        new_data = {**procedure_data, 'code': code, 'userId': user['id']}
        created = self.db.insert('procedures', new_data)
        self.audit.log(user=user, action='CREACION_TRAMITE', details=f'Creó nuevo trámite {code} para el tipo de documento ID {procedure_data["typeId"]}.')
        return created

    def delete_procedure(self, user: Dict[str, Any], procedure_id: Any) -> bool:
        procedure = self.db.find_by_id('procedures', procedure_id)
        if not procedure:
            return False
        docs = self.db.find_many('documents', {'procedureId': procedure_id})
        for doc in docs:
            self.db.delete('documents', doc['id'])
        self.db.delete('procedures', procedure_id)
        self.audit.log(user=user, action='ELIMINACION_TRAMITE', details=f'Eliminó trámite {procedure["code"]}.')
        return True


class TemplateService:
    def __init__(self, db: LocalDatabase, audit: AuditService):
        self.db = db
        self.audit = audit

    def save_template(self, user: Dict[str, Any], template_data: Dict[str, Any]) -> Dict[str, Any]:
        if not template_data.get('name') or not template_data.get('typeId') or not template_data.get('content'):
            raise ValueError('Nombre, Tipo de Trámite y Contenido son campos obligatorios.')

        variables = [v.strip().upper().replace('{', '').replace('}', '') for v in template_data.get('variables', []) if v.strip()]
        active = bool(template_data.get('active', True))
        prepared = {
            'name': template_data['name'].strip(),
            'description': template_data.get('description', '').strip(),
            'typeId': template_data['typeId'],
            'version': template_data.get('version', '1.0').strip(),
            'active': active,
            'content': template_data['content'],
            'variables': variables,
            'updatedAt': now_iso(),
            'updatedBy': user['fullname']
        }

        if template_data.get('id'):
            updated = self.db.update('templates', template_data['id'], prepared)
            self.audit.log(user=user, action='EDICION_PLANTILLA', details=f'Editó la plantilla "{prepared["name"]}" (v{prepared["version"]}).')
            return updated

        created = self.db.insert('templates', prepared)
        self.audit.log(user=user, action='CREACION_PLANTILLA', details=f'Creó una nueva plantilla "{prepared["name"]}" (v{prepared["version"]}).')
        return created

    def toggle_status(self, user: Dict[str, Any], template_id: Any) -> Dict[str, Any]:
        template = self.db.find_by_id('templates', template_id)
        if not template:
            raise ValueError('Plantilla no encontrada.')
        new_active = not template.get('active', True)
        updated = self.db.update('templates', template_id, {'active': new_active})
        self.audit.log(user=user, action='ESTADO_PLANTILLA', details=f'Cambió el estado de la plantilla "{template["name"]}" a {"ACTIVA" if new_active else "INACTIVA"}.')
        return updated


class DocumentService:
    def __init__(self, db: LocalDatabase, audit: AuditService):
        self.db = db
        self.audit = audit

    def compile_template(self, template_content: str, variables: Dict[str, str]) -> str:
        compiled = template_content
        for key, value in variables.items():
            compiled = re.sub(rf'\{{\{{{re.escape(key)}\}}\}}', value or '', compiled)
        return compiled

    def generate_draft(self, user: Dict[str, Any], procedure_id: Any) -> Dict[str, Any]:
        procedure = self.db.find_by_id('procedures', procedure_id)
        if not procedure:
            raise ValueError('Trámite no encontrado.')
        template = self.db.find_one('templates', {'typeId': procedure['typeId'], 'active': True})
        conversation = self.db.find_one('ai_conversations', {'procedureId': procedure_id})
        client = self.db.find_by_id('clients', procedure['clientId'])

        if not template or not conversation:
            raise ValueError('Error al generar borrador: Datos incompletos.')

        missing = [v for v in template['variables'] if not conversation['variablesCollected'].get(v) or conversation['variablesCollected'][v] == 'N/D']
        if missing:
            raise ValueError(f'Falta completar variables obligatorias: {", ".join(missing)}')

        compiled_content = self.compile_template(template['content'], conversation['variablesCollected'])
        title = f"Borrador de {template['name']} - {client['surnames']} {client['names']}"

        existing_doc = self.db.find_one('documents', {'procedureId': procedure_id})
        if existing_doc:
            self.db.insert('document_versions', {
                'documentId': existing_doc['id'],
                'content': existing_doc['content'],
                'updatedBy': user['fullname'],
                'updatedAt': now_iso(),
                'reason': 'Actualización por nueva recopilación de datos IA.'
            })
            updated_doc = self.db.update(existing_doc['id'] if False else 'documents', existing_doc['id'], {
                'title': title,
                'content': compiled_content,
                'status': 'borrador'
            })
            doc = updated_doc
        else:
            doc = self.db.insert('documents', {
                'procedureId': procedure_id,
                'templateId': template['id'],
                'title': title,
                'content': compiled_content,
                'status': 'borrador',
                'corrections': ''
            })

        self.db.update('procedures', procedure_id, {'status': 'Borrador generado'})
        self.audit.log(user=user, action='GENERACION_BORRADOR', details=f'Generó borrador de documento para trámite {procedure["code"]} ({title})')
        self.db.insert('notifications', {
            'userId': procedure['userId'],
            'message': f'Se ha generado el borrador para el trámite {procedure["code"]}.',
            'read': False,
            'createdAt': now_iso()
        })
        return doc

    def save_editor_changes(self, user: Dict[str, Any], document_id: Any, new_content: str) -> Dict[str, Any]:
        doc = self.db.find_by_id('documents', document_id)
        if not doc:
            raise ValueError('Documento no encontrado.')

        self.db.insert('document_versions', {
            'documentId': doc['id'],
            'content': doc['content'],
            'updatedBy': user['fullname'],
            'updatedAt': now_iso(),
            'reason': 'Edición manual del usuario.'
        })
        updated = self.db.update('documents', document_id, {'content': new_content})
        self.audit.log(user=user, action='EDICION_MANUAL_DOCUMENTO', details=f'Modificó manualmente el contenido del borrador "{doc["title"]}".')
        return updated

    def send_to_review(self, user: Dict[str, Any], document_id: Any) -> Dict[str, Any]:
        doc = self.db.find_by_id('documents', document_id)
        if not doc:
            raise ValueError('Documento no encontrado.')
        procedure = self.db.find_by_id('procedures', doc['procedureId'])
        if not procedure:
            raise ValueError('Trámite no encontrado.')

        self.db.update('documents', document_id, {'status': 'revision'})
        self.db.update('procedures', procedure['id'], {'status': 'En revisión'})

        for u in self.db.get_collection('users'):
            if u['role'] in ('NOTARIO', 'ADMINISTRADOR'):
                self.db.insert('notifications', {
                    'userId': u['id'],
                    'message': f'Nuevo documento del trámite {procedure["code"]} enviado a revisión por {user["fullname"]}.',
                    'read': False,
                    'createdAt': now_iso()
                })
        self.audit.log(user=user, action='ENVIO_A_REVISION', details=f'Envió documento del trámite {procedure["code"]} a revisión notarial.')
        return self.db.find_by_id('documents', document_id)


class AIService:
    def __init__(self, db: LocalDatabase, client_service: ClientService, audit: AuditService):
        self.db = db
        self.client_service = client_service
        self.audit = audit

    def init_conversation(self, procedure_id: Any) -> Dict[str, Any]:
        procedure = self.db.find_by_id('procedures', procedure_id)
        if not procedure:
            raise ValueError('Trámite no encontrado.')
        client = self.db.find_by_id('clients', procedure['clientId'])
        template = self.db.find_one('templates', {'typeId': procedure['typeId'], 'active': True})
        if not template:
            raise ValueError('No hay una plantilla activa configurada para este tipo de trámite.')

        conversation = self.db.find_one('ai_conversations', {'procedureId': procedure_id})
        if conversation:
            return conversation

        variables_collected = {v: 'N/D' for v in template['variables']}
        if client:
            if 'COMPARECIENTE' in template['variables']:
                variables_collected['COMPARECIENTE'] = f"{client['names']} {client['surnames']}"
            if 'CEDULA_COMPARECIENTE' in template['variables']:
                variables_collected['CEDULA_COMPARECIENTE'] = client['cedula']
            if 'ESTADO_CIVIL' in template['variables']:
                variables_collected['ESTADO_CIVIL'] = client['maritalStatus']
            if 'CIUDAD' in template['variables']:
                variables_collected['CIUDAD'] = 'Zumba'
            if 'FECHA' in template['variables']:
                variables_collected['FECHA'] = datetime.utcnow().strftime('%d de %B del %Y')
            if template['typeId'] == 4 and 'VENDEDOR' in template['variables']:
                variables_collected['VENDEDOR'] = f"{client['names']} {client['surnames']}"
            if template['typeId'] == 4 and 'CEDULA_VENDEDOR' in template['variables']:
                variables_collected['CEDULA_VENDEDOR'] = client['cedula']

        conversation = self.db.insert('ai_conversations', {
            'procedureId': procedure_id,
            'status': 'conversando',
            'currentStep': 0,
            'variablesCollected': variables_collected
        })

        welcome = (
            f"Hola, soy tu Asistente Notarial IA.\n"
            f"Veo que deseas preparar un borrador para el trámite de {template['name']} a nombre del compareciente {client['names']} {client['surnames']}.\n"
            "He extraído la información inicial del cliente. Por favor, ayúdame a completar los datos requeridos."
        )
        self.db.insert('ai_messages', {
            'conversationId': conversation['id'],
            'role': 'assistant',
            'content': welcome,
            'createdAt': now_iso()
        })
        return conversation

    def simulate_local_ai(self, user_input: str, current_variables: Dict[str, str], variables_schema: List[str], template_name: str) -> Dict[str, Any]:
        text = user_input.strip()
        next_variables = {**current_variables}
        missing = [v for v in variables_schema if not next_variables.get(v) or next_variables.get(v) == 'N/D']
        message = ''

        if missing:
            current_target = missing[0]
            if current_target in ('COMPARECIENTE', 'VENDEDOR', 'COMPRADOR', 'APODERADO', 'ACOMPANANTE'):
                if len(text) > 5 and 'quiero' not in text.lower() and 'necesito' not in text.lower():
                    next_variables[current_target] = text
            elif 'CEDULA' in current_target:
                match = re.search(r'\b\d{10}\b', text)
                if match:
                    ced = match.group(0)
                    if self.client_service.validate_cedula_ecuatoriana(ced):
                        next_variables[current_target] = ced
                    else:
                        message = f'⚠️ El número de cédula ingresado ({ced}) no es válido. Por favor inténtalo de nuevo.'
            elif current_target == 'PLACA':
                match = re.search(r'\b[A-Z]{3}-?\d{3,4}\b', text.upper())
                if match:
                    next_variables[current_target] = match.group(0)
                elif len(text) > 4:
                    next_variables[current_target] = text.upper()
            elif current_target == 'PRECIO':
                match = re.search(r'\b\d+[\d,.]*\b', text)
                if match:
                    next_variables[current_target] = match.group(0)
            else:
                if len(text) > 2:
                    next_variables[current_target] = text

        missing = [v for v in variables_schema if not next_variables.get(v) or next_variables.get(v) == 'N/D']
        if not message:
            if not missing:
                message = f'¡Excelente! He recopilado todos los datos obligatorios para la plantilla {template_name}. Ahora puedes generar el borrador oficial del trámite.'
            else:
                prompts = {
                    'COMPARECIENTE': 'Por favor, proporcione el nombre del compareciente (solicitante).',
                    'VENDEDOR': 'Por favor, ingrese el nombre completo del Vendedor del vehículo.',
                    'COMPRADOR': 'Por favor, ingrese el nombre completo del Comprador del vehículo.',
                    'APODERADO': 'Por favor, indique el nombre de la persona que recibirá el poder (Apoderado).',
                    'ACOMPANANTE': 'Por favor, indique el nombre del acompañante del menor en el viaje.',
                    'CEDULA_COMPARECIENTE': 'Por favor, proporcione el número de cédula (10 dígitos) del compareciente.',
                    'CEDULA_VENDEDOR': 'Por favor, proporcione la cédula de ciudadanía (10 dígitos) del Vendedor.',
                    'CEDULA_COMPRADOR': 'Por favor, proporcione la cédula de ciudadanía (10 dígitos) del Comprador.',
                    'CEDULA_APODERADO': 'Por favor, proporcione el número de cédula (10 dígitos) del Apoderado.',
                    'NOMBRE_MENOR': 'Por favor, ingrese el nombre completo del menor de edad.',
                    'DESTINO': '¿Cuál es el destino del viaje del menor?',
                    'FECHA_VIAJE': '¿Cuál es la fecha estimada del viaje?',
                    'MARCA_VEHICULO': 'Por favor, proporcione la marca y modelo del vehículo.',
                    'PLACA': 'Ingrese el número de placa del vehículo.',
                    'PRECIO': '¿Cuál es el precio pactado para la venta del vehículo?',
                    'DECLARACION': 'Por favor, describa detalladamente los hechos que declarará el compareciente bajo juramento.',
                    'OBJETO_PODER': 'Por favor, describa el objeto específico o gestiones para las que se otorga el poder.',
                    'CIUDAD': '¿En qué ciudad se realiza la diligencia?',
                    'FECHA': '¿Qué fecha del trámite colocamos?'
                }
                message = prompts.get(missing[0], f'Por favor, proporcione el dato para la variable {missing[0]}.')

        return {
            'message': message,
            'variables': next_variables,
            'finished': len(missing) == 0
        }


if __name__ == '__main__':
    db = LocalDatabase()
    audit = AuditService(db)
    auth = AuthService(db, audit)
    clients = ClientService(db, audit)
    procedures = ProcedureService(db, audit)
    templates = TemplateService(db, audit)
    documents = DocumentService(db, audit)
    ai = AIService(db, clients, audit)

    admin = auth.login('admin', 'password')
    print('Usuario autenticado:', admin)

    new_client = clients.save_client(admin, {
        'cedula': '1900456128',
        'names': 'Luis Humberto',
        'surnames': 'Cabrera Masache',
        'dob': '1982-06-25',
        'maritalStatus': 'SOLTERO',
        'nationality': 'Ecuatoriana',
        'address': 'Parroquia La Chonta',
        'phone': '0993456789',
        'email': 'luis.cabrera@example.com',
        'notes': 'Ninguna.'
    })
    print('Cliente creado:', new_client)

    new_proc = procedures.save_procedure(admin, {
        'clientId': new_client['id'],
        'typeId': 1,
        'date': '2026-08-06',
        'status': 'Pendiente'
    })
    print('Trámite creado:', new_proc)

    conv = ai.init_conversation(new_proc['id'])
    print('Conversación IA iniciada:', conv)

    response = ai.simulate_local_ai('Mi nombre completo es Luis Humberto Cabrera Masache', conv['variablesCollected'], list(conv['variablesCollected'].keys()), 'Plantilla de Poder Especial')
    print('Respuesta de IA simulada:', response)
