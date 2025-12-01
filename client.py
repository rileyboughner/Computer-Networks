import socket
import threading
import os

JOIN = 0x01
GROUP_JOIN = 0xA1
POST = 0x02
GROUP_POST = 0xA2
USERS = 0x03
GROUP_USERS = 0xA3
LEAVE = 0x04
GROUP_LEAVE = 0xA4
MESSAGE = 0x05
GROUP_MESSAGE = 0xA5
EXIT = 0x06
GROUPS = 0x07
ERROR = 0xFF

thread_stop = threading.Event()
print_lock = threading.Lock()
active_connection = False
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def await_message():
    global sock
    global active_connection
    while not thread_stop.is_set():
        if active_connection:
            incoming = sock.recv(1024)
            parse_received_message(incoming)

message_thread = threading.Thread(target=await_message, daemon=True)

def join(username: str):
    body = bytes([JOIN])
    username_bytes = username.encode('utf-8')
    body += len(username_bytes).to_bytes(2, 'little') + username_bytes
    send_message(body)

def group_join(group_id: str, username: str):
    body = bytes([GROUP_JOIN])
    group_bytes = group_id.encode('utf-8')
    body += len(group_bytes).to_bytes(2, 'little') + group_bytes
    username_bytes = username.encode('utf-8')
    body += len(username_bytes).to_bytes(2, 'little') + username_bytes
    send_message(body)

def post(subject: str, message: str):
    body = bytes([POST])
    subject_bytes = subject.encode('utf-8')
    message_bytes = message.encode('utf-8')
    body += len(subject_bytes).to_bytes(2, 'little') + subject_bytes
    body += len(message_bytes).to_bytes(2, 'little') + message_bytes
    send_message(body)

def group_post(group_id: str, subject: str, message: str):
    body = bytes([GROUP_POST])
    subject_bytes = subject.encode('utf-8')
    message_bytes = message.encode('utf-8')
    group_bytes = group_id.encode('utf-8')
    body += len(group_bytes).to_bytes(2, 'little') + group_bytes
    body += len(subject_bytes).to_bytes(2, 'little') + subject_bytes
    body += len(message_bytes).to_bytes(2, 'little') + message_bytes
    send_message(body)

def users():
    body = bytes([USERS])
    send_message(body)

def group_users(group_id: str):
    body = bytes([GROUP_USERS])
    group_bytes = group_id.encode('utf-8')
    body += len(group_bytes).to_bytes(2, 'little') + group_bytes
    send_message(body)

def leave():
    body = bytes([LEAVE])
    send_message(body)

def group_leave(group_id: str):
    body = bytes([GROUP_LEAVE])
    group_bytes = group_id.encode('utf-8')
    body += len(group_bytes).to_bytes(2, 'little') + group_bytes
    send_message(body)

def message_command(id: str):
    body = bytes([MESSAGE])
    id_bytes = id.encode('utf-8')
    body += len(id_bytes).to_bytes(2, 'little') + id_bytes
    send_message(body)

def group_message_command(group_id: str, msg_id: str):
    body = bytes([MESSAGE])
    group_bytes = group_id.encode('utf-8')
    body += len(group_bytes).to_bytes(2, 'little') + group_bytes
    id_bytes = msg_id.encode('utf-8')
    body += len(id_bytes).to_bytes(2, 'little') + id_bytes
    send_message(body)

def groups():
    body = bytes([GROUPS])
    send_message(body)

def exit_command():
    body = bytes([EXIT])
    send_message(body)

def send_message(body: bytes):
    global sock
    global active_connection
    if active_connection:
        prefix = bytes([0xF0, 0x0D, 0xBE, 0xEF]) + len(body).to_bytes(2, 'little') + body
        try:
            sock.sendall(prefix)
        except:
            pass

