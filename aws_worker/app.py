import json
import os
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from brain.computer_use import run_computer_use


HOST = os.getenv('WORKER_HOST', '0.0.0.0')
PORT = int(os.getenv('WORKER_PORT', '8787'))


def json_response(start_response, status_code: int, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    status_text = {
        200: '200 OK',
        400: '400 Bad Request',
        404: '404 Not Found',
        405: '405 Method Not Allowed',
        500: '500 Internal Server Error',
    }.get(status_code, f'{status_code} OK')
    start_response(status_text, [('Content-Type', 'application/json; charset=utf-8')])
    return [body]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET').upper()

    if path == '/healthz' and method == 'GET':
        return json_response(start_response, 200, {'status': 'healthy', 'display': os.getenv('DISPLAY', ':1')})

    if path == '/computer-use/' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH') or '0')
        except ValueError:
            length = 0
        raw_body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            return json_response(start_response, 400, {'success': False, 'error': 'JSON inválido.'})

        task = str(payload.get('task', '')).strip()
        if not task:
            return json_response(start_response, 400, {'success': False, 'error': 'Campo task é obrigatório.'})

        result = run_computer_use(task)
        status_code = 200 if result.get('success') else 500 if result.get('status') == 'error' else 200
        return json_response(start_response, status_code, result)

    if path == '/' and method == 'GET':
        return json_response(start_response, 200, {'service': 'alaha22-aws-worker', 'status': 'ok', 'routes': ['/healthz', '/computer-use/']})

    if path in {'/computer-use/', '/healthz', '/'}:
        return json_response(start_response, 405, {'success': False, 'error': 'Método não permitido.'})

    return json_response(start_response, 404, {'success': False, 'error': 'Rota não encontrada.'})


if __name__ == '__main__':
    with make_server(HOST, PORT, application) as server:
        print(f'AWS worker ouvindo em http://{HOST}:{PORT}', flush=True)
        server.serve_forever()
