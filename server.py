import socket
from threading import *

class client(Thread):
    def __init__(self, socket, address):
        Thread.__init__(self)
        self.socket = socket
        self.address = address
        # Start thread
        self.start()
        self._stop_event = Event()
    def run(self):
        while 1:
            print("Client send:\n%s" % self.socket.recv(1024).decode())
    def stop(self):
        self._stop_event.set()
    def stopped(self):
        return self._stop_event.is_set()


port = 8080
host = "localhost"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Initializing server with host %s and port %d \n" % (host, port))
server.bind((host, port))

server.listen(5)

while True:
    (clientsocket, address) = server.accept()

    print("Got connection from", address)

    client1 = client(socket=clientsocket, address=address)
    client1.run()
    message = "Thank you for connecting"
    message_bytes = message.encode("ascii")
    server.send("SUp mate".encode())
    
    client.stop()
    clientsocket.close()

    break