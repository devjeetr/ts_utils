from typing import Sequence, Type, Protocol, cast
from typing import Generic, TypeVar, Literal
from typing_extensions import Self

import dataclasses
from typing import Generator, Iterator, Callable, Optional

from tree_sitter import TreeCursor

#------------------------------------------------------------
#      generic cursor interface and implementation to ease
#      testing
#------------------------------------------------------------
T = TypeVar("T")


class Cursor(Protocol, Generic[T]):
    """A generic cursor interface offering a subset of the TreeCursor API.
    
    This is mostly used for testing purposes, enabling the use of mock objects
    instead of an actual TreeCursor.
    

    Attributes:
        node: The node at the current cursor position.
        goto_first_child: Move the cursor to the first child of the current node.
        goto_next_sibling: Move the cursor to the next sibling of the current node.
        goto_parent: Move the cursor to the parent of the current node.
    """
    node: T

    def goto_first_child(self) -> bool:
        ...

    def goto_next_sibling(self) -> bool:
        ...

    def goto_parent(self) -> bool:
        ...

    def copy(self) -> Self:
        ...


V = TypeVar("V")


@dataclasses.dataclass
class TreeSpec(Generic[T, V]):
    child_count: Callable[[T], int]
    get_child: Callable[[T, int], T]
    get_value: Callable[[T], V]

    def is_leaf(self, node: T) -> bool:
        return self.child_count(node) == 0

    def node_at_path(self, node: T, path: Sequence[int]) -> T:
        curr = node
        for child_idx in path:
            curr = self.get_child(curr, child_idx)
        return curr


class GenericCursor(Cursor[V], Generic[T, V]):
    """Generic cursor implementation for any tree-like structure."""

    def __init__(self,
                 tree: T,
                 tree_spec: TreeSpec[T, V],
                 path: tuple[int] = tuple()):
        self.tree = tree
        self.tree_spec = tree_spec
        self.path: list[int] = list(path)
        self.parent_stack = []
        self._node = tree
        self._node_dirty = True

    def copy(self):
        return GenericCursor(self.tree, self.tree_spec, path=tuple(self.path))

    @property
    def node(self):
        if self._node_dirty:
            self._node = self.tree_spec.node_at_path(self.tree, self.path)
            self._node_dirty = False

        return self.tree_spec.get_value(self._node)

    def goto_first_child(self):
        curr = self.tree_spec.node_at_path(self.tree, self.path)
        if not self.tree_spec.is_leaf(curr):
            self.parent_stack.append(curr)
            self.path.append(0)
            self._node_dirty = True
            return True

        return False

    def goto_parent(self):
        if not self.path:
            return False
        self._node = self.parent_stack.pop()
        self.path.pop()
        self._node_dirty = False
        return True

    def goto_next_sibling(self):
        if not self.parent_stack:
            # We are at the root, no siblings
            return False
        curr_child_idx = self.path[-1]
        parent = self.parent_stack[-1]
        child_count = self.tree_spec.child_count(parent)
        if curr_child_idx + 1 < child_count:
            self.path[-1] += 1
            self._node_dirty = True
            return True

        return False

    def __repr__(self):
        return f"Cursor({self.node})"


TupleNode = tuple[T, tuple["TupleNode[T]", ...]] | T
"""A nested tuple representing a tree structure.

    The general format of the tree is `(node_value, child1, child2, ...)`
    
    Examples:
        ```(2, 3, 4) # tree with root 2, and two children 3,4```
        ```(1, (2, 3), (4, 5,)) # tree with root 1, and two children 2 (with child 3) and 4 (with child 5)```
"""


def tuple_cursor(tree: TupleNode[T]) -> GenericCursor[TupleNode[T], T]:
    """A cursor for a tree represented as nested tuples.

    Args:
        tree: nested tuples of values of some type. 
    """

    def child_count(node: TupleNode[T]) -> int:
        if isinstance(node, tuple):
            _, *children = node
            return len(children)
        return 0

    def get_child_at_index(node: TupleNode[T], index: int) -> TupleNode[T]:
        if isinstance(node, tuple):
            _, *children = node
            return cast(TupleNode[T], children[index])

        raise IndexError()

    def get_value(node: TupleNode[V]) -> V:
        if isinstance(node, tuple):
            return node[0]
        return node

    return GenericCursor(tree,
                         TreeSpec(child_count, get_child_at_index, get_value))
