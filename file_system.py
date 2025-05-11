import json
import os

class VirtualFileSystem:
    def __init__(self, filename="vfs.json"):
        self.filename = filename
        self.users = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.users, f, indent=2)

    def init_user(self, username):
        if username not in self.users:
            self.users[username] = {}
            self.save()

    def list_files(self, username):
        return list(self.users.get(username, {}).keys())

    def read_file(self, username, filename):
        return self.users.get(username, {}).get(filename, "File not found.")

    def write_file(self, username, filename, content):
        self.users[username][filename] = content
        self.save()
        return f"File '{filename}' saved."

    def delete_file(self, username, filename):
        if filename in self.users[username]:
            del self.users[username][filename]
            self.save()
            return f"File '{filename}' deleted."
        return "File not found."

