# file_system.py

class VirtualFileSystem:
    def __init__(self):
        self.users = {}  # {'username': {'filename': 'content'}}

    def init_user(self, username):
        if username not in self.users:
            self.users[username] = {}

    def list_files(self, username):
        return list(self.users.get(username, {}).keys())

    def read_file(self, username, filename):
        return self.users.get(username, {}).get(filename, "File not found.")

    def write_file(self, username, filename, content):
        self.users[username][filename] = content
        return f"File '{filename}' saved."

    def delete_file(self, username, filename):
        if filename in self.users[username]:
            del self.users[username][filename]
            return f"File '{filename}' deleted."
        return "File not found."

