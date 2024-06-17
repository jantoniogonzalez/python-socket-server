import socket
from threading import *
import client

def parse_request():
    return

def main():
    port = 8000
    host = "localhost"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Initializing server with host %s and port %d \n" % (host, port))
    server.bind((host, port))

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
        

        # Response
        clientsocket.send('HTTP/1.0 200 OK\nContent-Type: text/html\n\n'.encode())
        clientsocket.send(testhtml.encode())
        clientsocket.close()

if __name__ == '__main__':
    main()