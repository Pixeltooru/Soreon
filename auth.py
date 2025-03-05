import os
import json
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal

class AuthSignals(QObject):
    authenticated = pyqtSignal()

class AuthManager:
    def __init__(self, config):
        self.config = config
        self.auth_data = {}
        self.signals = AuthSignals()
        self.server = None
        self.port = 8933
        self._load_auth_data()

    def _load_auth_data(self):
        auth_file = os.path.expanduser(self.config['Auth']['auth_file'])
        if os.path.exists(auth_file):
            with open(auth_file, 'r', encoding='utf-8') as f:
                self.auth_data = json.load(f)

    def _save_auth_data(self):
        auth_file = os.path.expanduser(self.config['Auth']['auth_file'])
        with open(auth_file, 'w', encoding='utf-8') as f:
            json.dump(self.auth_data, f, ensure_ascii=False)

    def is_authenticated(self):
        return bool(self.auth_data.get('username'))

    def get_username(self):
        return self.auth_data.get('username', 'Гость')

    def get_uuid(self):
        return self.auth_data.get('uuid', str(uuid.uuid4()))

    def get_access_token(self):
        return self.auth_data.get('accessToken', 'offline-token')

    def logout(self):
        self.auth_data = {}
        self._save_auth_data()

    def _start_server(self):
        class AuthHandler(BaseHTTPRequestHandler):
            def do_GET(_):
                _.send_response(200)
                _.send_header('Content-type', 'text/html; charset=utf-8')
                _.end_headers()
                _.wfile.write(self._generate_html().encode('utf-8'))

            def do_POST(_):
                content_length = int(_.headers['Content-Length'])
                post_data = _.rfile.read(content_length).decode('utf-8')
                self._handle_login(post_data)
                
                _.send_response(200)
                _.send_header('Content-type', 'text/html; charset=utf-8')
                _.end_headers()
                _.wfile.write(b'<script>window.close();</script>')

        self.server = HTTPServer(('localhost', self.port), AuthHandler)
        self.server.serve_forever()

    def _generate_html(self):
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Авторизация</title>
    <style>
        body { 
            background: #2a2a2a; 
            color: white;
            font-family: Arial;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .auth-box {
            background: #363636;
            padding: 2rem;
            border-radius: 10px;
            width: 300px;
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #444;
            background: #505050;
            color: white;
        }
        button { 
            background: #6E48AA; 
            border: none; 
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="auth-box">
        <h2>Авторизация</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Никнейм" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
    </div>
</body>
</html>'''

    def _handle_login(self, post_data):
        from urllib.parse import parse_qs
        params = parse_qs(post_data)
        self.auth_data = {
            'username': params['username'][0],
            'uuid': str(uuid.uuid4()),
            'accessToken': f"fake-token-{params['username'][0]}"
        }
        self._save_auth_data()
        self.signals.authenticated.emit()

    def authenticate(self):
        Thread(target=self._start_server, daemon=True).start()
        webbrowser.open(f'http://localhost:{self.port}')