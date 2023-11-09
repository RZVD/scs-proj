const std = @import("std");

pub fn LinkedList(comptime T: type) type {
    return struct {
        const Self = @This();

        pub const Node = struct {
            data: T,
            next: ?*Node = null,

            pub const Data = T;

            pub fn insertAfter(self: *Node, new_node: *Node) void {
                new_node.next = self.next;
                self.next = new_node;
            }
        };

        head: ?*Node,
        tail: ?*Node,
    };
}
