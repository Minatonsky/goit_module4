import json
import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime
import socketserver
import threading


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        record_data(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def record_data(new_data):
    try:
        with open('storage/data.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}

    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    data[timestamp] = new_data

    with open('storage/data.json', 'w') as file:
        json.dump(data, file, indent=2)


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


class SocketHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].decode('utf-8')
        new_data = json.loads(data)
        record_data(new_data)


def run_socket_server(server_class=socketserver.UDPServer, handler_class=SocketHandler):
    server_address = ('', 5000)
    socket_server = server_class(server_address, handler_class)
    try:
        socket_server.serve_forever()
    except KeyboardInterrupt:
        socket_server.server_close()


if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    socket_thread = threading.Thread(target=run_socket_server)
    socket_thread.start()

    http_thread.join()
    socket_thread.join()
