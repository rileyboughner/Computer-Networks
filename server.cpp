#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string>
#include <array>
#include <functional>
#include <cstdint>
#include <map>
#include <vector>
#include <iostream>
#include <thread>
#include <mutex>

enum OpCode {
    OP_JOIN = 0x1,
    OP_GROUP_JOIN = 0xA1,
    OP_POST = 0x2,
    OP_GROUP_POST = 0xA2,
    OP_USERS = 0x3,
    OP_GROUP_USERS = 0xA3,
    OP_LEAVE = 0x4,
    OP_GROUP_LEAVE = 0xA4,
    OP_MESSAGE = 0x5,
    OP_GROUP_MESSAGE = 0xA5,
    OP_EXIT = 0x6,
    OP_GROUPS = 0x7,
    OP_ERROR = 0xFF,
};

struct Message {
    std::string sender;
    std::string date;
    std::string subject;
    std::string body;
};

struct Group {
    std::string id;
    std::string longName;
    std::map<std::string, Message> messages;
    std::map<int, std::string> clients;
    std::vector<std::string> messageOrder;
};

Group publicGroup = {"Public", "Public group for all users.", {}, {}, {}};
Group privateGroup1 = {"Private1", "Private group 1.", {}, {}, {}};
Group privateGroup2 = {"Private2", "Private group 2.", {}, {}, {}};
Group privateGroup3 = {"Private3", "Private group 3.", {}, {}, {}};

std::map<std::string, Group*> groups = {
    {"Public", &publicGroup},
    {"Private1", &privateGroup1},
    {"Private2", &privateGroup2},
    {"Private3", &privateGroup3},
};

std::mutex messages_mutex;

void broadcastMessage(const std::vector<unsigned char>& message) {
    std::lock_guard<std::mutex> lock(messages_mutex);
    for (const auto& client : publicGroup.clients) {
        send(client.first, reinterpret_cast<const char*>(message.data()), message.size(), 0);
    }
}

static const std::array<unsigned char, 4> MAGIC = {0xF0, 0x0D, 0xBE, 0xEF};

static inline void push_uint16_le(std::vector<unsigned char>& out, uint16_t value) {
    out.push_back(static_cast<unsigned char>(value & 0xFF));
    out.push_back(static_cast<unsigned char>((value >> 8) & 0xFF));
}

static inline void appendStringWithLen(std::vector<unsigned char>& out, const std::string& s) {
    push_uint16_le(out, static_cast<uint16_t>(s.size()));
    out.insert(out.end(), s.begin(), s.end());
}

template<typename F>
std::vector<unsigned char> preparePacket(OpCode opcode, F fillBody) {
    std::vector<unsigned char> packet;
    packet.insert(packet.end(), MAGIC.begin(), MAGIC.end());
    std::vector<unsigned char> body;
    body.push_back(static_cast<unsigned char>(opcode));
    fillBody(body);
    push_uint16_le(packet, static_cast<uint16_t>(body.size()));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}
std::vector<unsigned char> prepareJoinResponse(std::string username) {
    return preparePacket(OP_JOIN, [&](std::vector<unsigned char>& body){
        appendStringWithLen(body, username);
    });
}

std::vector<unsigned char> prepareGroupJoinResponse(std::string username, std::string group_id, std::string group_name) {
    return preparePacket(OP_GROUP_JOIN, [&](std::vector<unsigned char>& body){
        appendStringWithLen(body, username);
        appendStringWithLen(body, group_id);
        appendStringWithLen(body, group_name);
    });
}

std::vector<unsigned char> preparePostResponse(std::string id, std::string sender, std::string date, std::string subject) {
    return preparePacket(OP_POST, [&](std::vector<unsigned char>& body){
        appendStringWithLen(body, id);
        appendStringWithLen(body, sender);
        appendStringWithLen(body, date);
        appendStringWithLen(body, subject);
    });
}

std::vector<unsigned char> prepareGroupPostResponse(std::string id, std::string sender, std::string date, std::string subject, std::string group_id, std::string group_name) {
    return preparePacket(OP_GROUP_POST, [&](std::vector<unsigned char>& body){
        appendStringWithLen(body, id);
        appendStringWithLen(body, sender);
        appendStringWithLen(body, date);
        appendStringWithLen(body, subject);
        appendStringWithLen(body, group_id);
        appendStringWithLen(body, group_name);
    });
}

