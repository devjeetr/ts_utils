from collections import namedtuple
from typing import Any, Iterable, MutableMapping, Optional

from ts_utils.core import hash_node
from ts_utils.typing import Node


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

NodeDictValue = namedtuple("NodeDictValue", ['node', 'data'])

class NodeDict(MutableMapping):
    """A mutable mapping that allows usage with tree_sitter Nodes.
    """
    def __init__(self, iterable=None) -> None:
        self._mapping: dict[Any, NodeDictValue] = {}

        if iterable is not None:
            for node, data in iterable:
                self[node] = data
    
    def __getitem__(self, node):
        _hash = hash_node(node)

        if _hash not in self._mapping:
            raise KeyError()
        
        return self._mapping[_hash].data
    
    def __setitem__(self, node, value):
        _hash = hash_node(node)

        self._mapping[_hash]= NodeDictValue(node, value)
    
    def __delitem__(self, node: Node) -> None:
        _hash = hash_node(node)

        del self._mapping[_hash]
    
    def __iter__(self) -> Iterable:
        for node_dict_value in self._mapping.values():
            yield node_dict_value.node, node_dict_value.data

    def __len__(self):
        return len(self._mapping)
