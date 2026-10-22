import json
import mimetypes
import random
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
import webbrowser


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = ROOT / 'notaria.db'
COLLECTIONS = (
    'users',
    'clients',
    'procedures',
    'document_types',
    'templates',
    'documents',
    'document_versions',
    'notifications',
    'audit_logs',
    'ai_conversations',
    'ai_messages',
)
MAX_REQUEST_BYTES = 25 * 1024 * 1024
STATIC_FILES = {'index.html', 'index.css', 'logo-notaria.jpg', 'tests.html'}


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS records (
            collection TEXT NOT NULL,
            record_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (collection, record_id)
        )
        '''
    )
    return connection


@contextmanager
def database():
    connection = connect_database()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class NotariaHandler(BaseHTTPRequestHandler):
    server_version = 'NotariaLocalServer/1.0'

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ValueError('El tamaño de la solicitud supera el límite permitido.')
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode('utf-8')) if body else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError('El cuerpo de la solicitud debe contener JSON válido.') from error

    def handle_api_error(self, error):
        if isinstance(error, ValueError):
            self.send_json(400, {'error': str(error)})
        elif isinstance(error, sqlite3.IntegrityError):
            self.send_json(409, {'error': 'Ya existe un registro con ese identificador.'})
        else:
            print(f'Error de base de datos: {error}')
            self.send_json(500, {'error': 'No se pudo completar la operación en la base de datos.'})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == '/api/db':
                with database() as connection:
                    snapshot = {name: [] for name in COLLECTIONS}
                    for row in connection.execute(
                        'SELECT collection, data_json FROM records ORDER BY rowid'
                    ):
                        if row['collection'] in snapshot:
                            snapshot[row['collection']].append(json.loads(row['data_json']))
                self.send_json(200, snapshot)
                return

            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[:2] == ['api', 'collections']:
                collection = self.require_collection(parts[2])
                with database() as connection:
                    rows = connection.execute(
                        'SELECT data_json FROM records WHERE collection = ? ORDER BY rowid',
                        (collection,),
                    ).fetchall()
                self.send_json(200, [json.loads(row['data_json']) for row in rows])
                return

            self.serve_static(path)
        except (ValueError, sqlite3.Error) as error:
            self.handle_api_error(error)

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        try:
            data = self.read_json()
            if path == '/api/db/import':
                if not isinstance(data, dict):
                    raise ValueError('Los datos para importar deben ser un objeto.')
                with database() as connection:
                    count = connection.execute('SELECT COUNT(*) FROM records').fetchone()[0]
                    if count:
                        self.send_json(409, {'error': 'La base de datos ya contiene información.'})
                        return
                    for collection in COLLECTIONS:
                        records = data.get(collection, [])
                        if not isinstance(records, list):
                            raise ValueError(f'La colección {collection} debe ser una lista.')
                        for record in records:
                            self.insert_record(connection, collection, record)
                self.send_json(201, {'ok': True})
                return

            if path == '/api/reset':
                with database() as connection:
                    connection.execute('DELETE FROM records')
                self.send_json(200, {'ok': True})
                return

            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[:2] == ['api', 'collections']:
                collection = self.require_collection(parts[2])
                with database() as connection:
                    record = self.insert_record(connection, collection, data)
                self.send_json(201, record)
                return

            self.send_json(404, {'error': 'Ruta no encontrada.'})
        except (ValueError, sqlite3.Error) as error:
            self.handle_api_error(error)

    def do_PUT(self):
        path = unquote(urlparse(self.path).path)
        try:
            data = self.read_json()
            parts = path.strip('/').split('/')
            if len(parts) != 4 or parts[:2] != ['api', 'collections']:
                self.send_json(404, {'error': 'Ruta no encontrada.'})
                return
            collection = self.require_collection(parts[2])
            record_id = parts[3]
            if not isinstance(data, dict):
                raise ValueError('Los datos del registro deben ser un objeto.')

            with database() as connection:
                row = connection.execute(
                    'SELECT data_json FROM records WHERE collection = ? AND record_id = ?',
                    (collection, record_id),
                ).fetchone()
                if row is None:
                    self.send_json(200, None)
                    return
                record = json.loads(row['data_json'])
                record.update(data)
                record['updatedAt'] = now_iso()
                connection.execute(
                    'UPDATE records SET data_json = ?, updated_at = ? '
                    'WHERE collection = ? AND record_id = ?',
                    (json.dumps(record, ensure_ascii=False), record['updatedAt'], collection, record_id),
                )
            self.send_json(200, record)
        except (ValueError, sqlite3.Error) as error:
            self.handle_api_error(error)

    def do_DELETE(self):
        path = unquote(urlparse(self.path).path)
        parts = path.strip('/').split('/')
        try:
            if len(parts) != 4 or parts[:2] != ['api', 'collections']:
                self.send_json(404, {'error': 'Ruta no encontrada.'})
                return
            collection = self.require_collection(parts[2])
            with database() as connection:
                cursor = connection.execute(
                    'DELETE FROM records WHERE collection = ? AND record_id = ?',
                    (collection, parts[3]),
                )
            self.send_json(200, cursor.rowcount > 0)
        except (ValueError, sqlite3.Error) as error:
            self.handle_api_error(error)

    @staticmethod
    def require_collection(name):
        if name not in COLLECTIONS:
            raise ValueError('La colección solicitada no está permitida.')
        return name

    @staticmethod
    def insert_record(connection, collection, data):
        if not isinstance(data, dict):
            raise ValueError('Cada registro debe ser un objeto.')
        record = {
            'id': data.get('id', int(time.time() * 1000) + random.randint(0, 999)),
            'createdAt': data.get('createdAt', now_iso()),
            **data,
        }
        record_id = str(record['id'])
        connection.execute(
            'INSERT INTO records (collection, record_id, data_json, created_at) VALUES (?, ?, ?, ?)',
            (collection, record_id, json.dumps(record, ensure_ascii=False), record['createdAt']),
        )
        return record

    def serve_static(self, url_path):
        relative_path = 'index.html' if url_path in ('', '/') else url_path.lstrip('/')
        file_path = (ROOT / relative_path).resolve()
        is_public_root_file = file_path.parent == ROOT and file_path.name in STATIC_FILES
        is_public_script = ROOT / 'src' / 'js' in file_path.parents and file_path.suffix == '.js'
        if not (is_public_root_file or is_public_script):
            self.send_error(404)
            return
        if not file_path.is_file():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
        if content_type.startswith('text/') or content_type in ('application/javascript', 'application/json'):
            content_type += '; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == '__main__':
    with database():
        pass
    server = ThreadingHTTPServer(('127.0.0.1', 8080), NotariaHandler)
    print(f'Servidor iniciado: http://localhost:8080 (SQLite: {DATABASE_PATH})')
    threading.Timer(1, webbrowser.open, args=('http://localhost:8080/',)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
    finally:
        server.server_close()
