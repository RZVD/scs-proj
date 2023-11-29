#include <iostream>
#include <thread>
#include <fstream>
#include <unistd.h>
#include <cstdlib>

void childThread(int readPipe, int writePipe) {
    char buffer;
    for (;;) {

        ssize_t bytesRead = read(readPipe, &buffer, 1);
        if (bytesRead <= 0) {
            break;
        }
        const char response = 'A'; // Modify this as needed
        write(writePipe, &response, 1);
    }
}

void ping_pong(int n, char* data_file) {
    int parentToChild[2];
    int childToParent[2];

    std::ofstream datafile(data_file, std::ios::app);


    if (pipe(parentToChild) == -1 || pipe(childToParent) == -1) {
        std::cerr << "Failed to create pipes\n";
        exit(1);
    }

    std::thread child(childThread, parentToChild[0], childToParent[1]);


    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < n; ++i) {
        const char data = 'X';
        write(parentToChild[1], &data, 1);

        char response;
        read(childToParent[0], &response, 1);

    }
    auto end = std::chrono::high_resolution_clock::now();


    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    datafile << "ThreadContextSwitches,C++," << n <<","<< duration.count() / 2 <<"\n";
    close(parentToChild[1]);
    datafile.close();
    close(childToParent[0]);

    child.join();
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Wrong args" << '\n';
        std::cerr << "Usage: (1) Nr of bytes sent through pipes:" << '\n';
        std::cerr << "Usage: (2) results file location:" << '\n';
        exit(-1);
    }
    

    int numIterations = std::atoi(argv[1]);

    ping_pong(numIterations, argv[2]);
    return 0;
}
