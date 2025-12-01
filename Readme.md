Project 2 - Simple Bulletin Board System

Team Members:



Eli Fouts

Riley Boughner

Ethan Chaplin





How to Run

Start Server

bashpython server.py

Server listens on port 5000 (auto-increments if unavailable).

Start Client

bashpython client.py



Commands



connect - Connect to server (prompts for username)

join - Join the main group

post - Post a message (prompts for subject and message)

leave - Leave current group

exit - Disconnect and quit



Part 2 commands (not implemented): groups, groupjoin, grouppost, groupusers, groupleave, groupmessage



Protocol

All communication uses JSON format over TCP sockets.

Client → Server:

json{"command": "commandName", "param1": "value1"}

Server → Client:

json{"status": "message", "subjects": \[...], "messages": \[...]}



Requirements



Python 3.6+

No external libraries needed (uses standard library only)

