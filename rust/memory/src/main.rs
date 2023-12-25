use std::fs::{File, OpenOptions};
use std::io::{self};

use std::io::Write;
use std::mem;
use std::time::Instant;

pub struct List<T> {
    head: Link<T>,
    tail: Link<T>,
}

enum Link<T> {
    Empty,
    More(Box<Node<T>>),
}

struct Node<T> {
    elem: T,
    next: Link<T>,
}

impl<T> List<T> {
    pub fn new() -> Self {
        List {
            head: Link::Empty,
            tail: Link::Empty,
        }
    }

    pub fn push_front(&mut self, elem: T) {
        let new_node = Box::new(Node {
            next: mem::replace(&mut self.head, Link::Empty),
            elem,
        });

        if let Link::Empty = &self.head {
            self.tail = mem::replace(&mut self.head, Link::Empty);
        }
        self.head = Link::More(new_node);
    }
    pub fn push_back(&mut self, elem: T) {
        let new_node = Box::new(Node {
            elem,
            next: Link::Empty,
        });

        if let Link::Empty = self.head {
            self.head = Link::More(new_node);
        } else {
            let mut current = &mut self.head;
            while let Link::More(ref mut node) = *current {
                current = &mut node.next;
            }
            *current = Link::More(new_node);
        }
    }

    pub fn traverse(&self) {
        let mut current = &self.head;

        while let Link::More(ref node) = *current {
            current = &node.next;
        }
    }
}

impl<T> Drop for List<T> {
    fn drop(&mut self) {
        let mut cur_link = mem::replace(&mut self.head, Link::Empty);

        while let Link::More(mut boxed_node) = cur_link {
            cur_link = mem::replace(&mut boxed_node.next, Link::Empty);
        }
    }
}

impl<T: std::fmt::Display> std::fmt::Display for List<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[")?;

        let mut current = &self.head;
        while let Link::More(ref node) = current {
            write!(f, "{}", node.elem)?;

            if let Link::More(_) = &node.next {
                write!(f, ", ")?;
            }
            current = &node.next;
        }

        write!(f, "]")
    }
}

fn dynamic_memory_tests(testfile_path: &str, out: &mut File, array_size: usize) -> io::Result<()> {
    let start = Instant::now();
    let mut _array: Vec<i32> = Vec::with_capacity(array_size);
    let duration = start.elapsed();

    let array: Vec<i32> = std::fs::read_to_string(&testfile_path)?
        .split_whitespace()
        .map(|s| s.parse().unwrap())
        .collect::<Vec<_>>();

    println!("{}", duration.as_nanos());

    writeln!(
        out,
        "Dynamic Array creation,Rust,{},{}",
        array_size,
        duration.as_nanos()
    )?;

    let start = Instant::now();
    let mut ll = List::new();
    for &elem in &array {
        ll.push_front(elem);
    }
    let duration = start.elapsed();
    println!("Time to create linked list: {:?}", duration);

    writeln!(
        out,
        "LinkedList creation,Rust,{},{}",
        array_size,
        duration.as_nanos()
    )?;

    let start = Instant::now();
    ll.traverse();
    let duration = start.elapsed();
    writeln!(
        out,
        "LinkedList traversal,Rust,{},{}",
        array_size,
        duration.as_nanos()
    )?;

    Ok(())
}

fn static_memory_tests(out: &mut File) -> io::Result<()> {
    let mut static_array: [i32; 100000] = [0; 100000];
    let start = Instant::now();
    for (idx, el) in static_array.iter_mut().enumerate() {
        *el = idx as i32 + 1;
    }
    let duration = start.elapsed();

    writeln!(
        out,
        "Static Memory test,Rust,{},{}",
        100000,
        duration.as_nanos()
    )?;
    Ok(())
}

fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();

    if args.len() != 4 {
        eprintln!("Wrong args");
        eprintln!("Usage: (1) testcase file location");
        eprintln!("Usage: (2) results file location");
        eprintln!("Usage: (3) array_size");
        std::process::exit(-1);
    }

    let array_size: usize = args[3].parse().expect("Invalid array size");

    let mut out = OpenOptions::new()
        .write(true)
        .append(true)
        .open(&args[2])?;

    dynamic_memory_tests(&args[1], &mut out, array_size)?;
    static_memory_tests(&mut out)?;

    Ok(())
}
