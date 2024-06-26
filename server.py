import socket
import os
import time
from dataclasses import dataclass
from threading import *
from typing import Callable


HTTP_CODES ={
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

class Server:
    def __init__(self):
        self.routes = []
        self.socket = socket.socket()

    def listen(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)
        while True:
            connection, addr = self.socket.accept()
            print("CONNECTED TO PROXY: ")
            print(addr)
            with connection:
                request = self.read_request(connection)
                
                request_headers_list, request_headers_dict = self.parse_request(request)
                http_method, endpoint = self.parse_http_method(request_headers_list[0])
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
                    response = self.generate_response(404)
                    connection.send(response)
                    continue

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
                print("CLOSING CONNECTION")
                connection.close()

    def read_request(self, connection):
        # Request
        print("READING REQUEST!!!!")
        print(connection)
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
        last_m= os.path.getmtime(filepath)
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
    
    def generate_response(self, code, content="", additional_headers={"Content-Type": "text/html"}):
        if not HTTP_CODES[code]:
            code = 500
            content=""
            additional_headers={"Content-Type": "text/html"}
        response = "HTTP/1.1 %d %s\n" % (code, HTTP_CODES[code])
        for key in additional_headers:
            response += "%s: %s\r\n" % (key, additional_headers[key])
        if not content and code != 304:
            response += "\r\n%s" % (HTTP_CODES[code])
        else:
            response += "\r\n%s" % (content)
        return response.encode()

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

def main():
    PORT = 8000
    HOST = socket.gethostname()
    server = Server()

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))

    def index(con, headers):     
        # Compare when file was last modified to the if-modified-since header
        print("SENDING FILE")
        if "If-Modified-Since" in headers:
            last_m= os.path.getmtime("test.html")
            last_modified = time.ctime(last_m)
            if time.strptime(headers["If-Modified-Since"]) >= time.strptime(last_modified):
                response = server.generate_response(304)
                con.sendall(response)
                return
            # Set the Last-Modified response header to get the If-Modified-Since request header back
        file, last_modified = server.open_file("test.html")
        response = server.generate_response(200, file, {"Content-Type": "text/html", "Last-Modified": last_modified})
        con.sendall(response)

    def protected(con, headers):
        file, last_modified = server.open_file("protected.html")
        response = server.generate_response(200, file, {"Content-Type": "text/html"})
        con.sendall(response)

    def index_post(con, headers):
        con.sendall("HTTP/1.1 200 OK\n\r\n\rSucessfully Posted".encode())

    def internal(con, headers):
        con.sendall("HTTP/1.1 403 Forbidden\n\r\n\rForbidden".encode())

    server.add_route("GET", "/", index)
    server.add_route("POST", "/", index_post)
    server.add_route("GET", "/internal", internal)
    server.add_route("GET", "/protected", protected)

    # t_origin = threading.Thread(target=server.listen, args=(HOST, PORT, 5))
    # # Start proxy
    # t_proxy = threading.Thread(target=proxy_server.listen_proxy, args=(PROXY_HOST, PROXY_PORT, 5))

    # t_origin.start()
    # t_proxy.start()
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
