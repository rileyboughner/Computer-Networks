# imports
import socket
import json
import os

# variuables
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
isConnected = False
hasGroup = False
username = ""

# functions
def clear():
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # macOS/Linux
    else:
        os.system('clear')

def get_messages(number):
    for i in range(number):
        print("Placeholder message")

def display_messages():
    if hasGroup:
        get_messages(2)
        print()
    
def debug(args):
    if not isConnected: 
        isNotConnectedHelper()
        return

    client.sendall(json.dumps({"command": "debug"}).encode())

def isNotConnectedHelper():
    print("please connect to the server first using the connect command")

def connect(args):
    global isConnected

    HOST = "0.0.0.0" # args[1]
    PORT = 5000      # args[2]

    client.connect((HOST, PORT))
    isConnected = True

    username = input("username>")
    
    client.sendall(json.dumps({"command": "setUsername", "username": username}).encode())
    

def join(args):
    global hasGroup
    if not isConnected: 
        isNotConnectedHelper()
        return

    client.sendall(json.dumps({"command": "join"}).encode())
    hasGroup = True

def post(args):
    if not isConnected: 
        isNotConnectedHelper()
        return

    subject = input("subject>")

    message = input("message>")

    client.sendall(json.dumps({"command": "post", "subject": subject, "message": message}).encode())

def users_command(args):

    if not isConnected: 
        isNotConnectedHelper()
        return

    client.sendall(json.dumps({"command": "users_command"}).encode())
    response = client.recv(1024).decode().strip()

    try:
        users = json.loads(response)
        print("users:")
        for user in users:
            print(user)

    except json.JSONDecodeError:
        print(f"[{addr}] Received invalid JSON: {message}")

def leave(args):
    global hasGroup

    if not isConnected: 
        isNotConnectedHelper()
        return

    client.sendall(json.dumps({"command": "leave"}).encode())
    
    hasGroup = False

def message(args):
    print(args)

def groups(args):
    print(args)

def groupspost(args):
    print(args)

def groupusers(args):
    print(args)

def groupleave(args):
    print(args)

def groupmessage(args):
    print(args)

def exit(args):
    print("closing connection")
    isConnected = False
    client.close()
    quit()

# commands
commands = {
        "debug": debug,
        "connect": connect,
        "join": join,
        "post": post,
        "users": users_command,
        "leave": leave,
        "message": message,
        "groups": groups,
        "groupspost": groupspost,
        "groupusers": groupusers,
        "groupleave": groupleave,
        "groupmessage": groupmessage,
        "exit": exit,
    }

# main loop
if __name__ == "__main__":
    while True:
        clear()

        display_messages()

        userInput = input(str(hasGroup) + ">")
        userInput = userInput.split()
        command = userInput[0]
        
        if command in commands:
            commands[command](userInput[1:])
        else:
            print("command not found")

