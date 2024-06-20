import socket
from dataclasses import dataclass
from threading import *
from typing import Callable

import client


@dataclass
class Route:
    method: str
    endpoint: str
    handler: Callable[..., None]


class Server:
    def __init__(self, socket):
        self.routes = []
        # routes = list of Route
        self.socket = socket

    def initialize_socket(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)

    def accept_connection(self):
        while True:
            connection, addr = self.socket.accept()
            with connection:
                # Request
                chunks = []
                chunk = connection.recv(1024).decode()
                chunks.append(chunk)
                while "\r\n" not in chunk:
                    chunk = connection.recv(1024).decode()
                    chunks.append(chunk)
                request = "".join(chunks)

                print("Client send:\n%s" % request)

                # Read request
                request_headers = parse_request(request)
                http_method, endpoint = parse_http_method(request_headers[0])
                parsed_headers = parse_headers(request_headers)
                print("Dictionary with headers: \n%s\n" % parsed_headers)
                if not http_method and not endpoint:
                    connection.close()
                    continue
                print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

                matchedRoutes = list(
                    filter(
                        lambda x: x.method == http_method and x.endpoint == endpoint,
                        self.routes,
                    )
                )

                if len(matchedRoutes) == 0:
                    connection.send()  # 404 not done yet

                matchedRoute = matchedRoutes[0]
                matchedRoute.handler(connection, request_headers)

    def add_route(self, method, endpoint: str, callback):
        if endpoint[-1] == "/":
            endpoint = endpoint[:-1]
        self.routes.append(Route(method, endpoint, callback))


def example_handler(file):
    return file.encode()


# Params: request string
# Returns: request_headers list
# Splits headers based on \r\n
def parse_request(request):
    request_headers = request.split("\r\n")
    if len(request_headers) < 1:
        return []
    return request_headers


# Params: headers list[string]
# Returns: parsed_headers dict
# Splits header lines
def parse_headers(headers):
    parsed_headers = {}
    for header in headers:
        parsed_header = header.split(": ")
        if len(parsed_header) == 2:
            parsed_headers[parsed_header[0]] = parsed_header[1]
    return parsed_headers


# Params: http_req string
# Returns: http_method string, endpoint string
# Parses request line to find method and endpoint
def parse_http_method(http_req):
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


def main():
    PORT = 8000
    HOST = "localhost"
    server = Server(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))
    server.initialize_socket(HOST, PORT, 5)

    testfile = open("test.html", "r")
    testhtml = testfile.read()
    testfile.close()

    def index(con, headers):
        # Response
        # Set the Last-Modified response header to get the If-Modified-Since request header back
        con.send(
            "HTTP/1.0 200 OK\nContent-Type: text/html\nLast-Modified: Tue, 18 Jun 2024 00:26:59 GMT\n".encode()
        )
        con.send(testhtml.encode())

    server.add_route("GET", "/", index)
    server.add_route("GET", "/unprotected", index)

    server.accept_connection()


if __name__ == "__main__":
    main()

"""
1. Check Route
If Route Exists:
    2. Call "handler"
    3. Check cache
"""

