import socket
import threading
import paramiko
from file_system import VirtualFileSystem

# Згенерований хост-ключ (тимчасовий, для роботи сервера)
HOST_KEY = paramiko.RSAKey.generate(2048)

# Віртуальна файлова система
vfs = VirtualFileSystem()

# Список дозволених публічних ключів
AUTHORIZED_KEYS = [
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCLrRt3cU31Wly3rVYAX5bQoM5CKIPJJOYEfAfMJ/LM4QGTqgY52byz/bREW+PY1ujW6xddylR4G/pPYE1iG+vnft7GdXoeWR8y/pODgM2MNk2ow44r7PrSXskXDX5YR0tEBjfNVAFDskmquUwYcPlRJ01EwJcY8Bg0BQfWX9HLO1Ows82Y2eVdYD5M0rKJKzaQud4nVhqcmUBly0LpNyVilCrHrvypqjGS+AGYiZ/64B/lpPGM+cyFp0S+7p80YBCK6eI4sX+9e25KZj4+wORo6EBsB0iA1UvCp+IOuTbHB39ZGBpGvgDIWOL8Y8B0F5D9t2PAdFe82t439O1pk/qw6VR01UwSuUWPa4WID37KZklW7KdYBmTEmxkyYljD7vo5ZZsY+w1AVrOUf5/LTyBK2lPm3whh0UGvoPRTl7AI9Z8K/0W/1AsYypkHlkrvyjEsR9bhT3jwplou+XXh5RRxn5BJpQZuRXl6PPD5vZqHDTy7hkYJz9iTSooqUwi2Vd8= daniaa@zonex"
]

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_publickey(self, username, key):
        # Отримуємо ключ у вигляді рядка
        key_str = f"{key.get_name()} {key.get_base64()}"
        if key_str in AUTHORIZED_KEYS:
            vfs.init_user(username)
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED if kind == 'session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def handle_connection(client):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)

    server = Server()
    transport.start_server(server=server)
    channel = transport.accept(20)

    if channel is None:
        print("No channel.")
        return

    server.event.wait(10)
    username = transport.get_username()
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

