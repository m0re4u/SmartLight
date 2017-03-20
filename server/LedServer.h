#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <iostream>

#include "led-matrix.h"
#include "thread.h"

#define BUFF_SIZE 8

struct Square {
    // x
    // y
    // w
    // h
    // colours
    // unsigned offset:2;
    unsigned blue:KPWMBITS;
    unsigned green:KPWMBITS;
    unsigned red:KPWMBITS;
    unsigned height:4;
    unsigned width:5;
    unsigned y_pos:4;
    unsigned x_pos:5;
};

struct Message {
    char fourth;
    char third;
    char second;
    char first;
};

union EnDecode {
    Square square;
    Message message;
};

class LedServer : public Thread {
private:
    // Sockets
    int sockfd, newsockfd;
    // Client address, filled by accept()
    int cli_addr;
    // LED Matrix
    RGBMatrix *const matrix;

public:
    // Constructor
    LedServer(int portno, RGBMatrix* matrix);
    //
    void Run();
    virtual ~LedServer();
    void error(const char *msg);
protected:
    volatile bool running_;
};
