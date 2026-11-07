"""
Doubly Linked List
Internal helper used by LRU for O(1) insertion, removal, and move-to-end.
Not part of the public cache interface.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Node:
    """A single node in the doubly linked list."""

    key: str
    value: Any
    prev: Node | None = field(default=None, repr=False)
    next: Node | None = field(default=None, repr=False)

class DoublyLinkedList:
    """
    Doubly linked list with sentinel head and tail nodes.

    Provides O(1) append (to tail), remove, and move_to_end operations.
    The least-recently-used item sits right after head; the most-recently-used
    sits right before tail.
    """

    def __init__(self) -> None:
        self._head = Node(key="__HEAD__", value=None)
        self._tail = Node(key="__TAIL__", value=None)
        self._head.next = self._tail
        self._tail.prev = self._head

    def append(self, node: Node) -> None:
        """Insert *node* just before the tail sentinel (most-recent position)."""
        prev = self._tail.prev
        prev.next = node
        node.prev = prev
        node.next = self._tail
        self._tail.prev = node

    def remove(self, node: Node) -> None:
        """Unlink *node* from the list."""
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None

    def move_to_end(self, node: Node) -> None:
        """Move an existing *node* to the most-recent position (before tail)."""
        self.remove(node)
        self.append(node)

    def pop_front(self) -> Node | None:
        """Remove and return the least-recent node (right after head), or None if empty."""
        if self._head.next is self._tail:
            return None
        node = self._head.next
        self.remove(node)
        return node

    def clear(self) -> None:
        """
        Remove all nodes from the list and sever their pointers.
        """
        node = self._head.next
        while node is not self._tail:
            nxt = node.next
            node.prev = None
            node.next = None
            node = nxt
        self._head.next = self._tail
        self._tail.prev = self._head
