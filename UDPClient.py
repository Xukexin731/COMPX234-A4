import socket
import sys
import base64
import os
MAX_RETRIES = 5
INITIAL_TIMEOUT = 500
def send_and_receive(sock, message, server_address, timeout=2, max_retries=3):
    for attempt in range(max_retries):
         try:
            sock.sendto(message.encode(), server_address)
            sock.settimeout(timeout * (attempt + 1))
            response, _ = sock.recvfrom(4096)
            return response.decode().strip()
         except socket.timeout:
            print(f"[RETRY] Timeout (attempt {attempt + 1})")
         except Exception as e:
            print(f"[ERROR] Communication error: {str(e)}")
            break
    return None

def download_file(control_sock, filename, server_address):
    response = send_and_receive(control_sock, f"DOWNLOAD {filename}", server_address)
    if not response:
        print(f"[FAILED] No response for {filename}")
        return False
    if response.startswith("ERR"):
        print(f"[ERROR] Server response: {response}")
        return False
    # Parse the OK response
    parts = response.split()
    file_size = int(parts[3])
    data_port = int(parts[5])
    data_address = (server_address[0], data_port)
    print(f"[INFO] Downloading {filename} ({file_size} bytes) via port {data_port}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as data_sock:
        data_sock.settimeout(5)
    
        try:
            with open(filename, 'wb') as f:
                downloaded = 0
                while downloaded < file_size:
                    start = downloaded
                    end = min(start + 999, file_size - 1)
                    request = f"FILE {filename} GET START {start} END {end}"
    
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
    # Parse command-line arguments
    if len(sys.argv) != 4:
        print("Usage: python3 UDPclient.py <hostname> <port> <files.txt>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    fileslist = sys.argv[3]
    server_address = (host, port)

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (hostname, port)

    # Read the file list
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as control_sock:
        control_sock.settimeout(3)

        try:
            with open(filelist) as f:
                files = [line.strip() for line in f if line.strip()]

            for filename in files:
                if not download_file(control_sock, filename, server_address):
                    print(f"[WARNING] Failed to download {filename}")

        except FileNotFoundError:
            print(f"[ERROR] File list {filelist} not found")
        except Exception as e:
            print(f"[ERROR] Fatal error: {str(e)}")

if __name__ == "__main__":
    main()