import socket
import sys
import base64
import os
MAX_RETRIES = 5
INITIAL_TIMEOUT = 500
def send_and_receive(sock, message, address, max_retries=MAX_RETRIES, initial_timeout=INITIAL_TIMEOUT):
    retries = 0
    timeout = initial_timeout
    while retries < max_retries:
        try:
            sock.sendto(message.encode(), address)
            sock.settimeout(timeout / 1000)
            response, _ = sock.recvfrom(65536)
            return response.decode()
        except socket.timeout:
            retries += 1
            timeout *= 2
            print(f"  Timeout (attempt {retries}/{max_retries}), retrying...")
    raise Exception("Max retries exceeded")
    def download_file(sock, server_host, server_port, filename):
        response = send_and_receive(sock, f"DOWNLOAD {filename}", (server_host, server_port))
        parts = response.split()
        if parts[0] == "ERR":
            return False
        file_size = int(parts[3])
        data_port = int(parts[5])
        with open(filename, 'wb') as f:
            while downloaded < file_size:
            request_msg = f"FILE {filename} GET START {start} END {end}"
            response = send_and_receive(sock, request_msg, (server_host, data_port))
            data_parts = response.split()
            base64_data = response[data_idx:]
            file_data = base64.b64decode(base64_data)