def parse_received_message(message: bytes):
    if len(message) < 7 or message[0:4] != bytes([0xF0, 0x0D, 0xBE, 0xEF]) or int.from_bytes(message[4:6], 'little') + 6 != len(message):
        return
    op_code = message[6]
    if op_code == ERROR:
        error_length = int.from_bytes(message[7:9], 'little')
        error_message = message[9:9+error_length].decode('utf-8')
        # print in red text
        with print_lock:
            print(f"\n\033[91mError from server: {error_message}\033[0m", end='', flush=True)
    elif op_code == USERS:
        user_count = int.from_bytes(message[7:9], 'little')
        users = []
        index = 9
        for _ in range(user_count):
            username_length = int.from_bytes(message[index:index+2], 'little')
            index += 2
            username = message[index:index+username_length].decode('utf-8')
            index += username_length
            users.append(username)
        with print_lock:
            print(f"\nActive users: \n{'\n'.join(users)}", end='', flush=True)
    elif op_code == GROUP_USERS:
        user_count = int.from_bytes(message[7:9], 'little')
        users = []
        index = 9
        for _ in range(user_count):
            username_length = int.from_bytes(message[index:index+2], 'little')
            index += 2
            username = message[index:index+username_length].decode('utf-8')
            index += username_length
            users.append(username)
        group_id_length = int.from_bytes(message[index:index+2], 'little')
        index += 2
        group_id = message[index:index+group_id_length].decode('utf-8')
        index += group_id_length
        group_name_length = int.from_bytes(message[index:index+2], 'little')
        index += 2
        group_name = message[index:index+group_name_length].decode('utf-8')
        with print_lock:
            print(f"\nActive users of \"{group_name}\" (id: {group_id}): \n{'\n'.join(users)}", end='', flush=True)
    elif op_code == POST:
        id_length = int.from_bytes(message[7:9], 'little')
        id = message[9:9+id_length].decode('utf-8')
        sender_length = int.from_bytes(message[9+id_length:11+id_length], 'little')
        sender = message[11+id_length:11+id_length+sender_length].decode('utf-8')
        date_length = int.from_bytes(message[11+id_length+sender_length:13+id_length+sender_length], 'little')
        date = message[13+id_length+sender_length:13+id_length+sender_length+date_length].decode('utf-8')
        subject_length = int.from_bytes(message[13+id_length+sender_length+date_length:15+id_length+sender_length+date_length], 'little')
        subject = message[15+id_length+sender_length+date_length:15+id_length+sender_length+date_length+subject_length].decode('utf-8')
        with print_lock:
            print(f"\nID: {id}\nFrom: {sender}\nDate: {date}\nSubject: {subject}", end='', flush=True)
    elif op_code == GROUP_POST:
        id_length = int.from_bytes(message[7:9], 'little')
        id = message[9:9+id_length].decode('utf-8')
        sender_length = int.from_bytes(message[9+id_length:11+id_length], 'little')
        sender = message[11+id_length:11+id_length+sender_length].decode('utf-8')
        date_length = int.from_bytes(message[11+id_length+sender_length:13+id_length+sender_length], 'little')
        date = message[13+id_length+sender_length:13+id_length+sender_length+date_length].decode('utf-8')
        subject_length = int.from_bytes(message[13+id_length+sender_length+date_length:15+id_length+sender_length+date_length], 'little')
        subject = message[15+id_length+sender_length+date_length:15+id_length+sender_length+date_length+subject_length].decode('utf-8')
        group_id_length = int.from_bytes(message[15+id_length+sender_length+date_length+subject_length:17+id_length+sender_length+date_length+subject_length], 'little')
        group_id = message[17+id_length+sender_length+date_length+subject_length:17+id_length+sender_length+date_length+subject_length+group_id_length].decode('utf-8')
        group_name_length = int.from_bytes(message[17+id_length+sender_length+date_length+subject_length+group_id_length:19+id_length+sender_length+date_length+subject_length+group_id_length], 'little')
        group_name = message[19+id_length+sender_length+date_length+subject_length+group_id_length:19+id_length+sender_length+date_length+subject_length+group_id_length+group_name_length].decode('utf-8')
        with print_lock:
            print(f"\nFROM Group \"{group_name}\" (id: {group_id}):", end='', flush=True)
            print(f"\nID: {id}\nFrom: {sender}\nDate: {date}\nSubject: {subject}", end='', flush=True)
    elif op_code == JOIN:
        username_length = int.from_bytes(message[7:9], 'little')
        username = message[9:9+username_length].decode('utf-8')
        with print_lock:
            print(f"\nUser {username} has joined the chat.", end='', flush=True)
    elif op_code == GROUP_JOIN:
        username_length = int.from_bytes(message[7:9], 'little')
        username = message[9:9+username_length].decode('utf-8')
        group_id_length = int.from_bytes(message[9+username_length:11+username_length], 'little')
        group_id = message[11+username_length:11+username_length+group_id_length].decode('utf-8')
        group_name_length = int.from_bytes(message[11+username_length+group_id_length:13+username_length+group_id_length], 'little')
        group_name = message[13+username_length+group_id_length:13+username_length+group_id_length+group_name_length].decode('utf-8')
        with print_lock:
            print(f"\nUser {username} has joined group \"{group_name}\" (id: {group_id})", end='', flush=True)
    elif op_code == LEAVE:
        username_length = int.from_bytes(message[7:9], 'little')
        username = message[9:9+username_length].decode('utf-8')
        with print_lock:
            print(f"\nUser {username} has left the chat.", end='', flush=True)
    elif op_code == GROUP_LEAVE:
        username_length = int.from_bytes(message[7:9], 'little')
        username = message[9:9+username_length].decode('utf-8')
        group_id_length = int.from_bytes(message[9+username_length:11+username_length], 'little')
        group_id = message[11+username_length:11+username_length+group_id_length].decode('utf-8')
        group_name_length = int.from_bytes(message[11+username_length+group_id_length:13+username_length+group_id_length], 'little')
        group_name = message[13+username_length+group_id_length:13+username_length+group_id_length+group_name_length].decode('utf-8')
        with print_lock:
            print(f"\nUser {username} has left group \"{group_name}\" (id: {group_id})", end='', flush=True)
    elif op_code == MESSAGE:
        body_length = int.from_bytes(message[7:9], 'little')
        body = message[9:9+body_length].decode('utf-8')
        with print_lock:
            print(f"\n--------------------------------------\n{body}\n--------------------------------------", end='', flush=True)
    elif op_code == GROUPS:
        group_count = int.from_bytes(message[7:9], 'little')
        groups = []
        index = 9
        for _ in range(group_count):
            group_id_length = int.from_bytes(message[index:index+2], 'little')
            index += 2
            group_id = message[index:index+group_id_length].decode('utf-8')
            index += group_id_length
            group_name_length = int.from_bytes(message[index:index+2], 'little')
            index += 2
            group_name = message[index:index+group_name_length].decode('utf-8')
            index += group_name_length
            groups.append(f"\"{group_name}\" (id: {group_id})")
        with print_lock:
            print(f"\nActive groups: \n{'\n'.join(groups)}", end='', flush=True)
    with print_lock:
        print("\n> ", end='', flush=True)

