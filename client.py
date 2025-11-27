# imports
import socket
import json
import os
import threading

# variuables
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
isConnected = False
hasGroup = False
username = ""
messageLength = 5 #this controls how many messages to show at the top of the screen

users = []
subjects = []
messages = []

# functions
def clear():
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # macOS/Linux
    else:
        os.system('clear')

def get_messages(number):
    client.sendall(json.dumps({"command": "getMessages", "number":number}).encode())

def handle_server():
    global users
    global subjects
    global messages

    while True:
        try:
            response = client.recv(1024).decode().strip()
            response = json.loads(response)

            if not response:
                print("Server disconnected.")
                break

            if "users" in response:
                users = response["users"]

            if "subjects" in response:
                subjects = response["subjects"]

            if "messages" in response:
                messages = response["messages"]    

            updateDisplay()
        except Exception as e:
            print("Listener error:", e)
            break

def updateDisplay():
    clear()
    print(messages)

    if hasGroup:
        count = min(len(subjects), len(messages))
        start = max(0, count - messageLength)

        for i in range(start, count):
            print(f"[{subjects[i]}] {messages[i]}")

def debug(args):
    if not isConnected: 
        isNotConnectedHelper()
        return

    client.sendall(json.dumps({"command": "debug"}).encode())

def alreadyHasGroupHelper():
    print("please connect to the server firsta using the connect command")

def isNotConnectedHelper():
    print("please connect to the server first using the connect command")

def connect(args):
    global isConnected

    HOST = "0.0.0.0" # args[1]
    PORT = 5000      # args[2]

    client.connect((HOST, PORT))
    isConnected = True

    listener_thread = threading.Thread(target=handle_server, daemon=True)
    listener_thread.start()

    username = input("username>")
    
    client.sendall(json.dumps({"command": "setUsername", "username": username}).encode())
    

def join(args):
    global hasGroup
    if not isConnected: 
        isNotConnectedHelper()
        return

    if hasGroup:
        alreadyHasGroupHelper()
        return

    client.sendall(json.dumps({"command": "join"}).encode())
    hasGroup = True

def post(args):
    if not isConnected: 
        isNotConnectedHelper()
        return

    if not hasGroup: 
        alreadyHasGroupHelper()
        return

    subject = input("subject>")

    message = input("message>")

    client.sendall(json.dumps({"command": "post", "subject": subject, "message": message}).encode())

def users_command(args):
    pass
    # if not isConnected: 
    #     isNotConnectedHelper()
    #     return
    #
    # client.sendall(json.dumps({"command": "users_command"}).encode())
    # response = client.recv(1024).decode().strip()
    #
    # try:
    #     users = json.loads(response)
    #     print("users:")
    #     for user in users:
    #         print(user)
    #
    # except json.JSONDecodeError:
    #     print(f"[{addr}] Received invalid JSON: {message}")

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
        updateDisplay()

        userInput = input(username + ">")
        userInput = userInput.split()
        command = userInput[0]
        
        if command in commands:
            commands[command](userInput[1:])
        else:
            print("command not found")

