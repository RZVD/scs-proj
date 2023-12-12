const std = @import("std");
const p = @cImport({
    @cInclude("pthread.h");
});

extern fn pthread_setaffinity_np(p: p.pthread_t, fads: c_int, fadsd: *p.cpu_set_t) void;
extern fn pthread_getaffinity_np(p: p.pthread_t, fads: c_int, fadsd: *p.cpu_set_t) void;

pub fn cpuClearAndSet(cpu: u6, cpu_set: *p.cpu_set_t) void {
    var a: *u128 = @ptrCast(cpu_set.*.__bits[0..]);
    a.* = 0 | @as(u64, 1) << cpu;
}

pub fn runFunction() void {
    return;
}

fn testThreadCreation(runs: usize, file: *std.fs.File) !void {
    var timer = try std.time.Timer.start();
    for (runs) |_| {
        const thread = try std.Thread.spawn(.{}, runFunction, .{});
        thread.join();
    }
    const thread_time = timer.read();

    timer.reset();
    for (runs) |_| {
        runFunction();
    }
    const direct_time = timer.read();

    var buff: [100]u8 = undefined;
    _ = try file.write(try std.fmt.bufPrint(&buff, "ThreadCreation,Zig,{},{}\n", .{ runs, (thread_time - direct_time) / runs }));
}

fn ctxSwitchFn(runs: usize, parentToChild: [2]std.os.fd_t, childToParent: [2]std.os.fd_t) !void { // Zig doesn't support lambdas yet
    for (0..runs) |i| {
        _ = i;
        var buf: [2]u8 = undefined;
        _ = try std.os.read(parentToChild[0], buf[0..]);
        var response = [_]u8{'A'};
        _ = try std.os.write(childToParent[1], response[0..]);
    }
}

fn testThreadContextSwitch(runs: usize, datafile: *std.fs.File) !void {
    const parentToChild = try std.os.pipe();
    const childToParent = try std.os.pipe();

    const child = try std.Thread.spawn(.{}, ctxSwitchFn, .{ runs, parentToChild, childToParent });

    var timer = try std.time.Timer.start();
    var data = [_]u8{'X'};
    for (0..runs) |i| {
        _ = i;
        _ = try std.os.write(parentToChild[1], data[0..]);
        var response: [1]u8 = undefined;
        _ = try std.os.read(childToParent[0], response[0..]);
    }

    const duration = timer.read();
    child.join();
    var buff: [100]u8 = undefined;
    _ = try datafile.write(try std.fmt.bufPrint(&buff, "ThreadContextSwitches,Zig,{},{}\n", .{ runs, duration / 2 }));
}

fn migratingThread(duration: *u64) !void {
    var mask: p.cpu_set_t = undefined;
    cpuClearAndSet(0, &mask);
    pthread_setaffinity_np(p.pthread_self(), @sizeOf(p.cpu_set_t), &mask);

    _ = std.os.system.sched_yield();

    cpuClearAndSet(1, &mask);
    pthread_setaffinity_np(p.pthread_self(), @sizeOf(p.cpu_set_t), &mask);
    var timer = try std.time.Timer.start();
    _ = std.os.system.sched_yield();

    duration.* += timer.read();
}

pub fn testThreadMigrations(runs: usize, datafile: *std.fs.File) !void {
    var duration: u64 = 0;

    for (0..runs) |i| {
        _ = i;
        const child = try std.Thread.spawn(.{}, migratingThread, .{&duration});
        child.join();
    }

    var buff: [100]u8 = undefined;
    _ = try datafile.write(try std.fmt.bufPrint(&buff, "ThreadMigration,Zig,{},{}\n", .{ runs, duration }));
}

pub fn main() !void {
    const args = std.os.argv;
    if (args.len != 5) {
        std.debug.print("Wrong args\n", .{});
        std.debug.print("Usage: (1) Nr of thread runs\n", .{});
        std.debug.print("Usage: (2) results file location\n", .{});
        std.debug.print("Usage: (3) Nr of forced thread migrations\n", .{});
        std.debug.print("Usage: (4) results file location\n", .{});
        std.process.exit(1);
    }
    const creation_runs_str = std.mem.span(args[1]);
    const creation_runs = try std.fmt.parseInt(usize, creation_runs_str, 10);

    const pipe_runs_str = std.mem.span(args[2]);
    const pipe_runs = try std.fmt.parseInt(usize, pipe_runs_str, 10);

    const thread_migrations_str = std.mem.span(args[3]);
    const thread_migrations = try std.fmt.parseInt(usize, thread_migrations_str, 10);

    const datafile = std.mem.span(args[4]);

    var file = try std.fs.cwd().openFile(datafile, .{ .mode = .read_write });
    defer file.close();
    var stat = try file.stat();
    try file.seekTo(stat.size);

    try testThreadCreation(creation_runs, &file);
    try testThreadContextSwitch(pipe_runs, &file);
    try testThreadMigrations(thread_migrations, &file);
}
