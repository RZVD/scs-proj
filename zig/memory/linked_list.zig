const std = @import("std");

pub fn LinkedList(comptime T: type) type {
    return struct {
        const Self = @This();
        head: ?*Node = null,
        tail: ?*Node = null,

        pub const Node = struct {
            data: T,
            next: ?*Node = null,

            pub const Data = T;

            pub fn insertAfter(self: *Node, new_node: *Node) void {
                new_node.next = self.next;
                self.next = new_node;
            }
        };

        pub fn push_back(self: Self, value: T, allocator: std.mem.Allocator) !void {
            const newNode = try allocator.create(Node);
            newNode.data = value;
            if (self.tail != null) {
                self.tail.?.next = newNode;
            } else {
                self.head = newNode;
            }
            self.tail = newNode;
        }

        pub fn push_front(self: Self, value: T, allocator: std.mem.Allocator) !void {
            const newNode = try allocator.create(Node);
            newNode.data = value;

            newNode.next = self.head;
            self.head = newNode;
        }

        const callbackFunction = *const fn (value: T) void;
        pub fn traverse(self: Self, action: callbackFunction) void {
            const current = self.head;

            while (current != null) {
                action(current.?.data);
            }
            current = current.next;
        }
    };
}
