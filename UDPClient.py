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
    print(f"Requesting file: {filename}")
    try:
        response = send_and_receive(sock, f"DOWNLOAD {filename}", (server_host, server_port))
    except Exception as e:
        print(f"  Download failed: {e}")
        return False
    
    # 处理响应
    parts = response.split()
    if parts[0] == "ERR":
        print(f"  Server error: {' '.join(parts[1:])}")
        return False
    
    if parts[0] != "OK" or len(parts) < 6 or parts[2] != "SIZE" or parts[4] != "PORT":
        print(f"  Invalid response: {response}")
        return False
    
    try:
        file_size = int(parts[3])
        data_port = int(parts[5])
        print(f"  File size: {file_size} bytes, Data port: {data_port}")
    except ValueError:
        print(f"  Invalid size/port in response: {response}")
        return False
    
    try:
        with open(filename, 'wb') as f:
            block_size = 1000
            downloaded = 0  
            
            while downloaded < file_size:
                start = downloaded  
                end = min(downloaded + block_size - 1, file_size - 1) 
                
                request_msg = f"FILE {filename} GET START {start} END {end}"
                try:
                    response = send_and_receive(sock, request_msg, (server_host, data_port))
                except Exception as e:
                    print(f"  Block download failed: {e}")
                    return False
                
                data_parts = response.split()
                if (len(data_parts) < 7 or data_parts[0] != "FILE" or data_parts[1] != filename or 
                    data_parts[2] != "OK" or data_parts[3] != "START" or data_parts[5] != "END"):
                    print(f"  Invalid data response: {response[:50]}")
                    return False
                
                data_idx = response.find("DATA ") + 5 
                if data_idx < 5:
                    print("  DATA field missing")
                    return False
                
                base64_data = response[data_idx:]
                try:
                    file_data = base64.b64decode(base64_data)
                except Exception:
                    print("  Base64 decode error")
                    return False
        
                f.seek(start)  
                f.write(file_data)
                downloaded += len(file_data)  
                print('*', end='', flush=True)  
            
            print("\n  File download complete")
            
 
            try:
                close_resp = send_and_receive(sock, f"FILE {filename} CLOSE", 
                                            (server_host, data_port))
                if close_resp != f"FILE {filename} CLOSE_OK":
                    print("  Invalid close confirmation")
            except Exception as e:
                print(f"  Close failed: {e}")
                return False
            
            return True
            
    except IOError as e:
        print(f"  File I/O error: {e}")
        return False
def main():
    if len(sys.argv) != 4:
        print("Usage: python UDPClient.py <server_host> <server_port> <file_list>")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    file_list_path = sys.argv[3]
    if not os.path.exists(file_list_path):
        print(f"File list not found: {file_list_path}")
        sys.exit(1)
    
    with open(file_list_path, 'r') as f:
        files = [line.strip() for line in f if line.strip()]
    
    if not files:
        print("No files specified in file list")
        sys.exit(1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)