def parse_command(command: str):
    global message_thread
    global sock
    global active_connection
    if command.find('"') != -1:
        parts = []
        temp = ''
        in_quotes = False
        for char in command:
            if char == '"':
                in_quotes = not in_quotes
                if not in_quotes:
                    parts.append(temp)
                    temp = ''
            elif char == ' ' and not in_quotes:
                if temp:
                    parts.append(temp)
                    temp = ''
            else:
                temp += char
        if temp:
            parts.append(temp)
        tokens = parts
        # if no second quote, raise invalid command
        if in_quotes:
            with print_lock:
                print("\nInvalid command: unmatched quotes.\n> ", end='', flush=True)
            return
    else:
        tokens = command.strip().split(' ')
    if not tokens:
        return
    cmd = tokens[0].lower()
    if cmd == 'connect':
        if len(tokens) != 3:
            with print_lock:
                print("\nUsage: connect <ip> <port>\n> ", end='', flush=True)
            return
        if active_connection:
            with print_lock:
                print("\nAlready connected to a server.\n> ", end='', flush=True)
            return
        ip = tokens[1]
        try:
            port = int(tokens[2])
        except ValueError:
            with print_lock:
                print("\nPort must be an integer.\n> ", end='', flush=True)
            return
        try:
            sock.connect((ip, port))
            with print_lock:
                print(f"\nConnected to {ip}:{port}\n> ", end='', flush=True)
        except Exception as e:
            with print_lock:
                print(f"\nFailed to connect to {ip}:{port} - {e}\n> ", end='', flush=True)
        active_connection = True
        message_thread.start()
    elif cmd == 'join':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        if len(tokens) != 2:
            with print_lock:
                print("\nUsage: join <username>\n> ", end='', flush=True)
            return
        join(tokens[1])
        with print_lock:
            print("\n> ", end='', flush=True)
    elif cmd == 'post':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        if len(tokens) != 3:
            with print_lock:
                print("\nUsage: post <subject> <message>\n> ", end='', flush=True)
            return
        subject = tokens[1]
        message = ' '.join(tokens[2:])
        post(subject, message)
    elif cmd == 'users':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        users()
    elif cmd == 'leave':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        leave()
        with print_lock:
            print("\n> ", end='', flush=True)
    elif cmd == 'message':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        if len(tokens) != 2:
            with print_lock:
                print("\nUsage: message <id>\n> ", end='', flush=True)
            return
        message_command(tokens[1])
    elif cmd == 'groups':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        groups()
    elif cmd == 'groupjoin':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        if len(tokens) != 3:
            with print_lock:
                print("\nUsage: groupjoin <group_id> <username>\n> ", end='', flush=True)
            return
        group_id = tokens[1]
        username = tokens[2]
        group_join(group_id, username)
        with print_lock:
            print("\n> ", end='', flush=True)
    elif cmd == 'grouppost':
        if not active_connection:
            with print_lock:
                print("\nNot connected to any server. Use 'connect <ip> <port>' first.\n> ", end='', flush=True)
            return
        if len(tokens) != 4:
            with print_lock:
                print("\nUsage: grouppost <group_id> <subject> <message>\n> ", end='', flush=True)
            return
        group_id = tokens[1]
        subject = tokens[2]
        message = tokens[3]
        group_post(group_id, subject, message)
    elif cmd == 'groupusers':
        if len(tokens) != 2:
            with print_lock:
                print("\nUsage: groupjoin <group_id>\n> ", end='', flush=True)
            return
        group_id = tokens[1]
        group_users(group_id)
    elif cmd == 'groupmessage':
        if len(tokens) != 3:
            with print_lock:
                print("\nUsage: groupjoin <group_id>\n> ", end='', flush=True)
            return
        group_id = tokens[1]
        message_id = tokens[2]
        group_message_command(group_id, message_id)
    elif cmd == 'groupleave':
        if len(tokens) != 2:
            with print_lock:
                print("\nUsage: groupjoin <group_id>\n> ", end='', flush=True)
            return
        group_id = tokens[1]
        group_leave(group_id)
        with print_lock:
            print("\n> ", end='', flush=True)
    elif cmd == 'help':
        with print_lock:
            print("\nAvailable commands:\n\t", end='', flush=True)
            print("connect <ip> <port>: Connects to a server on the given ip address and port\n\t", end='', flush=True)
            print("exit: Leave all groups and quit program\n\t", end='', flush=True)
            print("groupjoin <group_id> <username>: Joins a private group with a given username\n\t", end='', flush=True)
            print("groupleave <group_id>: Leaves a private group\n\t", end='', flush=True)
            print("groupmessage <group_id> <message_id>: View a message from a private group\n\t", end='', flush=True)
            print("grouppost <group_id< <subject> <body>: Posts to a private group\n\t", end='', flush=True)
            print("groups: Lists all available groups to join\n\t", end='', flush=True)
            print("groupusers <group_id>: List users of a private group \n\t", end='', flush=True)
            print("help: View commands\n\t", end='', flush=True)
            print("join <username>: Joins the public group with a given username\n\t", end='', flush=True)
            print("leave: Leaves the public group\n\t", end='', flush=True)
            print("message <message_id>: View a message from the public group\n\t", end='', flush=True)
            print("post <subject> <body>: Posts to the public group\n\t", end='', flush=True)
            print("users: List users of the public group\n> ", end='', flush=True)
    else:
        with print_lock:
            print("\nUnknown command.\n> ", end='', flush=True)

