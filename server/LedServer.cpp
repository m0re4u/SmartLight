#include "LedServer.h"
#include <bitset>
#include <sstream>


LedServer::LedServer(int portno, RGBMatrix* matrix) : matrix(matrix), running_(true){
    // Setup server
    struct sockaddr_in serv_addr;
    // S U C C _ S T R E A M
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
        error("ERROR opening socket");
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);
    if (bind(sockfd, (struct sockaddr *) &serv_addr,sizeof(serv_addr)) < 0)
        error("ERROR on binding");
    std::cout << "setup server!" << '\n';
}

void LedServer::Run() {
    char name[128];
    gethostname(name, sizeof name);
    std::cout << "Running on: " << name << '\n';
    while (running_) {
        socklen_t clilen;
        char buffer[BUFF_SIZE];
        listen(sockfd, 5);
        clilen = sizeof(cli_addr);
        newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
        if (newsockfd < 0)
            error("ERROR on accept");
        // Make buffer all 0
        bzero(buffer, BUFF_SIZE);
        // Read in max BUFF_SIZE bytes into buffer
        int n = read(newsockfd, buffer, BUFF_SIZE);
        if (n < 0)
            error("ERROR reading from socket");

        EnDecode data;
        data.message.first = buffer[0];
        data.message.second = buffer[1];
        data.message.third = buffer[2];
        data.message.fourth = buffer[3];
        // Square s = data.square;
        std::cout << "x_pos: " << data.square.x_pos << '\n';
        std::cout << " y_pos: "<< data.square.y_pos << '\n';
        std::cout << " width: " << data.square.width << '\n';
        std::cout << " height: " << data.square.height << '\n';
        std::cout << " red: " << data.square.red << '\n';
        std::cout << " green: " << data.square.green << '\n';
        std::cout << " blue: " << data.square.blue << '\n';

        for (int w = 0; w < data.square.width; ++w)
        {
            for (int h = 0; h < data.square.height; ++h)
            {
                matrix->SetPixel(
                    data.square.x_pos + w,
                    data.square.y_pos + h,
                    data.square.red,
                    data.square.green,
                    data.square.blue
                );
            }
        }

        std::string answer("I got your "
            + std::to_string(data.square.width)
            + "x"
            + std::to_string(data.square.height)
            + " square!");
        std::cout << "Sending: " << answer << '\n';
        n = write(newsockfd, &answer, answer.size());
        if (n < 0)
            error("ERROR writing to socket");
    }
}

LedServer::~LedServer() {
    running_ = false;
    close(newsockfd);
    close(sockfd);
}

void LedServer::error(const char *msg)
{
    perror(msg);
    exit(1);
}
