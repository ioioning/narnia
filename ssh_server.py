import socket
import threading
import paramiko
from file_system import VirtualFileSystem

HOST_KEY = paramiko.RSAKey.generate(2048)
vfs = VirtualFileSystem()

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.username = None

    def check_auth_none(self, username):
        self.username = username
        vfs.init_user(username)
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return 'none'

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

    channel = transport.accept(30)
    if channel is None:
        print("No channel. Timeout or authentication failure.")
        return

    server.event.wait(10)
    username = server.username or "unknown"
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

