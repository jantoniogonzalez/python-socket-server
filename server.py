import socket
from threading import *
from dataclasses import dataclass
import client

@dataclass
class Route:
    method: str
    endpoint: str

class Server():
    def __init__(self, socket, routes = [Route("GET", "/test.html")]):
        # routes = list of Route
        self.routes = routes
        self.socket = socket
        self.connections = {}

    def initialize_socket(self, host, port, num_connections):
        self.socket.bind((host, port))
        self.socket.listen(num_connections)

    def accept_connection(self):
        connection, addr =  self.socket.accept()
        return connection, addr
    
    def add_route(self, route):
        self.routes.append(route)


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
    return http_method, endpoint

# Params: http_method string, endpoint string, routes list[tuple]
# Returns: bool
# Checks if route_exists
def route_exists(http_method, endpoint, routes):
    for route in routes:
        if route.method == http_method and route.endpoint == endpoint:
            return True
    return False

# Use when route_exists returns false
def check_inexistent_route(endpoint, routes):
    for route in routes:
        if route.endpoint == endpoint:
            return 400
    return 404

# Use when route_exists return true


def main():
    PORT = 8000
    HOST = "localhost"
    server = Server(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))
    server.initialize_socket(HOST, PORT, 5)

    testfile = open('test.html', 'r')
    testhtml = testfile.read()
    testfile.close()

    while True:
        (connection, address) = server.accept_connection()
        print(server.__getattribute__("connections"))

        print("Got connection from", address)

        # client1 = client.client(socket=clientsocket, address=address)
        # client1.run()
        # client1.send_data('HTTP/1.0 200 OK\nContent-Type: text/html\n\n')
        # client1.send_data(testhtml)
        # client1.close_socket()

        
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
            if not http_method and not endpoint:
                connection.close()
                continue
            print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

            routes_example = [Route("GET", "/hola"), Route("GET", "/")]
            if not route_exists(http_method, endpoint, routes_example):
                error_code = check_inexistent_route(endpoint, routes_example)
                print("Got error code %d\n from check_inexistent_route" % error_code)
            else:
                print("No errors... yet!")

            parsed_headers = parse_headers(request_headers)
            print("Dictionary with headers: \n%s\n" % parsed_headers)


            # Response
            # Set the Last-Modified response header to get the If-Modified-Since request header back
            connection.send('HTTP/1.0 200 OK\nContent-Type: text/html\nLast-Modified: Tue, 18 Jun 2024 00:26:59 GMT\n'.encode())
            connection.send(testhtml.encode())

if __name__ == '__main__':
    main()

'''
1. Check Route
If Route Exists:
    2. Call "handler"
    3. Check cache
'''