import socket as s

PORT = 8000


def main():
    with s.socket(s.AF_INET, s.SOCK_STREAM) as socket:
        socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        socket.bind(("", PORT))
        socket.listen(1)
        while True:
            connection, addr = socket.accept()
            with connection:
                chunks = []
                chunk = connection.recv(1024).decode()
                chunks.append(chunk)
                while "\r\n" not in chunk:
                    chunk = connection.recv(1024).decode()
                    print(chunk)
                    chunks.append(chunk)

                resStr = "".join(chunks)

                res = "HTTP/1.1 200 OK\r\n\r\n<h1>Test</h1>"
                connection.sendall(res.encode())

                print("finished sending!")


if __name__ == "__main__":
    main()
