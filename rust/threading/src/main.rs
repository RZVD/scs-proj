use std::env;
use std::fs::{OpenOptions};
use std::io::{self, Write};
use std::thread;
use std::time::{Instant};

fn run_function() {
    return;
}

fn main() -> io::Result<()> {
    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        eprintln!("Wrong args");
        eprintln!("Usage: (1) Nr of thread runs");
        eprintln!("Usage: (2) results file location");
        std::process::exit(1);
    }

    let runs: usize = args[1].parse().expect("Invalid number of runs");
    let datafile = &args[2];

    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .append(true)
        .open(datafile)?;

    let start_thread = Instant::now();
    for _ in 0..runs {
        let _ = thread::spawn(|| run_function()).join();
    }
    let thread_time = start_thread.elapsed();

    let start_direct = Instant::now();
    for _ in 0..runs {
        run_function();
    }
    let direct_time = start_direct.elapsed();

    let duration_difference = thread_time - direct_time;

    let result_line = format!(
        "ThreadCreation,Rust,{},{}\n",
        runs,
        duration_difference.as_nanos() / runs as u128
    );

    file.write_all(result_line.as_bytes())?;

    Ok(())
}
