import socket
import time

HOST = "127.0.0.1"
PORT = 1234


global_win_counter = 50



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    s.connect((HOST,PORT))
    
    for _ in range(100):
        s.sendall(b"victory\n")
        time.sleep(2)
        s.sendall(b"lose\n")
        time.sleep(2)
        s.sendall(f"score\n{global_win_counter}\n".encode())
        time.sleep(2)
 
        
