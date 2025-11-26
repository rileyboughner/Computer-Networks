# imports
import socket
import threading
import os
import json

# variuables
HOST = "0.0.0.0"
users = []
groups = []

# classes
class Message:
    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

class Group:
    def __init__(self, name):
        self.name = name
        self.users = []
        self.messages = []
        

class User:
    def __init__(self, conn, addr):
        self.conn = conn 
        self.addr = addr
        self.username = self.addr
        self.groupid = ""
        self.group = ""
    
    def getUsername(self):
        return self.username

    def setUsername(self, username):
        self.username = username

# functions
def debug(user, args):
    print("---groups---")
    for group in groups:
        print(group.name)
        print(group.users)
    print()
    print("---users---")
    for user in users:
        print(user.username)
        print(user.group)
        print()

def add_message_to_group(message, group):
    pass

def remove_from_group(username, groupid):
    groups[groupid].users.remove(username)

def join(user, args):
    user.username = args["username"]

    groups[0].users.append(args["username"])
    user.group = groups[0].name
    user.groupid = 0

def post(user, args):
    message = Message()
    add_message_to_group(message, group)

    # notify everyone of the new message?

def users_command(user, args):
    user.conn.sendall(json.dumps(groups[user.groupid].users).encode())

def leave(user, args):
    remove_from_group(user.username, user.groupid)

def handle_client(user):
    addr = user.addr
    conn = user.conn
    print(f"Connected by {addr}")

    with conn:
        while True:
            createDisplay()
            try:
                # Receive raw bytes
                data = conn.recv(1024)
                if not data:  # client disconnected
                    break

                message = data.decode().strip()

                try:
                    data = json.loads(message)
                    commands[data["command"]](newUser, data)

                except json.JSONDecodeError:
                    print(f"[{addr}] Received invalid JSON: {message}")

            except ConnectionResetError:
                break

    users.remove(newUser)

    remove_from_group(newUser.username, newUser.groupid)

    createDisplay()

def clear():
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # macOS/Linux
    else:
        os.system('clear')

def createDisplay():
    #clear()
    print("users online: " + str(len(users)))
    print()
    for group in groups:
        print(group.name)
        for user in group.users:
            print(user)


# commands
commands = {
        "debug": debug,
        "join": join,
        "post": post,
        "users_command": users_command,
        "leave": leave,
    }


# main loop
if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #this will automatically find and open port that is available
    while True:
        try:
            server.bind((HOST, PORT))
            break
        except OSError:
            print("port " + str(PORT) + " in use")
            PORT = PORT + 1

    server.listen()
    print(f"Server listening on {HOST}:{PORT} waiting for first client connection")

    #this creates the main default chatroom
    group = Group("main")
    groups.append(group)

    while True:
        conn, addr = server.accept()
        
        newUser = User(conn, addr)
        users.append(newUser)

        # create a new thread for each client
        thread = threading.Thread(target=handle_client, args=(newUser, ), daemon=True)
        thread.start()
