import mimetypes
import pathlib
import socket
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from multiprocessing import Process
from datetime import datetime
import pymongo

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/message':
            data = self.rfile.read(int(self.headers['Content-Length']))
            print(data)  # Debugging line
            data_parse = urllib.parse.unquote_plus(data.decode())
            print(data_parse)  # Debugging line
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            print(data_dict)  # Debugging line
            self.save_data_to_json(data_dict)
            self.send_to_socket_server(data_dict)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_html_file('error.html', 404)

    def save_data_to_json(self, data_dict):
        data_path = pathlib.Path('storage') / 'data.json'
        # Load existing data
        if data_path.exists():
            with open(data_path, 'r') as f:
                data = json.load(f)
        else:
            data = []
        # Append new data
        data.append(data_dict)
        # Save data back to file
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=4)

    def send_to_socket_server(self, data_dict):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 5000))
            data_dict['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            s.sendall(json.dumps(data_dict).encode())

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

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
        file_path = pathlib.Path('static') / self.path.split('/')[-1]
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    print("HTTP server running on port 3000")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server():
    client = pymongo.MongoClient("mongodb://mongo:27017/")
    db = client["message_db"]
    collection = db["messages"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5000))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    data_dict = json.loads(data.decode())
                    data_dict["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    collection.insert_one(data_dict)

if __name__ == '__main__':
    p1 = Process(target=run_http_server)
    p2 = Process(target=run_socket_server)
    p1.start()
    p2.start()
    p1.join()
    p2.join()