def windows_command_loop():
    import msvcrt
    print("> ", end='', flush=True)
    lpos = 0
    command = ''
    previous_commands = []
    prev_cmd_index = -1
    while True:
        char = msvcrt.getwch()
        if char == '\r':
            if command.strip() == '':
                with print_lock:
                    print("\n> ", end='', flush=True)
                lpos = 0
                continue
            if command.strip().lower() == 'exit':
                exit_command()
                break
            parse_command(command)
            prev_cmd_index = -1
            previous_commands.append(command)
            command = ''
            # process command here
            lpos = 0
        elif char == '\t':
            continue
        elif char == '\b':
            if lpos > 0:
                lpos -= 1
                new_command = command[0:lpos] + command[lpos+1:]
                command = new_command
                # remove character in place and reprint rest of line
                with print_lock:
                    print('\b', end='', flush=True)
                    print(command[lpos:] + ' ', end='', flush=True)
                    print('\b' * (len(command) - lpos + 1), end='', flush=True)
        elif char == '\xe0':
            arrow = msvcrt.getwch()
            if arrow == 'K':  # left arrow
                if lpos > 0:
                    with print_lock:
                        print('\b', end='', flush=True)
                    lpos -= 1
            elif arrow == 'M':  # right arrow
                if lpos < len(command):
                    with print_lock:
                        print(command[lpos], end='', flush=True)
                    lpos += 1
            elif arrow == 'H':  # up arrow
                if previous_commands:
                    # clear current line
                    if abs(prev_cmd_index) <= len(previous_commands):
                        with print_lock:
                            print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                        command = previous_commands[prev_cmd_index]
                        prev_cmd_index -= 1
                        
                        with print_lock:
                            print(command, end='', flush=True)
                        lpos = len(command)
            elif arrow == 'P':  # down arrow
                if previous_commands and prev_cmd_index < -1:
                    # clear current line
                    with print_lock:
                        print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                    prev_cmd_index += 1
                    command = previous_commands[prev_cmd_index]
                    
                    with print_lock:
                        print(command, end='', flush=True)
                    lpos = len(command)
                elif prev_cmd_index == -1:
                    # clear current line
                    with print_lock:
                        print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                    command = ''
                    lpos = 0
        #ctrl c
        elif char == '\x03':
            with print_lock:
                print("^C")
            exit_command()
            break
        else:
            lpos += 1
            command = command[:lpos-1] + char + command[lpos-1:]
            with print_lock:
                print(command[lpos-1:], end='', flush=True)
                print('\b' * (len(command) - lpos), end='', flush=True)
            

