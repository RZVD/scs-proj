#include <iostream>
#include <fstream>
#include <thread>
#include <chrono>

void runFunction() {
    return;
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "Wrong args" << '\n';
        std::cerr << "Usage: (1) Nr of thread runs:" << '\n';
        std::cerr << "Usage: (2) results file location:" << '\n';
        exit(-1);
    }

    int runs = atoi(argv[1]);

    auto startThread = std::chrono::high_resolution_clock::now();
    std::ofstream datafile(argv[2], std::ios::app);

    for (int i = 0; i < runs; i++) {
        std::thread thread(runFunction);
        thread.join();
    }

    auto endThread = std::chrono::high_resolution_clock::now();
    auto durationThread = std::chrono::duration_cast<std::chrono::nanoseconds>(endThread - startThread);
    std::cout << "Time taken with thread: " << durationThread.count() << " milliseconds\n";

    auto startDirect = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < runs; ++i) {
        runFunction();
    }

    auto endDirect = std::chrono::high_resolution_clock::now();
    auto durationDirect = std::chrono::duration_cast<std::chrono::nanoseconds>(endDirect - startDirect);

    auto durationDifference = std::chrono::duration_cast<std::chrono::nanoseconds>(durationThread - durationDirect);

    std::cout << "Time taken without thread: " << durationDirect.count() << " milliseconds\n";

    std::cout << durationDifference.count() / runs << "\n";

    datafile << "ThreadCreation,C++," << runs <<","<< durationDifference.count() / runs <<"\n";

    datafile.close();

    return 0;
}
