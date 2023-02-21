from collections import namedtuple
from dataclasses import dataclass
from typing import (Any, Generic, ItemsView, Iterable, Iterator,
                    MutableMapping, Optional, TypeVar)

from ts_utils.core import hash_node
from tree_sitter import Node

__all__ = ["NodeCollection", "NodeInfo"]

class IdCounter:
    def __init__(self, start=0):
        self.id = start
    
    def __call__(self):
        curr_id = self.id
        self.id += 1

        return curr_id

NodeInfo = namedtuple('NodeInfo', ['node', 'id'])
class NodeCollection:
    """A container for a collection of nodes. It maintains unique
    ids for each node in the collection.

    >>> collection = NodeCollection(tree.walk()) # build from cursor
    >>> collection[tree.root_node]
        => 0
    >>> for node_id, node in collection:
            ...
    """
    def __init__(self, iterable: Optional[Iterable[Node]] = None):
        self._nodes: dict[Any, NodeInfo] = {}
        self.id_counter = IdCounter()

        if iterable is not None:
            for node in iterable:
                self.add(node)
                

    def __getitem__(self, node: Node) -> int:
        node_hash = hash_node(node)
        if node_hash not in self._nodes:
            raise ValueError(f"Node {node} not found in NodeCollection")

        return self._nodes[node_hash].id
        
    def add(self, node: Node):
        node_hash = hash_node(node)
        self._nodes[node_hash] = NodeInfo(node, self.id_counter())

    def remove(self, node) -> None:
        node_hash = hash_node(node)
        del self._nodes[node_hash]
    
    def __len__(self):
        return len(self._nodes)
    
    def __iter__(self):
        for node_info in self._nodes.values():
            yield node_info.id, node_info.node


    def __contains__(self, node):
        node_hash = hash_node(node)
        return node_hash in self._nodes

# NodeDictValue = namedtuple("NodeDictValue", ['node', 'data'])


K = TypeVar("K")
V = TypeVar("V")


@dataclass
class NodeDictValue(Generic[V]):
    node: Node
    data: V
class NodeDict(MutableMapping[Node, V]):
    """A mutable mapping that allows usage with tree_sitter Nodes.
    """
    def __init__(self, iterable: Optional[Iterable[tuple[Node, V]]]=None) -> None:
        self._mapping: dict[int, NodeDictValue[V]] = {}

        if iterable is not None:
            for node, data in iterable:
                self[node] = data
    
    def __getitem__(self, node: Node):
        _hash = hash_node(node)

        if _hash not in self._mapping:
            raise KeyError()
        
        return self._mapping[_hash].data
    
    def __setitem__(self, node: Node, value: V):
        _hash = hash_node(node)

        self._mapping[_hash]= NodeDictValue(node, value)
    
    
    def __delitem__(self, node: Node) -> None:
        _hash = hash_node(node)

        del self._mapping[_hash]
    
    def __iter__(self):
        return self.keys()

    def __len__(self):
        return len(self._mapping)

    def values(self) -> Iterable[ V]:
        for entry in self._mapping.values():
            yield entry.data
    
    def keys(self) -> Iterator[Node]:
        for node_dict_value in self._mapping.values():
            yield node_dict_value.node
    
    def items(self) -> Iterable[tuple[Node, V]]:
        for entry in self._mapping.values():
            yield entry.node, entry.data
    

