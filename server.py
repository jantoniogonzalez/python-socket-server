import socket
import os
import time
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
    def __init__(self):
        self.routes = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def listen(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)
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
                request_headers_list, request_headers_dict = parse_request(request)
                http_method, endpoint = parse_http_method(request_headers_list[0])
                print("Headers: \n%s\n" % request_headers_dict)
                if not http_method and not endpoint:
                    connection.close()
                    continue
                print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

                # Check for matching endpoints
                matchedEndpoints = list(
                    filter(
                        lambda x: x.endpoint == endpoint,
                        self.routes,
                    )
                )  
                if len(matchedEndpoints) == 0:
                    connection.send(
                        "HTTP/1.1 404 Not Found\nContent-Type: text/html\n\r\n\rNot Found".encode()
                    )
                    continue

                # Check for matching routes
                matchedRoutes = list(
                    filter(
                        lambda x: x.endpoint == endpoint and x.method == http_method,
                        matchedEndpoints,
                    )
                )
                if len(matchedRoutes) == 0:
                    connection.send(
                        "HTTP/1.1 400 Bad Request\nContent-Type: text/html\n\r\n\rBad Request".encode()
                    )
                else:
                    matchedRoute = matchedRoutes[0]
                    matchedRoute.handler(connection, request_headers_dict)

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
        return [], {}
    return request_headers, parse_headers(request_headers)


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

def open_file(filepath):
    last_m= os.path.getmtime(filepath)
    last_modified = time.ctime(last_m)

    file = open(filepath, "r")
    readfile = file.read()
    file.close()

    print("last modifieed %f %s" % (last_m, last_modified))

    return readfile, last_modified


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
    server = Server()

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))

    def index(con, headers):
        file, last_modified = open_file("test.html")
        # Compare when file was last modified to the if-modified-since header
        if "If-Modified-Since" in headers and time.strptime(headers["If-Modified-Since"]) >= time.strptime(last_modified):
            con.sendall("HTTP/1.1 304 Not Modified\n\r\n\rHome Page".encode())
        else:
            # Set the Last-Modified response header to get the If-Modified-Since request header back
            resp_header = "HTTP/1.1 200 OK\nLast-Modified: %s \n\r\n\rHome Page" % last_modified
            con.sendall(resp_header.encode())

    def index_post(con, headers):
        con.sendall("HTTP/1.1 200 OK\n\r\n\rSucessfully Posted".encode())

    def internal(con, headers):
        con.sendall("HTTP/1.1 403 Forbidden\n\r\n\rForbidden".encode())

    server.add_route("GET", "/", index)
    server.add_route("POST", "/", index_post)
    server.add_route("GET", "/internal", internal)

    server.listen(HOST, PORT, 5)


if __name__ == "__main__":
    main()

"""
1. Check Route
If Route Exists:
    2. Call "handler"
    3. Check cache
"""
