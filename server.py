import os
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable

import client

HTTP_CODES = {
    200: "OK",
    304: "Not Modified",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
}


@dataclass
class Route:
    method: str
    endpoint: str
    handler: Callable[..., None]


@dataclass
class Cached_File:
    content: str
    last_modified: str


class Server:
    def __init__(self):
        self.routes = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def handle_connection(self, connection):
        with connection:
            request = self.read_request(connection)

            request_headers_list, request_headers_dict = self.__parse_request(request)
            http_method, endpoint = self.__parse_http_method(request_headers_list[0])
            print("Headers: \n%s\n" % request_headers_dict)
            if not http_method and not endpoint:
                connection.close()
                return
            print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

            # Check for matching endpoints
            matchedEndpoints = list(
                filter(
                    lambda x: x.endpoint == endpoint,
                    self.routes,
                )
            )
            if len(matchedEndpoints) == 0:
                response = self.generate_response(404)
                connection.send(response)
                return

            # Check for matching routes
            matchedRoutes = list(
                filter(
                    lambda x: x.endpoint == endpoint and x.method == http_method,
                    matchedEndpoints,
                )
            )
            if len(matchedRoutes) == 0:
                response = self.generate_response(400)
                connection.send(response)
            else:
                matchedRoute = matchedRoutes[0]
                matchedRoute.handler(connection, request_headers_dict)

    def listen(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)
        while True:
            connection, _ = self.socket.accept()
            thread = threading.Thread(target=self.handle_connection, args=(connection,))
            thread.start()

    def read_request(self, connection):
        # Request
        chunks = []
        chunk = connection.recv(1024).decode()
        chunks.append(chunk)
        while "\r\n" not in chunk:
            chunk = connection.recv(1024).decode()
            chunks.append(chunk)
        request = "".join(chunks)
        print("Client send:\n%s" % request)
        return request

    def add_route(self, method, endpoint: str, callback):
        if endpoint[-1] == "/":
            endpoint = endpoint[:-1]
        self.routes.append(Route(method, endpoint, callback))

    def open_file(self, filepath):
        last_m = os.path.getmtime(filepath)
        last_modified = time.ctime(last_m)

        file = open(filepath, "r")
        readfile = file.read()
        file.close()

        print("last modifieed %f %s" % (last_m, last_modified))

        return readfile, last_modified

    def check_modified_header(self, cache_last_modified, filepath):
        last_m = os.path.getmtime(filepath)
        last_modified = time.ctime(last_m)
        # Compare datetimes
        return time.strptime(last_modified) > time.strptime(cache_last_modified)

    def generate_response(
        self, code, content="", additional_headers={"Content-Type": "text/html"}
    ):
        if not HTTP_CODES[code]:
            code = 500
            content = ""
            additional_headers = {"Content-Type": "text/html"}
        response = "HTTP/1.1 %d %s\n" % (code, HTTP_CODES[code])
        for key in additional_headers:
            response += "%s: %s\r\n" % (key, additional_headers[key])
        if not content:
            response += "\r\n%s" % (HTTP_CODES[code])
        else:
            response += "\r\n%s" % (content)
        return response.encode()

    # Params: request string
    # Returns: request_headers list
    # Splits headers based on \r\n
    def __parse_request(self, request):
        request_headers = request.split("\r\n")
        if len(request_headers) < 1:
            return [], {}
        return request_headers, self.__parse_headers(request_headers)

    # Params: headers list[string]
    # Returns: parsed_headers dict
    # Splits header lines
    def __parse_headers(self, headers):
        parsed_headers = {}
        for header in headers:
            parsed_header = header.split(": ")
            if len(parsed_header) == 2:
                parsed_headers[parsed_header[0]] = parsed_header[1]
        return parsed_headers

    # Params: http_req string
    # Returns: http_method string, endpoint string
    # Parses request line to find method and endpoint
    def __parse_http_method(self, http_req):
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


class Proxy_Server(Server):
    def __init__(self):
        self.files = {}
        self.routes = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.origin_server = Server()
        self.origin_host = "localhost"
        self.origin_port = 8000

    def start_origin_server(self, host, port, num_connections):
        self.origin_port = port
        self.origin_host = host
        self.origin_server.listen(host, port, num_connections)

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


def main_2():
    PROXY_PORT = 3000
    PROXY_HOST = "localhost"
    proxy_server = Proxy_Server()
    # Start proxy
    proxy_server.listen(PROXY_HOST, PROXY_PORT, 5)

    ORIGIN_PORT = 8000
    ORIGIN_HOST = "localhost"
    # Start origin
    proxy_server.start_origin_server(ORIGIN_HOST, ORIGIN_PORT, 5)


def main():
    PORT = 8000
    HOST = "localhost"
    server = Server()

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))

    def index(con, headers):
        file, last_modified = server.open_file("test.html")
        # Compare when file was last modified to the if-modified-since header
        if "If-Modified-Since" in headers and time.strptime(
            headers["If-Modified-Since"]
        ) >= time.strptime(last_modified):
            con.sendall("HTTP/1.1 304 Not Modified\n\r\n\r".encode())
        else:
            # Set the Last-Modified response header to get the If-Modified-Since request header back
            resp_header = (
                "HTTP/1.1 200 OK\nLast-Modified: %s \n\r\n\rHome Page" % last_modified
            )
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

Proxy Server (need to change):
Basically will just relay the request from the client
The server will check the modified-since tag, and return a 304 code or a 200 with the appropriate file
The proxy will cache the file if one has been sent
Proxy will send back the response to the client
"""