def unix_command_loop():
    pass
    import sys
    import termios
    import tty
    print("> ", end='', flush=True)
    lpos = 0
    command = ''
    previous_commands = []
    prev_cmd_index = -1

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            char = sys.stdin.read(1)
            if char == '\n':
                if command.strip() == '':
                    with print_lock:
                        print("\n> ", end='', flush=True)
                    lpos = 0
                    continue
                if command.strip().lower() == 'exit':
                    exit_command()
                    break
                parse_command(command)
                prev_cmd_index = -1
                previous_commands.append(command)
                command = ''
                lpos = 0
            elif char == '\x7f':  # backspace
                if lpos > 0:
                    lpos -= 1
                    new_command = command[0:lpos] + command[lpos+1:]
                    command = new_command
                    with print_lock:
                        print('\b', end='', flush=True)
                        print(command[lpos:] + ' ', end='', flush=True)
                        print('\b' * (len(command) - lpos + 1), end='', flush=True)
            elif char == '\x1b':  # escape sequence
                next1 = sys.stdin.read(1)
                if next1 == '[':
                    next2 = sys.stdin.read(1)
                    if next2 == 'D':  # left arrow
                        if lpos > 0:
                            with print_lock:
                                print('\b', end='', flush=True)
                            lpos -= 1
                    elif next2 == 'C':  # right arrow
                        if lpos < len(command):
                            with print_lock:
                                print(command[lpos], end='', flush=True)
                            lpos += 1
                    elif next2 == 'A':  # up arrow
                        if previous_commands:
                            if abs(prev_cmd_index) <= len(previous_commands):
                                with print_lock:
                                    print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                                command = previous_commands[prev_cmd_index]
                                prev_cmd_index -= 1
                                
                                with print_lock:
                                    print(command, end='', flush=True)
                                lpos = len(command)
                    elif next2 == 'B':  # down arrow
                        if previous_commands and prev_cmd_index < -1:
                            with print_lock:
                                print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                            prev_cmd_index += 1
                            command = previous_commands[prev_cmd_index]
                            
                            with print_lock:
                                print(command, end='', flush=True)
                            lpos = len(command)
                        elif prev_cmd_index == -1:
                            with print_lock:
                                print('\b' * lpos + ' ' * len(command) + '\b' * len(command), end='', flush=True)
                            command = ''
                            lpos = 0
            # ctrl c
            elif char == '\x03':
                with print_lock:
                    print("^C")
                exit_command()
                break
            else:
                lpos += 1
                command = command[:lpos-1] + char + command[lpos-1:]
                with print_lock:
                    print(command[lpos-1:], end='', flush=True)
                    print('\b' * (len(command) - lpos), end='', flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    global sock
    global message_thread
    global active_connection
    if os.name == 'nt':
        windows_command_loop()
    else:
        # same functionality as windows but for unix
        unix_command_loop()
    thread_stop.set()
    try:
        message_thread.join()
    except:
        pass
    if active_connection:
        sock.close()

if __name__ == "__main__":
    main()

