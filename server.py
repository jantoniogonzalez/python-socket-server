import socket
from threading import *
import client

class Server():
    def __init__(self, socket, routes = [('GET', '/test.html', 'test.html')]):
        # routes = [("METHOD", "ENDPOINT")]
        self.routes = routes
        self.socket = socket

    def initialize_socket(self, host, port, connections):
        self.socket.bind((host, port))
        self.socket.listen(connections)

    def accept_connection(self):
        connection, addr =  self.socket.accept()
        return connection, addr
    
    def add_route(self, route):
        self.routes.appen(route)

    def get_routes(self):
        return self.routes

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

def route_exists(http_method, endpoint, routes):
    for route in routes:
        if route[0] == http_method and route[1] == endpoint:
            return True
    return False

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

        print("Got connection from", address)

        # client1 = client.client(socket=clientsocket, address=address)
        # client1.run()
        # client1.send_data('HTTP/1.0 200 OK\nContent-Type: text/html\n\n')
        # client1.send_data(testhtml)
        # client1.close_socket()

        # Request
        request = connection.recv(1024).decode()
        print("Client send:\n%s" % request)

        # Read request
        request_headers = parse_request(request)
        http_method, endpoint = parse_http_method(request_headers[0])
        if not http_method and not endpoint:
            connection.close()
            continue
        print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))

        parsed_headers = parse_headers(request_headers)
        print("Dictionary with headers: \n%s\n" % parsed_headers)


        # Response
        connection.send('HTTP/1.0 200 OK\nContent-Type: text/html\n\n'.encode())
        connection.send(testhtml.encode())

if __name__ == '__main__':
    main()