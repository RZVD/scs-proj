#include <array>
#include <bits/chrono.h>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>

template <typename T> class Node {
  public:
    T data;
    Node* next;

    Node(T value) {
        this->data = value;
        this->next = nullptr;
    }
};

template <typename T> class LinkedList {
  public:
    Node<T>* head;
    Node<T>* tail;

    LinkedList() {
        head = nullptr;
        tail = nullptr;
    }

    LinkedList(T val) {
        Node<T>* newNode = new Node<T>(val);
        head = newNode;
        tail = newNode;
    }

    void push_front(T value) {
        Node<T>* newNode = new Node<T>(value);
        newNode->next = this->head;
        if (this->head == nullptr) {
            this->tail = newNode;
        }
        this->head = newNode;
    }

    void push_back(T value) {
        Node<T>* newNode = new Node<T>(value);
        if (this->tail) {
            this->tail->next = newNode;
        } else {
            this->head = newNode;
        }
        this->tail = newNode;
    }

    template <typename U> LinkedList<U> map(U (*transform)(T)) {
        Node<T>* current = this->head;
        LinkedList<U> newList = LinkedList<U>();

        while (current) {
            if (transform != nullptr) {
                newList.push_back(transform(current->data));
            }
            current = current->next;
        }
        return newList;
    }

    void display() {
        Node<T>* current = head;
        std::cout << "[";
        while (current) {
            std::cout << current->data;
            if (current->next) {
                std::cout << ", ";
            }
            current = current->next;
        }

        std::cout << "]\n";
    }

    void traverse() {
        volatile Node<T>* current = head; // Necesarry to prevent loop unrolling when comipling with -O3 flags

        while (current) {
            current = current->next;
        }

    }

    ~LinkedList() {
        Node<T>* current = head;
        Node<T>* nextNode = nullptr;

        while (current) {
            nextNode = current->next;
            delete current;
            current = nextNode;
        }
    }
};

void parse_testfile(char* testfile_path, char* datafile_path, int array_size) {
    std::ifstream testfile(testfile_path);
    std::ofstream datafile(datafile_path, std::ios::app);

    auto start = std::chrono::high_resolution_clock::now();
    int* array = (int*)malloc(sizeof(int) * array_size);
    auto end = std::chrono::high_resolution_clock::now();

    auto duration =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    datafile << "Dynamic Array creation,C++," << array_size << ","
             << duration.count() << '\n';
    std::cout << "Array alloc: " << duration.count() << '\n';

    int idx = 0;
    int el = -1;
    while (testfile >> el) {
        array[idx++] = el;
    }
    testfile.close();

    start = std::chrono::high_resolution_clock::now();
    auto ll = new LinkedList<int>();
    for (int i = 0; i < array_size; i++) {
        ll->push_back(array[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    duration =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    std::cout << "Time to create linked list: " << duration.count() << '\n';

    datafile << "LinkedList creation,C++," << array_size << ","
             << duration.count() << '\n';

    start = std::chrono::high_resolution_clock::now();
    ll->traverse();
    end = std::chrono::high_resolution_clock::now();

    duration =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    datafile << "LinkedList traversal,C++," << array_size << ","
             << duration.count() << '\n';


    int static_arr[100000] = {0};

    start = std::chrono::high_resolution_clock::now();
    for(int i = 0; i < 100000;i++) {
        static_arr[i] = i + 1;
    }
    end = std::chrono::high_resolution_clock::now();

    duration =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    datafile << "Static Memory test,C++," << 100000 << "," << duration.count() << '\n';
    datafile.close();
}

int main(int argc, char** argv) {

    if (argc != 4) {
        std::cerr << "Wrong args" << '\n';
        std::cerr << "Usage: (1) testcase file location:" << '\n';
        std::cerr << "Usage: (2) results file location:" << '\n';
        std::cerr << "Usage: (3) array_size:" << '\n';
        exit(-1);
    }

    int array_size = atoi(argv[3]);
    parse_testfile(argv[1], argv[2], array_size);

    return 0;
}
