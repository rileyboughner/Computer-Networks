#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string>
#include <map>
#include <vector>
#include <iostream>

enum OpCode {
    OP_JOIN = 0x1,
    OP_POST = 0x2,
    OP_USERS = 0x3,
    OP_LEAVE = 0x4,
    OP_MESSAGE = 0x5,
    OP_EXIT = 0x6,
    OP_ERROR = 0xFF,
};

std::vector<unsigned char> prepareJoinResponse(std::string username) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_JOIN));
    char* username_cstr = const_cast<char*>(username.c_str());
    body.push_back(static_cast<unsigned char>(username.size() & 0xFF));
    body.push_back(static_cast<unsigned char>((username.size() >> 8) & 0xFF));
    for (size_t i = 0; i < username.size(); ++i) {
        body.push_back(static_cast<unsigned char>(username_cstr[i]));
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

std::vector<unsigned char> preparePostResponse(std::string id, std::string sender, std::string date, std::string subject) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_POST));
    for (auto data : {id, sender, date, subject}) {
        char* cstr = const_cast<char*>(data.c_str());
        body.push_back(static_cast<unsigned char>(data.size() & 0xFF));
        body.push_back(static_cast<unsigned char>((data.size() >> 8) & 0xFF));
        for (size_t i = 0; i < data.size(); ++i) {
            body.push_back(static_cast<unsigned char>(cstr[i]));
        }
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

std::vector<unsigned char> prepareUsersResponse(uint16_t num_users, std::vector<std::string> usernames) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_USERS));
    body.push_back(static_cast<unsigned char>(num_users & 0xFF));
    body.push_back(static_cast<unsigned char>((num_users << 8) & 0xFF));
    for (auto data : usernames) {
        char* cstr = const_cast<char*>(data.c_str());
        body.push_back(static_cast<unsigned char>(data.size() & 0xFF));
        body.push_back(static_cast<unsigned char>((data.size() >> 8) & 0xFF));
        for (size_t i = 0; i < data.size(); ++i) {
            body.push_back(static_cast<unsigned char>(cstr[i]));
        }
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

std::vector<unsigned char> prepareLeaveResponse(std::string username) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_LEAVE));
    char* cstr = const_cast<char*>(username.c_str());
    body.push_back(static_cast<unsigned char>(username.size() & 0xFF));
    body.push_back(static_cast<unsigned char>((username.size() >> 8) & 0xFF));
    for (size_t i = 0; i < username.size(); ++i) {
        body.push_back(static_cast<unsigned char>(cstr[i]));
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

std::vector<unsigned char> prepareMessageResponse(std::string message) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_MESSAGE));
    char* cstr = const_cast<char*>(message.c_str());
    body.push_back(static_cast<unsigned char>(message.size() & 0xFF));
    body.push_back(static_cast<unsigned char>((message.size() >> 8) & 0xFF));
    for (size_t i = 0; i < message.size(); ++i) {
        body.push_back(static_cast<unsigned char>(cstr[i]));
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

std::vector<unsigned char> prepareErrorResponse(std::string message) {
    std::vector<unsigned char> packet = {0xF0, 0x0D, 0xBE, 0xEF};
    std::vector <unsigned char> body;
    body.push_back(static_cast<unsigned char>(OP_ERROR));
    char* cstr = const_cast<char*>(message.c_str());
    body.push_back(static_cast<unsigned char>(message.size() & 0xFF));
    body.push_back(static_cast<unsigned char>((message.size() >> 8) & 0xFF));
    for (size_t i = 0; i < message.size(); ++i) {
        body.push_back(static_cast<unsigned char>(cstr[i]));
    }
    packet.push_back(static_cast<unsigned char>(body.size() & 0xFF));
    packet.push_back(static_cast<unsigned char>((body.size() >> 8) & 0xFF));
    packet.insert(packet.end(), body.begin(), body.end());
    return packet;
}

void parseMessage(char* message) {
    if (message[0] != (char)0xF0 || message[1] != (char)0x0D || message[2] != (char)0xBE || message[3] != (char)0xEF) {
        return;
    }
    uint16_t body_length = (static_cast<unsigned char>(message[5]) << 8) | static_cast<unsigned char>(message[4]);
    unsigned char op_code = static_cast<unsigned char>(message[6]);
    if (op_code == OP_JOIN) {
        uint16_t username_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string username(&message[9], username_length);
    }
    else if (op_code == OP_POST) {
        std::string subject;
        std::string body;
        uint16_t subject_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        subject = std::string(&message[9], subject_length);
        uint16_t body_length = (static_cast<unsigned char>(message[9 + subject_length + 1]) << 8) | static_cast<unsigned char>(message[9 + subject_length]);
        body = std::string(&message[9 + subject_length + 2], body_length);
        std::cout << "Post Subject: " << subject << ", Body: " << body << std::endl;
    }
    else if (op_code == OP_USERS) {
        // handle users request
    }
    else if (op_code == OP_LEAVE) {
        // handle leave request
    }
    else if (op_code == OP_MESSAGE) {
        uint16_t id_length = (static_cast<unsigned char>(message[8]) << 8) | static_cast<unsigned char>(message[7]);
        std::string id(&message[9], id_length);
    }
    else if (op_code == OP_EXIT) {
        // handle exit
    }
    else {
        return;
    }
}

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serverAddress;
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(8085);
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    bind(sock, (struct sockaddr*)&serverAddress, sizeof(serverAddress));
    listen(sock, 5);
    int clientSocket = accept(sock, nullptr, nullptr);
    char buffer[1024] = {0};
    for(;;) {
        recv(clientSocket, buffer, sizeof(buffer), 0);
        parseMessage(buffer);
        for (int i = 0; i < 1024; ++i) {
            buffer[i] = 0;
        }
    }
    
    return 0;
}