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
  private:
    Node<T>* head;
    Node<T>* tail;

  public:
    void push_front(T value) {
        Node<T>* newNode = new Node<T>(value);
        newNode->next = this->head;
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

    void traverse(void (*action)(T)) {
        Node<T>* current = this->head;
        while (current) {
            if (action) {
                action(current->data);
            }
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
