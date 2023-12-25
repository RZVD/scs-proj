#include <array>
#include <bits/chrono.h>
#include <chrono>
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

    template <typename U> auto map(U (*transform)(T)) -> LinkedList<U> {
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
        volatile Node<T>* current = head; // Necesary to prevent loop unrolling
                                          // when comipling with -O3 flags

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

void dynamic_memory_tests(std::ifstream& in, std::ofstream& out, int array_size) {

    auto start = std::chrono::high_resolution_clock::now();
    int* array = (int*)malloc(sizeof(int) * array_size);
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    out << "Dynamic Array creation,C++," << array_size << "," << duration.count() << '\n';

    std::cout << "Array alloc: " << duration.count() << '\n';

    int idx = 0;
    int el = -1;

    while (in >> el) {
        array[idx++] = el;
    }

    start = std::chrono::high_resolution_clock::now();
    auto ll = new LinkedList<int>();

    for (int i = 0; i < array_size; i++) {
        ll->push_back(array[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    std::cout << "Time to create linked list: " << duration.count() << '\n';

    out << "LinkedList creation,C++," << array_size << "," << duration.count() << '\n';

    start = std::chrono::high_resolution_clock::now();
    ll->traverse();
    end = std::chrono::high_resolution_clock::now();

    duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    out << "LinkedList traversal,C++," << array_size << "," << duration.count() << '\n';
}

void static_memory_tests(std::ofstream& out) {

    int static_arr[100000] = {0};

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 100000; i++) {
        static_arr[i] = i + 1;
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    out << "Static Memory test,C++," << 100000 << "," << duration.count() << '\n';
}

int main(int argc, char** argv) {

    if (argc != 4) {
        std::cerr << "Wrong args" << '\n';
        std::cerr << "Usage: (1) testcase file location:" << '\n';
        std::cerr << "Usage: (2) results file location:" << '\n';
        std::cerr << "Usage: (3) array_size:" << '\n';
        exit(-1);
    }

    std::ifstream testfile(argv[1]);
    std::ofstream datafile(argv[2], std::ios::app);
    int array_size = atoi(argv[3]);

    dynamic_memory_tests(testfile, datafile, array_size);
    static_memory_tests(datafile);
    return 0;
}