std::vector<unsigned char> prepareUsersResponse(uint16_t num_users, std::vector<std::string> usernames) {
    return preparePacket(OP_USERS, [&](std::vector<unsigned char>& body){
        push_uint16_le(body, num_users);
        for (const auto& username : usernames) {
            appendStringWithLen(body, username);
        }
    });
}

std::vector<unsigned char> prepareGroupUsersResponse(uint16_t num_users, std::vector<std::string> usernames, std::string group_id, std::string group_name) {
    return preparePacket(OP_GROUP_USERS, [&](std::vector<unsigned char>& body){
        push_uint16_le(body, num_users);
        for (const auto& username : usernames) {
            appendStringWithLen(body, username);
        }
        appendStringWithLen(body, group_id);
        appendStringWithLen(body, group_name);
    });
}

std::vector<unsigned char> prepareLeaveResponse(std::string username) {
    return preparePacket(OP_LEAVE, [&](std::vector<unsigned char>& body) {
        appendStringWithLen(body, username);
    });
}

std::vector<unsigned char> prepareGroupLeaveResponse(std::string username, std::string group_id, std::string group_name) {
    return preparePacket(OP_GROUP_LEAVE, [&](std::vector<unsigned char>& body) {
        appendStringWithLen(body, username);
        appendStringWithLen(body, group_id);
        appendStringWithLen(body, group_name);
    });
}

std::vector<unsigned char> prepareMessageResponse(std::string message) {
    return preparePacket(OP_MESSAGE, [&](std::vector<unsigned char>& body) {
        appendStringWithLen(body, message);
    });
}

std::vector<unsigned char> prepareErrorResponse(std::string message) {
    return preparePacket(OP_ERROR, [&](std::vector<unsigned char>& body) {
        appendStringWithLen(body, message);
    });
}

std::vector<unsigned char> prepareGroupsResponse(uint16_t num_groups, std::vector<std::string> group_ids, std::vector<std::string> group_names) {
    return preparePacket(OP_GROUPS, [&](std::vector<unsigned char>& body){
        push_uint16_le(body, num_groups);
        for (size_t i = 0; i < group_ids.size(); i++) {
            appendStringWithLen(body, group_ids[i]);
            appendStringWithLen(body, group_names[i]);
        }
    });
}

