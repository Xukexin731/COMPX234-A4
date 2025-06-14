import socket
import threading
import os
import base64
import random
def handle_client_request(filename, client_address, server_socket):
    for attempt in range(3):
        port = random.randint(50000, 51000)
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.bind(('', port))
            print(f"[SUCCESS] Data port {port} bound for {filename}")
            break
        except Exception as e:
            print(f"[WARNING] Port {port} bind failed (attempt {attempt + 1}): {str(e)}")
            client_socket.close()
            if attempt == 2:
                server_socket.sendto(f"ERR {filename} PORT_ERROR".encode(), client_address)
                return
