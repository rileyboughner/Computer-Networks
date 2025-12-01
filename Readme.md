# Simple Bulletin Board System

A simple command-line bulletin board system that allows users to communicate in public and private groups.

# Team Members

- Eli Fouts
- Riley Boughner
- Ethan Chaplin

# Features

- Public and private message groups.
- Post messages with a subject and body.
- List users in the current group.
- List all available groups.
- A custom binary protocol for communication.

# How to Run

## Server

There are two server implementations available: Python and C++.

### Python Server

The Python server listens for incoming connections on a specified port.

```bash
python3 server.py
```

The server will start on port 5000 by default. If the port is in use, it will automatically increment to the next available port.

### C++ Server

To compile and run the C++ server:

```bash
g++ server.cpp -o server
./server
```

The C++ server will start on port 5000 by default.

## Client

The client connects to the server and allows users to send commands.

```bash
python3 client.py
```

# Commands

The client supports the following commands:

- `connect <ip> <port>`: Connect to the server.
- `join <username>`: Join the main public group.
- `post <subject> <message>`: Post a message to the current group.
- `users`: List all users in the current group.
- `leave`: Leave the current group.
- `message <id>`: Retrieve a message by its ID.
- `groups`: List all available groups.
- `groupjoin <group_id> <username>`: Join a private group.
- `grouppost <group_id> <subject> <message>`: Post a message to a private group.
- `groupusers <group_id>`: List all users in a private group.
- `groupleave <group_id>`: Leave a private group.
- `groupmessage <group_id> <message_id>`: Retrieve a message from a private group by its ID.
- `exit`: Disconnect from the server and exit the client.

# Protocol

All communication between the client and server is done over TCP sockets using a custom binary protocol.

## Message Structure

All messages are composed of a header and a data payload.

### Header

| Field         | Size (bytes) | Value        | Description                                                  |
|---------------|--------------|--------------|--------------------------------------------------------------|
| Magic Number  | 4            | `0xF00DBEEF` | A constant value to identify the start of a message.         |
| Length        | 2            |              | The length of the message payload in bytes.                  |
| Opcode        | 1            |              | The operation code for the message.                          |

### Data Payload

The data payload is a variable-length sequence of bytes that contains the message data. The structure of the data payload is determined by the opcode.

## Opcodes

The following opcodes are supported:

| Opcode | Name           | Description                               |
|--------|----------------|-------------------------------------------|
| 0x01   | JOIN           | Join the main public group.               |
| 0xA1   | GROUP_JOIN     | Join a private group.                     |
| 0x02   | POST           | Post a message to the main public group.  |
| 0xA2   | GROUP_POST     | Post a message to a private group.        |
| 0x03   | USERS          | Get a list of users in the main public group. |
| 0xA3   | GROUP_USERS    | Get a list of users in a private group.   |
| 0x04   | LEAVE          | Leave the main public group.              |
| 0xA4   | GROUP_LEAVE    | Leave a private group.                    |
| 0x05   | MESSAGE        | Get a message from the main public group. |
| 0xA5   | GROUP_MESSAGE  | Get a message from a private group.       |
| 0x06   | EXIT           | Disconnect from the server.               |
| 0x07   | GROUPS         | Get a list of all available groups.       |
| 0xFF   | ERROR          | An error occurred.                        |

# Requirements

- Python 3.6+
- g++ (for the C++ server)
- No external libraries are required.
