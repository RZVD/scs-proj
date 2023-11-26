const std = @import("std");

pub fn LinkedList(comptime T: type) type {
    return struct {
        const Self = @This();
        head: ?*Node = null,
        tail: ?*Node = null,

        pub const Node = struct {
            data: T,
            next: ?*Node = null,
        };

        fn nodeConstructor(value: T, next: ?*Node, allocator: std.mem.Allocator) !?*Node {
            const newNode = try allocator.create(Node);
            newNode.data = value;
            newNode.next = next;
            return newNode;
        }

        pub fn destroy(self: *Self, allocator: std.mem.Allocator) void {
            var current = self.head;
            var nextNode: ?*Node = null;
            while (current != null) : (current = nextNode) {
                nextNode = current.?.next;
                allocator.destroy(current.?);
            }

            self.head = null;
            self.tail = null;
        }

        pub fn push_back(self: *Self, value: T, allocator: std.mem.Allocator) !void {
            const newNode = try nodeConstructor(value, null, allocator);
            if (self.tail != null) {
                self.tail.?.next = newNode;
            } else {
                self.head = newNode;
            }
            self.tail = newNode;
        }

        pub fn push_front(self: *Self, value: T, allocator: std.mem.Allocator) !void {
            const newNode = try nodeConstructor(value, self.head, allocator);
            if (self.head == null) {
                self.tail = newNode;
            }
            self.head = newNode;
        }

        const callbackFunction = fn (value: T) void;
        pub fn map(self: *Self, action: callbackFunction) void {
            var current = self.head;

            while (current != null) : (current = current.next) {
                action(current.data);
            }
        }

        pub fn display(self: *Self) void {
            var current = self.head;

            std.debug.print("[", .{});
            while (current) |node| : (current = current.?.next) {
                std.debug.print("{}", .{node.data});
                if (current.?.next != null) {
                    std.debug.print(", ", .{});
                }
            }

            std.debug.print("]\n", .{});
        }

        pub fn traverse(self: *Self) void {
            var current = self.head;

            while (current != null) : (current = current.?.next) {}
        }
    };
}

pub fn parseTestFile(testfilePath: []const u8, datafilePath: []const u8, arraySize: usize, allocator: std.mem.Allocator) !void {
    var testfile = try std.fs.cwd().openFile(testfilePath, .{});
    defer testfile.close();
    var reader = testfile.reader();

    var results_file = try std.fs.cwd().openFile(datafilePath, .{ .mode = .read_write });
    var stat = try results_file.stat();
    try results_file.seekTo(stat.size);

    defer results_file.close();

    var timer = try std.time.Timer.start();
    var start = try std.time.Instant.now();
    var array = try allocator.alloc(i32, arraySize);
    var end = try std.time.Instant.now();
    var duration = end.since(start);

    var buff: [100]u8 = undefined;

    _ = try results_file.write(try std.fmt.bufPrint(&buff, "Dynamic Array creation,Zig,{},{}\n", .{ arraySize, duration }));

    var buffer: [32]u8 = undefined;
    var ll = LinkedList(i32){};
    defer ll.destroy(allocator);

    var idx: usize = 0;
    while (reader.readUntilDelimiter(&buffer, ' ')) |numStr| {
        const num = try std.fmt.parseInt(i32, numStr, 10);
        array[idx] = num;
        idx += 1;
    } else |err| {
        if (err != error.EndOfStream) {
            return err;
        }
    }
    timer.reset();

    for (array) |element| {
        try ll.push_back(element, allocator);
    }

    _ = try results_file.write(try std.fmt.bufPrint(&buff, "LinkedList creation,Zig,{},{}\n", .{ arraySize, timer.read() }));

    timer.reset();
    ll.traverse();
    _ = try results_file.write(try std.fmt.bufPrint(&buff, "LinkedList traversal,Zig,{},{}\n", .{ arraySize, timer.read() }));
}

pub fn main() !void {
    const args = std.os.argv;

    if (args.len != 4) {
        std.debug.print("Wrong args\n", .{});
        std.debug.print("Usage: (1) testcase file location\n", .{});
        std.debug.print("Usage: (2) results file location\n", .{});
        std.debug.print("Usage: (3) array_size\n", .{});
        std.process.exit(1);
    }

    const testcase = std.mem.span(args[1]);
    const results = std.mem.span(args[2]);
    const size = std.mem.span(args[3]);
    const arraySize = try std.fmt.parseInt(usize, size, 10);

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();
    _ = allocator;
    try parseTestFile(testcase, results, arraySize, std.heap.c_allocator);
    // var ll = LinkedList(i32){};
    //
    // try ll.push_back(1, std.heap.page_allocator);
    // try ll.push_back(2, std.heap.page_allocator);
    // try ll.push_back(3, std.heap.page_allocator);
    // try ll.push_back(4, std.heap.page_allocator);
    // try ll.push_back(5, std.heap.page_allocator);
    // ll.display();
}
