import socket
from threading import *
import client

# Params: request string
# Returns: request_headers list
def parse_request(request):
    request_headers = request.split("\r\n")
    if len(request_headers) < 1:
        return []
    print(request_headers)
    return request_headers

# Params: http_req string
# Returns: http_method string, endpoint string
def parse_http_method(http_req):
    if type(http_req) != str:
        return "", ""
    parsed_http_request = http_req.split(" ")
    if len(parsed_http_request) < 1:
        return "", ""
    # Method
    http_method, endpoint = parsed_http_request[0], parsed_http_request[1]
    if endpoint == "/favicon.ico":
        return "", ""
    return http_method, endpoint

def main():
    PORT = 8000
    HOST = "localhost"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Initializing server with host %s and port %d \n" % (HOST, PORT))
    server.bind((HOST, PORT))

    server.listen(5)

    testfile = open('test.html', 'r')
    testhtml = testfile.read()

    while True:
        (clientsocket, address) = server.accept()

        print("Got connection from", address)

        # client1 = client.client(socket=clientsocket, address=address)
        # client1.run()
        # client1.send_data('HTTP/1.0 200 OK\nContent-Type: text/html\n\n')
        # client1.send_data(testhtml)
        # client1.close_socket()

        # Request
        request = clientsocket.recv(1024).decode()
        print("Client send:\n%s" % request)

        # Read request
        request_headers = parse_request(request)
        http_method, endpoint = parse_http_method(request_headers[0])
        print("Method: %s\nEndpoint: %s\n" % (http_method, endpoint))
        # Response
        clientsocket.send('HTTP/1.0 200 OK\nContent-Type: text/html\n\n'.encode())
        clientsocket.send(testhtml.encode())
        clientsocket.close()

if __name__ == '__main__':
    main()