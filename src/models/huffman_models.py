import heapq
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Node:
    frequency: int
    symbol: Optional[Any] = None
    left: Optional['Node'] = None
    right: Optional['Node'] = None

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __repr__(self):
        if self.symbol is not None:
            return f"Node(symbol={self.symbol}, freq={self.frequency})"
        return f"Node(freq={self.frequency})"

class MinHeap:
    def __init__(self):
        self.heap = []

    def push(self, node):
        heapq.heappush(self.heap, node)

    def pop(self):
        return heapq.heappop(self.heap) if self.heap else None

    def size(self):
        return len(self.heap)

    def is_empty(self):
        return len(self.heap) == 0