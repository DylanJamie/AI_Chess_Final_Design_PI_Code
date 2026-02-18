import socket
import time

HOST = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"victory")
    time.sleep(3)
    s.sendall(b"lose")
    time.sleep(3)
    s.sendall(b"draw")
    time.sleep(3)
 
        
