import server
import socket
import os
import time
import string
from dataclasses import dataclass
from threading import *
from typing import Callable

@dataclass
class Cached_File:
    content: str
    last_modified: str

class Proxy_Server():
    def __init__(self):
        self.files = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.origin_port = 8000
        self.origin_host = socket.gethostname()

    def read_request(self, connection):
        # Request
        print("READING REQUEST!!!!")
        chunks = []
        chunk = connection.recv(1024).decode()
        chunks.append(chunk)
        while "\r\n" not in chunk:
            chunk = connection.recv(1024).decode()
            chunks.append(chunk)
        request = "".join(chunks)
        print("Client send:\n%s" % request)
        return request
    
    # Params: request string
    # Returns: request_headers list
    # Splits headers based on \r\n
    def parse_request(self, request):
        request_headers = request.split("\r\n")
        if len(request_headers) < 1:
            return [], {}
        return request_headers, self.parse_headers(request_headers)


    # Params: headers list[string]
    # Returns: parsed_headers dict
    # Splits header lines
    def parse_headers(self, headers):
        parsed_headers = {}
        for header in headers:
            parsed_header = header.split(": ")
            if len(parsed_header) == 2:
                parsed_headers[parsed_header[0]] = parsed_header[1]
        return parsed_headers


    # Params: http_req string
    # Returns: http_method string, endpoint string
    # Parses request line to find method and endpoint
    def parse_http_method(self, http_req):
        if type(http_req) != str:
            return "", ""
        parsed_http_request = http_req.split(" ")
        if len(parsed_http_request) < 2:
            return "", ""
        # Method
        http_method, endpoint = parsed_http_request[0], parsed_http_request[1]
        if endpoint == "/favicon.ico":
            return "", ""
        if endpoint[-1] == "/":
            endpoint = endpoint[:-1]
        return http_method, endpoint

    def listen_proxy(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)
        while True:
            connection, addr = self.socket.accept()
            print("REQUEST TO PROXY")
            request = self.read_request(connection)

            request_headers_list, request_headers_dict = self.parse_request(request)
            http_method, endpoint = self.parse_http_method(request_headers_list[0])
            print("Headers: \n%s\n" % request_headers_dict)
            if not http_method and not endpoint:
                connection.close()
                continue
            print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))
            # Attach if-modified-since header
            request = self.conditional_get(http_method, endpoint, request)

            # Send req to origin
            client_socket = socket.socket()
            client_socket.connect((self.origin_host, self.origin_port))
            client_socket.send(request.encode())
            print("RECEIVING ORIGIN RESPONSE")
            chunks = []
            chunk = client_socket.recv(1024).decode()
            chunks.append(chunk)
            while "\r\n" not in chunk:
                chunk = client_socket.recv(1024).decode()
                chunks.append(chunk)
            response = "".join(chunks)
            # Cache the file from response
            print("Origin server sent:\n%s" % response)
            client_socket.close()
            if self.has_not_modified_header(response) and (http_method, endpoint) in self.files:
                response += self.files[(http_method, endpoint)].content
            else:
                self.cache_file(response, http_method, endpoint)
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

    def conditional_get(self, http_method, endpoint, request):
        if (http_method, endpoint) not in self.files:
            return request
        else:
            request+="\r\nIf-Modified-Since: %s" % self.files[(http_method, endpoint)].last_modified
            return request
        
    def has_not_modified_header(self, response):
        response_body = response.split("\r\n\r\n")       
        return "304" in response_body[0]

    def cache_file(self, response, http_method, endpoint):
        response_body = response.split("\r\n\r\n")
        _, response_headers_dict = self.parse_request(response_body[0])
        if "Last-Modified" not in response_headers_dict:
            return
        # Only cache files that have the last-modified header
        new_file = Cached_File
        new_file.content = response_body[1]
        new_file.last_modified = response_headers_dict["Last-Modified"]
        self.files[(http_method, endpoint)] = new_file # idk if you can actually do this
        
def main():
    PROXY_PORT = 3000
    PROXY_HOST = "localhost"
    proxy_server = Proxy_Server()

    print("Initializing proxy with host %s and port %s \n" % (PROXY_HOST, PROXY_PORT))

    proxy_server.listen_proxy(PROXY_HOST, PROXY_PORT, 5)

if __name__ == "__main__":
    main()