int parseMessage(char* message, int sock) {
    if (message[0] != (char)0xF0 || message[1] != (char)0x0D || message[2] != (char)0xBE || message[3] != (char)0xEF) {
        return 1;
    }
    uint16_t body_length = (static_cast<unsigned char>(message[5]) << 8) | static_cast<unsigned char>(message[4]);
    unsigned char op_code = static_cast<unsigned char>(message[6]);
    if (op_code == OP_JOIN) {
        uint16_t username_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string username(&message[9], username_length);
        for (const std::pair<int, std::string> client : publicGroup.clients) {
            if (client.first == sock) {
                std::vector<unsigned char> response = prepareErrorResponse("Already joined.");
                send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
                return 0;
            }
            if (client.second == username) {
                std::vector<unsigned char> response = prepareErrorResponse("Username already taken.");
                send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
                return 0;
            }
        }
        broadcastMessage(prepareJoinResponse(username));
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            publicGroup.clients[sock] = username;
        }
        for (int i = std::max(0, (int)publicGroup.messageOrder.size() - 2); i < publicGroup.messageOrder.size(); i++) {
            std::string msgId = publicGroup.messageOrder[i];
            Message msg = publicGroup.messages[msgId];
            std::vector<unsigned char> response = preparePostResponse(msgId, msg.sender, msg.date, msg.subject);
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    else if (op_code == OP_GROUP_JOIN) {
        uint16_t group_id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string group_id(&message[9], group_id_length);
        if (groups.find(group_id) == groups.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Group ID not found.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        if (groups[group_id]->clients.find(sock) != groups[group_id]->clients.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Already joined.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        uint16_t username_length = (static_cast<unsigned char>(message[9 + group_id_length + 1]) << 8) | static_cast<unsigned char>(message[9 + group_id_length]);
        std::string username(&message[9 + group_id_length + 2], username_length);
        for (const std::pair<int, std::string> client : groups[group_id]->clients) {
            // if (client.first == sock) {
            //     std::vector<unsigned char> response = prepareErrorResponse("Already joined.");
            //     send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            //     return 0;
            // }
            if (client.second == username) {
                std::vector<unsigned char> response = prepareErrorResponse("Username already taken.");
                send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
                return 0;
            }
        }
        broadcastMessage(prepareGroupJoinResponse(username, group_id, groups[group_id]->longName));
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            groups[group_id]->clients[sock] = username;
        }
        for (int i = std::max(0, (int)groups[group_id]->messageOrder.size() - 2); i < groups[group_id]->messageOrder.size(); i++) {
            std::string msgId = groups[group_id]->messageOrder[i];
            Message msg = groups[group_id]->messages[msgId];
            std::vector<unsigned char> response = preparePostResponse(msgId, msg.sender, msg.date, msg.subject);
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
    else if (op_code == OP_POST) {
        std::string subject;
        std::string body;
        uint16_t subject_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        subject = std::string(&message[9], subject_length);
        uint16_t body_length = (static_cast<unsigned char>(message[9 + subject_length + 1]) << 8) | static_cast<unsigned char>(message[9 + subject_length]);
        body = std::string(&message[9 + subject_length + 2], body_length);
        Message newMessage;
        newMessage.sender = publicGroup.clients[sock];
        newMessage.subject = subject;
        newMessage.body = body;
        newMessage.date = "2024-01-01"; // Placeholder date
        std::string messageId = "msg" + std::to_string(publicGroup.messages.size() + 1);
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            publicGroup.messages[messageId] = newMessage;
            publicGroup.messageOrder.push_back(messageId);
        }
        broadcastMessage(preparePostResponse(messageId, newMessage.sender, newMessage.date, newMessage.subject));
    }
    else if (op_code == OP_GROUP_POST) {
        uint16_t group_id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string group_id(&message[9], group_id_length);
        if (groups.find(group_id) == groups.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Group ID not found.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        if (groups[group_id]->clients.find(sock) == groups[group_id]->clients.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Not a member of the group.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        std::string subject;
        std::string body;
        uint16_t subject_length = (static_cast<unsigned char>(message[9 + group_id_length + 1]) << 8) | static_cast<unsigned char>(message[9 + group_id_length]);
        subject = std::string(&message[9 + group_id_length + 2], subject_length);
        uint16_t body_length = (static_cast<unsigned char>(message[9 + group_id_length + 2 + subject_length + 1]) << 8) | static_cast<unsigned char>(message[9 + group_id_length + 2 + subject_length]);
        body = std::string(&message[9 + group_id_length + 2 + subject_length + 2], body_length);
        Message newMessage;
        newMessage.sender = groups[group_id]->clients[sock];
        newMessage.subject = subject;
        newMessage.body = body;
        newMessage.date = "2024-01-01"; // Placeholder date
        std::string messageId = "msg" + std::to_string(groups[group_id]->messages.size() + 1);
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            groups[group_id]->messages[messageId] = newMessage;
            groups[group_id]->messageOrder.push_back(messageId);
        }
        broadcastMessage(prepareGroupPostResponse(messageId, newMessage.sender, newMessage.date, newMessage.subject, group_id, groups[group_id]->longName));
    }
    else if (op_code == OP_USERS) {
        std::vector<std::string> usernames;
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            for (const auto& client : publicGroup.clients) {
                usernames.push_back(client.second);
            }
        }
        std::vector<unsigned char> response = prepareUsersResponse(usernames.size(), usernames);
        send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
    }
    else if (op_code == OP_GROUP_USERS) {
        uint16_t group_id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string group_id(&message[9], group_id_length);
        if (groups.find(group_id) == groups.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Group ID not found.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        if (groups[group_id]->clients.find(sock) == groups[group_id]->clients.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Not a member of the group.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        std::vector<std::string> usernames;
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            for (const auto& client : groups[group_id]->clients) {
                usernames.push_back(client.second);
            }
        }
        std::vector<unsigned char> response = prepareGroupUsersResponse(usernames.size(), usernames, group_id, groups[group_id]->longName);
        send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
    }
    else if (op_code == OP_LEAVE) {
        std::string username = publicGroup.clients[sock];
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            publicGroup.clients.erase(sock);
        }
        broadcastMessage(prepareLeaveResponse(username));
    }
    else if (op_code == OP_GROUP_LEAVE) {
        uint16_t group_id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string group_id(&message[9], group_id_length);
        if (groups.find(group_id) == groups.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Group ID not found.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        if (groups[group_id]->clients.find(sock) == groups[group_id]->clients.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Not a member of the group.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        std::string username = groups[group_id]->clients[sock];
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            groups[group_id]->clients.erase(sock);
        }
        broadcastMessage(prepareGroupLeaveResponse(username, group_id, groups[group_id]->longName));
    }
    else if (op_code == OP_MESSAGE) {
        uint16_t id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string id(&message[9], id_length);
        std::string body;
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            if (publicGroup.messages.find(id) != publicGroup.messages.end()) {
                Message msg = publicGroup.messages[id];
                body = msg.body;
            } else {
                std::vector<unsigned char> response = prepareErrorResponse("Message ID not found.");
                send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
                return 0;
            }
        }
        std::vector<unsigned char> response = prepareMessageResponse(body);
        send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
    }
    else if (op_code == OP_GROUP_MESSAGE) {
        uint16_t group_id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string group_id(&message[9], group_id_length);
        if (groups.find(group_id) == groups.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Group ID not found.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        if (groups[group_id]->clients.find(sock) == groups[group_id]->clients.end()) {
            std::vector<unsigned char> response = prepareErrorResponse("Not a member of the group.");
            send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
            return 0;
        }
        uint16_t id_length = (static_cast<unsigned char>(message[9 + group_id_length + 1]) << 8) | static_cast<unsigned char>(message[9 + group_id_length]);
        std::string id(&message[9 + group_id_length + 2], id_length);
        std::string body;
        {
            std::lock_guard<std::mutex> lock(messages_mutex);
            if (groups[group_id]->messages.find(id) != groups[group_id]->messages.end()) {
                Message msg = groups[group_id]->messages[id];
                body = msg.body;
            } else {
                std::vector<unsigned char> response = prepareErrorResponse("Message ID not found.");
                send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
                return 0;
            }
        }
        std::vector<unsigned char> response = prepareMessageResponse(body);
        send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
    }
    else if (op_code == OP_EXIT) {
        if (publicGroup.clients.find(sock) != publicGroup.clients.end()) {
            std::string username = publicGroup.clients[sock];
            {
                std::lock_guard<std::mutex> lock(messages_mutex);
                publicGroup.clients.erase(sock);
            }
            broadcastMessage(prepareLeaveResponse(username));
        }
        for (auto& pair : groups) {
            Group* group = pair.second;
            if (group->clients.find(sock) != group->clients.end()) {
                std::string username = group->clients[sock];
                {
                    std::lock_guard<std::mutex> lock(messages_mutex);
                    group->clients.erase(sock);
                }
                broadcastMessage(prepareGroupLeaveResponse(username, group->id, groups[group->id]->longName));
            }
        }
        close(sock);
        return -1;
    }
    else if (op_code == OP_GROUPS) {
        std::vector<std::string> group_ids;
        std::vector<std::string> group_names;
        for (const auto& pair : groups) {
            group_ids.push_back(pair.first);
            group_names.push_back(pair.second->longName);
        }
        std::vector<unsigned char> response = prepareGroupsResponse(group_ids.size(), group_ids, group_names);
        send(sock, reinterpret_cast<const char*>(response.data()), response.size(), 0);
    }
    else {
        return 1;
    }
    return 0;
}

void connectionThread(int sock) {
    for(;;) {
        char buffer[1024] = {0};
        if (recv(sock, buffer, sizeof(buffer), 0) <= 0) {
            std::cout << "Client disconnected." << std::endl;
            break;
        }
        if (parseMessage(buffer, sock) == -1) {
            break;
        }
    }
}

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serverAddress;
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(8083);
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    bind(sock, (struct sockaddr*)&serverAddress, sizeof(serverAddress));
    listen(sock, 5);
    for (;;) {
        int clientSocket = accept(sock, nullptr, nullptr);
        std::thread(connectionThread, clientSocket).detach();
    }
    
    return 0;
}