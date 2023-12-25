use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::thread;
use std::time::Instant;

use libc::{CPU_SET, CPU_ZERO};

mod pthread {
    pub use libc::{c_int, cpu_set_t, pthread_self, pthread_setaffinity_np};
}

extern "C" {
    fn sched_yield() -> libc::c_int;
}

pub fn cpu_clear_and_set(cpu: usize, cpuset: &mut pthread::cpu_set_t) {
    unsafe {
        CPU_ZERO(cpuset);
        CPU_SET(cpu, cpuset)
    }
}

fn run_function() {
    return;
}

pub fn test_thread_creation(runs: usize, file: &mut File) -> io::Result<()> {
    let timer = Instant::now();
    for _ in 0..runs {
        let thread = thread::spawn(|| run_function());
        thread.join().unwrap();
    }
    let thread_time = timer.elapsed();

    let timer = Instant::now();
    for _ in 0..runs {
        run_function();
    }
    let direct_time = timer.elapsed();

    let duration_difference = thread_time - direct_time;

    writeln!(
        file,
        "ThreadCreation,Rust,{},{}",
        runs,
        duration_difference.as_nanos() / runs as u128
    )?;

    Ok(())
}

pub async fn test_tokio_thread_creation(runs: usize, file: &mut File) -> io::Result<()> {
    let timer = Instant::now();

    for _ in 0..runs {
        let _ = tokio::task::spawn(async {
            return;
        })
        .await;
    }

    let thread_time = timer.elapsed();

    let timer = Instant::now();
    for _ in 0..runs {
        run_function();
    }
    // asdf
    let direct_time = timer.elapsed();

    let duration_difference = thread_time - direct_time;

    writeln!(
        file,
        "ThreadCreation,RustTokio,{},{}",
        runs,
        duration_difference.as_nanos() / runs as u128
    )?;

    Ok(())
}

fn ctx_switch_fn(
    runs: usize,
    parent_to_child: [libc::c_int; 2],
    child_to_parent: [libc::c_int; 2],
) -> io::Result<()> {
    let buf = [0u8; 2].as_mut_ptr() as *mut libc::c_void;
    for _ in 0..runs {
        unsafe {
            libc::read(parent_to_child[0], buf, 1);
            let response = [0u8; 1].as_mut_ptr() as *const libc::c_void;
            libc::write(child_to_parent[1], response, 1);
        }
    }
    Ok(())
}

pub fn test_thread_context_switch(runs: usize, file: &mut File) -> io::Result<()> {
    let (parent_to_child, child_to_parent) = unsafe {
        let mut fd1 = [0; 2];
        let mut fd2 = [0; 2];
        libc::pipe(fd1.as_mut_ptr());
        libc::pipe(fd2.as_mut_ptr());
        (fd1, fd2)
    };

    let child = thread::spawn(move || ctx_switch_fn(runs, parent_to_child, child_to_parent));

    let timer = Instant::now();
    let data = [b'X'].as_mut_ptr() as *const libc::c_void;
    for _ in 0..runs {
        unsafe {
            libc::write(parent_to_child[1], data, 1);
            let response = [0u8; 1].as_mut_ptr() as *mut libc::c_void;
            libc::read(child_to_parent[0], response, 1);
        }
    }
    let duration = timer.elapsed().as_nanos();

    child.join().unwrap()?;
    writeln!(
        file,
        "ThreadContextSwitches,Rust,{},{:?}",
        runs,
        duration / 2
    )?;
    Ok(())
}

fn migrating_thread() -> u64 {
    let mut mask: libc::cpu_set_t = unsafe { std::mem::zeroed() };

    cpu_clear_and_set(0, &mut mask);
    unsafe {
        libc::pthread_setaffinity_np(
            libc::pthread_self(),
            std::mem::size_of_val(&mask) as libc::size_t,
            &mask,
        );
    }

    unsafe {
        sched_yield();
    }

    cpu_clear_and_set(1, &mut mask);
    unsafe {
        libc::pthread_setaffinity_np(
            libc::pthread_self(),
            std::mem::size_of_val(&mask) as libc::size_t,
            &mask,
        );
    }
    let start_time = Instant::now();

    unsafe {
        sched_yield();
    }

    let end_time = Instant::now();

    (end_time - start_time).as_nanos() as u64
}

pub fn test_thread_migrations(runs: usize, file: &mut File) -> io::Result<()> {
    let mut duration: u64 = 0;

    for _ in 0..runs {
        let handle = thread::spawn(move || migrating_thread());
        duration += handle.join().unwrap()
    }

    println!("{}", duration);
    writeln!(file, "ThreadMigration,Rust,{},{}", runs, duration)?;

    Ok(())
}

#[tokio::main]
pub async fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 5 {
        eprintln!("Wrong args");
        eprintln!("Usage: (1) Nr of thread runs");
        eprintln!("Usage: (2) Nr of pipe reads runs");
        eprintln!("Usage: (3) Nr of forced thread migrations");
        eprintln!("Usage: (4) results file location");
        std::process::exit(1);
    }

    let creation_runs = args[1]
        .parse::<usize>()
        .expect("Invalid input for thread runs");
    let pipe_runs = args[2]
        .parse::<usize>()
        .expect("Invalid input for pipe runs");
    let thread_migrations = args[3]
        .parse::<usize>()
        .expect("Invalid input for thread migrations");
    let datafile_location = &args[4];

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open(datafile_location)?;

    test_thread_creation(creation_runs, &mut file)?;
    test_tokio_thread_creation(creation_runs, &mut file).await?;
    test_thread_context_switch(pipe_runs, &mut file)?;
    test_thread_migrations(thread_migrations, &mut file)?;

    Ok(())
}
