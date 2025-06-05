import socket
import threading
import paramiko
from file_system import VirtualFileSystem

import os

HOST_KEY_PATH = "host_keys/ssh_host_rsa_key"

if not os.path.exists(HOST_KEY_PATH):
    os.makedirs("host_keys", exist_ok=True)
    # Генеруємо ключ і зберігаємо у файл
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_PATH)
    print("Host key generated and saved.")
else:
    key = paramiko.RSAKey(filename=HOST_KEY_PATH)
    print("Host key loaded from file.")

HOST_KEY = key

# Віртуальна файлова система
vfs = VirtualFileSystem()
vfs.init_user("test")
vfs.write_file("test", ".ssh/authorized_keys", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJX3tHXdehuJHkGl/mcApERHd3Huy5YUs+cZJO6gZZQ6")  # Додайте тут ваші дозволені публічні ключі #тут можна додати користувачі як тут показано на прикладі
vfs.init_user("root")
vfs.write_file("root", ".ssh/authorized_keys", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINmX+iJKBlqlXkLvJ8OA9WrO8+bmf5PTcaUNw2/Lig/L")  # Додайте тут ваші дозволені публічні ключі

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_publickey(self, username, key):
        key_str = f"{key.get_name()} {key.get_base64()}"
        print(f"Received key: {key_str}")
        if key_str == vfs.read_file(username, ".ssh/authorized_keys"):
            return paramiko.AUTH_SUCCESSFUL
            
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def handle_connection(client):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)

    server = Server()
    transport.start_server(server=server)
    
    channel = transport.accept(30)  # Збільшений тайм-аут

    if channel is None:
        print("No channel. Timeout or authentication failure.")
        return

    server.event.wait(10)
    username = transport.get_username()
    print(f"Authenticated user: {username}")
    channel.send(f"Welcome {username}!\n")

    while True:
        channel.send(f"{username}@vfs$ ")
        command = ""
        while not command.endswith("\n"):
            data = channel.recv(1024)
            if not data:
                break
            command += data.decode("utf-8")

        command = command.strip()
        if command == "exit":
            channel.send("Bye!\n")
            break
        elif command.startswith("ls"):
            files = vfs.list_files(username)
            channel.send("\n".join(files) + "\n")
        elif command.startswith("cat "):
            _, filename = command.split(" ", 1)
            content = vfs.read_file(username, filename)
            channel.send(content + "\n")
        elif command.startswith("write "):
            _, filename = command.split(" ", 1)
            channel.send("Enter content (end with 'EOF'):\n")
            content = ""
            while True:
                line = channel.recv(1024).decode("utf-8")
                if line.strip() == "EOF":
                    break
                content += line
            message = vfs.write_file(username, filename, content)
            channel.send(message + "\n")
        elif command.startswith("rm "):
            _, filename = command.split(" ", 1)
            message = vfs.delete_file(username, filename)
            channel.send(message + "\n")
        else:
            channel.send("Unknown command.\n")

    channel.close()

def start_ssh_server(port=2200):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(100)
    print(f"Listening for SSH connections on port {port}...")

    while True:
        client, addr = sock.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_connection, args=(client,)).start()

if __name__ == "__main__":
    start_ssh_server()

