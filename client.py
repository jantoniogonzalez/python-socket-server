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
            data = self.socket.recv(1024).decode()
            if not data:
                continue
            self.data = data
            print("Client send:\n%s" % data)

    def send_data(self, data):
        if not data:
            return
        self.socket.send(data.encode())

    def close_socket(self):
        self.socket.close()

    def get_data(self):
        return self.data
     
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    