import server
import socket
import os
import time
from dataclasses import dataclass
from threading import *
from typing import Callable

class Proxy_Server(server.Server):
    def __init__(self):
        self.files = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.origin_port = 8000
        self.origin_host = "localhost"

    def listen_proxy(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)
        connection, addr = self.socket.accept()
        while True:
            print("GOT CONNECTION IN PROXY SERVER")
            print("REQUEST FROM PROXY")
            request = self.read_request(connection)

            request_headers_list, request_headers_dict = self.parse_request(request)
            http_method, endpoint = self.parse_http_method(request_headers_list[0])
            print("Headers: \n%s\n" % request_headers_dict)
            if not http_method and not endpoint:
                connection.close()
                continue
            print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

            # Send req to origin
            client_socket = socket.socket()
            client_socket.connect((self.origin_host, self.origin_port))
            client_socket.send(request.encode())
            print("RECEIVING RESPONSE")
            chunks = []
            chunk = client_socket.recv(1024).decode()
            chunks.append(chunk)
            while "\r\n" not in chunk:
                chunk = client_socket.recv(1024).decode()
                chunks.append(chunk)
            response = "".join(chunks)
            print("Origin server sent:\n%s" % response)
            client_socket.close()
            connection.sendall(response.encode())

    def connect_origin(self, request):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.origin_host, self.origin_port))
        client_socket.send(b"Hello, world")
        print("SENDING HEADERS TO ORIGIN SERVER")
        return client_socket
        
    def receive_response(self, client_socket):
        print("RECEIVING RESPONSE")
        chunks = []
        chunk = client_socket.recv(1024).decode()
        chunks.append(chunk)
        while "\r\n" not in chunk:
            chunk = client_socket.recv(1024).decode()
            chunks.append(chunk)
        response = "".join(chunks)
        print("Origin server sent:\n%s" % response.decode())
        client_socket.close()
        return response

    def find_file(self, filepath):
        readfile, last_modified
        if not self.files[filepath]:
            # Request file from origin server
            readfile, last_modified = self.origin_server.open_file(filepath)
            # Cache the file
        else:
            # Here we would make a request to our actual origin server
            self.socket.connect((self.origin_host, self.origin_port))
            # Check if last_modified corresponds to actual last time it was modified
            self.socket.send(self.files[filepath].last_modified)
            return
        
def main():
    PROXY_PORT = 3000
    PROXY_HOST = "localhost"
    proxy_server = Proxy_Server()

    print("Initializing proxy with host %s and port %s \n" % (PROXY_HOST, PROXY_PORT))

    proxy_server.listen_proxy(PROXY_HOST, PROXY_PORT, 5)

if __name__ == "__main__":
    main()