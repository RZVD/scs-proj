const std = @import("std");
const Allocators = enum {
    c_allocator, ca,
    page_allocator, pa,
    general_purpose_allocator, gpa,
    arena_allocator, aa 
};

pub fn LinkedList(comptime T: type) type {
    return struct {
        const Self = @This();
        head: ?*Node = null,
        tail: ?*Node = null,

        pub const Node = struct {
            data: T,
            next: ?*Node = null,
        };

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
            const newNode = try allocator.create(Node);
            newNode.* = .{
                .data = value,
                .next = null,
            };

            if (self.tail != null) {
                self.tail.?.next = newNode;
            } else {
                self.head = newNode;
            }
            self.tail = newNode;
        }

        pub fn push_front(self: *Self, value: T, allocator: std.mem.Allocator) !void {
            const newNode = try allocator.create(Node);
            newNode.* = .{
                .data = value,
                .next = self.head,
            };

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

fn dynamic_memory_tests(
    in: *std.fs.File,
    out: *std.fs.File,
    arraySize: usize,
    allocator: std.mem.Allocator,
    alloc_type: Allocators,
) !void {
    var reader = in.reader();
    var timer = try std.time.Timer.start();
    var array = try allocator.alloc(i32, arraySize);
    var duration = timer.read();

    var buff: [100]u8 = undefined;

    _ = try out.write(try std.fmt.bufPrint(&buff, "Dynamic Array creation,Zig_{s},{},{}\n", .{ @tagName(alloc_type), arraySize, duration }));

    var buffer: [32]u8 = undefined;
    var ll = LinkedList(i32){};
    defer ll.destroy(allocator);

    var idx: usize = 0;
    while (reader.readUntilDelimiter(&buffer, ' ')) |numStr| : (idx += 1) {
        const num = try std.fmt.parseInt(i32, numStr, 10);
        array[idx] = num;
    } else |err| {
        if (err != error.EndOfStream) {
            return err;
        }
    }
    timer.reset();

    for (array) |element| {
        try ll.push_back(element, allocator);
    }

    _ = try out.write(try std.fmt.bufPrint(&buff, "LinkedList creation,Zig_{s},{},{}\n", .{ @tagName(alloc_type), arraySize, timer.read() }));

    timer.reset();
    ll.traverse();
    _ = try out.write(try std.fmt.bufPrint(&buff, "LinkedList traversal,Zig_{s},{},{}\n", .{ @tagName(alloc_type), arraySize, timer.read() }));
}

fn static_memory_tests(out: *std.fs.File) !void {
    var static_arr: [100000]i32 = undefined;
    var timer = try std.time.Timer.start();
    var buff: [100]u8 = undefined;

    for (0..100000) |i| {
        static_arr[i] = @intCast(i + 1);
    }

    _ = try out.write(try std.fmt.bufPrint(&buff, "Static Memory test,Zig,100000,{}\n", .{timer.read()}));
}

pub fn main() !void {
    const args = std.os.argv;
    if (args.len != 5) {
        std.debug.print("Wrong args\n", .{});
        std.debug.print("Usage: (1) testcase file location\n", .{});
        std.debug.print("Usage: (2) results file location\n", .{});
        std.debug.print("Usage: (3) array_size\n", .{});
        std.debug.print("Usage: (4) allocator_type\n\tSupported: c_allocator (ca), page_allocator(pa), general_purpose_allocator(gpa), arena_allocator(aa)\n", .{});
        std.process.exit(1);
    }
    const testcase = std.mem.span(args[1]);
    const results = std.mem.span(args[2]);
    const size = std.mem.span(args[3]);
    const allocator_type = std.mem.span(args[4]);
    const arraySize = try std.fmt.parseInt(usize, size, 10);
    _ = arraySize;

    var testfile = try std.fs.cwd().openFile(testcase, .{});
    defer testfile.close();

    var results_file = try std.fs.cwd().openFile(results, .{ .mode = .read_write });
    var stat = try results_file.stat();
    try results_file.seekTo(stat.size);
    defer results_file.close();

    const alloc = std.meta.stringToEnum(Allocators, allocator_type).?;

    var allocator = switch (alloc) {
        .general_purpose_allocator, .gpa => general_purpose_allocator: {
            var gpa = std.heap.GeneralPurposeAllocator(.{}){};
            break :general_purpose_allocator gpa.allocator();
        },
        .c_allocator, .ca => std.heap.c_allocator,
        .page_allocator, .pa => std.heap.page_allocator,
        .arena_allocator, .aa => arena_allocator: {
            var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
            break :arena_allocator arena.allocator();
        },
    };

    std.debug.print("{}", .{@typeName(allocator)});

    // try dynamic_memory_tests(&testfile, &results_file, arraySize, allocator, alloc);
    // try static_memory_tests(&results_file);
}
