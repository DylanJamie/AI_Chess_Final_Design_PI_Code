import socket
import time

HOST = "127.0.0.1"
PORT = 1234

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    s.connect((HOST,PORT))
    
    for _ in range(100):
        s.sendall(b"victory")
        time.sleep(1)
        s.sendall(b"lose")
        time.sleep(1)
        s.sendall(b"draw")
        time.sleep(1)
 
        
