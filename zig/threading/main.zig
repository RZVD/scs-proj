const std = @import("std");

pub fn runFunction() void {
    return;
}

pub fn main() !void {
    const args = std.os.argv;
    if (args.len != 3) {
        std.debug.print("Wrong args\n", .{});
        std.debug.print("Usage: (1) Nr of thread runs\n", .{});
        std.debug.print("Usage: (2) results file location\n", .{});
        std.process.exit(1);
    }

    const runs_str = std.mem.span(args[1]);

    const runs = try std.fmt.parseInt(usize, runs_str, 10);
    const datafile = std.mem.span(args[2]);

    var file = try std.fs.cwd().openFile(datafile, .{ .mode = .read_write });
    defer file.close();
    var stat = try file.stat();
    try file.seekTo(stat.size);

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
