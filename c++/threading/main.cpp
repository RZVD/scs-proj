#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
#include <unistd.h>

void testThreadCreation(int runs, std::ofstream& datafile) {

    auto threadCreationFunction = [] { return; };
    auto startThread = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < runs; i++) {
        std::thread thread(threadCreationFunction);
        thread.join();
    }

    auto endThread = std::chrono::high_resolution_clock::now();
    auto durationThread =
        std::chrono::duration_cast<std::chrono::nanoseconds>(endThread - startThread);
    std::cout << "Time taken with thread: " << durationThread.count() << " milliseconds\n";

    auto startDirect = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < runs; ++i) {
        threadCreationFunction();
    }

    auto endDirect = std::chrono::high_resolution_clock::now();
    auto durationDirect =
        std::chrono::duration_cast<std::chrono::nanoseconds>(endDirect - startDirect);

    auto durationDifference =
        std::chrono::duration_cast<std::chrono::nanoseconds>(durationThread - durationDirect);

    std::cout << "Time taken without thread: " << durationDirect.count() << " milliseconds\n";

    std::cout << durationDifference.count() / runs << "\n";

    datafile << "ThreadCreation,C++," << runs << "," << durationDifference.count() / runs << "\n";
}

void testThreadContextSwitch(int runs, std::ofstream& datafile) {
    int parentToChild[2];
    int childToParent[2];

    if (pipe(parentToChild) == -1 || pipe(childToParent) == -1) {
        std::cerr << "Failed to create pipes\n";
        exit(1);
    }

    std::thread child([=] {
        char buf[2];
        for (int i = 0; i < runs; i++) {
            if (read(parentToChild[0], buf, 1) != 1) {
                perror("read");
                exit(EXIT_FAILURE);
            }
            const char response = 'A';
            write(childToParent[1], &response, 1);
        }
    });

    auto start = std::chrono::high_resolution_clock::now();
    char data = 'X';
    for (int i = 0; i < runs; i++) {
        write(parentToChild[1], &data, 1);
        char response;
        read(childToParent[0], &response, 1);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    child.join();

    datafile << "ThreadContextSwitches,C++," << runs << "," << duration.count() / 2 << "\n";
    close(parentToChild[1]);
    close(childToParent[0]);

}

void testThreadMigrations(int runs, std::ofstream& datafile) {
    unsigned long long duration = 0;
    for (int i = 0; i < runs; i++) {
        std::thread([&duration] {
            cpu_set_t mask;
            CPU_ZERO(&mask);
            CPU_SET(0, &mask);

            if (pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &mask) != 0) {
                std::cerr << "Error setting CPU affinity (migration)" << std::endl;
                exit(-1);
            }

            sched_yield();

            CPU_ZERO(&mask);
            CPU_SET(1, &mask);

            if (pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &mask) != 0) {
                std::cerr << "Error setting CPU affinity (migration)" << std::endl;
                exit(-1);
            }

            auto start = std::chrono::high_resolution_clock::now();

            sched_yield();

            auto end = std::chrono::high_resolution_clock::now();

            duration += std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        }).join();
    }

    datafile << "ThreadMigration,C++," << runs << "," << duration << "\n";
}

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "Wrong args" << '\n';
        std::cerr << "Usage: (1) Nr of thread runs:" << '\n';
        std::cerr << "Usage: (2) Nr of pipe reads runs:" << '\n';
        std::cerr << "Usage: (3) Nr of forced thread migrations:" << '\n';
        std::cerr << "Usage: (4) results file location:" << '\n';
        exit(-1);
    }

    int creation_runs = atoi(argv[1]);
    int pipe_runs = atoi(argv[2]);
    int thread_migrations = atoi(argv[3]);
    std::ofstream datafile(argv[4], std::ios::app);

    testThreadCreation(creation_runs, datafile);
    testThreadContextSwitch(pipe_runs, datafile);
    testThreadMigrations(thread_migrations, datafile);
    datafile.close();
    return 0;
}
