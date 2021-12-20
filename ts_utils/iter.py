"""
This module contains a set of generators that perform
traversals of a tree_sitter Tree.

All traversal functions take a function, 'traversal_filter' that
determines which subtrees in the tree should be visited. All traversal
functions are designed so that given a tree and a traversal filter, 
they all yield nodes in the same order. 

```
tree: Tree = ...
traversal_filter = ...
nodes_a = [node for node in iternodes(tree.walk(), traversal_filter)]
nodes_b = [node for _, node, _ in iternodes_with_edges(tree.walk(), traversal_filter)]

nodes_a == nodes_b # True
```
"""

from enum import Enum
from typing import Callable, Generator, Optional, Tuple, TypeVar

from tree_sitter import Node, TreeCursor

__all__ = [
    "iternodes", "iternodes_with_parent", "iternodes_with_edges",
    "iternodes_indexed"
]

T = TypeVar("T")
Predicate = Callable[[T], bool]

always = lambda val: lambda _: val


def iternodes(
    cursor: TreeCursor, traversal_filter: Predicate[Node] = always(True)
) -> Generator[Node, None, None]:
    """Performs a tree-order traversal starting from the position of the current cursor.
    The node from which the given cursor is derived is considered to be the root of the 
    tree. The traversal_filter can be used to determine whether the subtree starting
    at a given node should be traversed, or skipped entirely.

    Parameters
    ----------
    cursor : TreeCursor
        a tree cursor at which to start
        the traversal
    traversal_filter : Predicate[Node], optional
        a predicate that determines which parts of
        the tree should be explored., by default always(True)

    Yields
    -------
    Generator[Node, None, None]
        an iterable of nodes in pre-order
    """
    reached_root = False
    while reached_root == False:
        node = cursor.node

        if traversal_filter(node):
            # We only traverse nodes that are filtered
            # by traversal function. If traversal_filter(node) == False,
            # we skip the entire subtree
            yield node

            if cursor.goto_first_child():
                continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False


def iternodes_indexed(
    cursor: TreeCursor, traversal_filter: Predicate[Node] = always(True)
) -> Generator[Tuple[int, Node], None, None]:
    """indexed version of iternodes.

    Parameters
    ----------
    cursor : TreeCursor
        a tree cursor at which to start
        the traversal
    traversal_filter : Predicate[Node], optional
        a predicate that determines which parts of
        the tree should be explored., by default always(True)

    Yields
    -------
    Generator[Node, None, None]
        an iterable of nodes in pre-order
    """
    yield from enumerate(iternodes(cursor, traversal_filter=traversal_filter))


class Move(Enum):
    PARENT = 1
    CHILD = 2
    SIBLING = 3


NodeWithIndex = Tuple[int, Node]


def iternodes_with_parent(
    cursor: TreeCursor,
    traversal_filter: Predicate[Node] = always(True),
    parent_filter: Predicate[Node] = always(True),
) -> Generator[Tuple[Node, Optional[Node]], None, None]:
    """Performs an inorder traversal starting from the position of the current cursor.
    The node from which the given cursor is derived is considered to be the root of the 
    tree.

    Parameters
    ----------
    cursor : TreeCursor
        a tree cursor at which to start
        the traversal
    traversal_filter : Predicate[Node], optional
        a predicate that determines which parts of
        the tree should be explored., by default always(True)
    parent_filter : Predicate[Node], optional
        a predicate that determines which nodes in
        the tree can serve as parent nodes, by default always(True)
    

    Yields
    -------
    Generator[Tuple[TreeCursor, Optional[Move]], None, None]
        an iterable of cursor and optionally move
    """
    reached_root = False
    parent_stack = []
    while reached_root == False:
        node = cursor.node
        if traversal_filter(node):

            # We only traverse nodes that are filtered
            # by traversal function. If traversal_filter(node) == False,
            # we skip the entire subtree
            yield node, parent_stack[-1] if parent_stack else None

            if cursor.goto_first_child():
                if parent_filter(node):
                    parent_stack.append(node)

                continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if parent_stack and parent_filter(cursor.node):
                parent_stack.pop()

            if cursor.goto_next_sibling():
                retracing = False


def iternodes_with_edges(
    cursor: TreeCursor, traversal_filter: Predicate[Node] = always(True)
) -> Generator[Tuple[TreeCursor, Optional[Move], Optional[str]], None, None]:
    """Similar to iternodes_with_parent, but also provides edge (node field)
    information along with the node and it's parent.

    Parameters
    ----------
    cursor : TreeCursor
        a tree cursor at which to start
        the traversal
    traversal_filter : Predicate[Node], optional
        a predicate that determines which parts of
        the tree should be explored., by default always(True)

    Yields
    -------
    Generator[Tuple[TreeCursor, Optional[Move]], None, None]
        an iterable of cursor and optionally move
    """
    reached_root = False
    parent_stack = []
    while reached_root == False:
        node = cursor.node
        if traversal_filter(node):
            # We only traverse nodes that are filtered
            # by traversal function. If traversal_filter(node) == False,
            # we skip the entire subtree
            yield node, parent_stack[
                -1] if parent_stack else None, cursor.current_field_name()

            if cursor.goto_first_child():
                parent_stack.append(node)
                continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if parent_stack:
                parent_stack.pop()

            if cursor.goto_next_sibling():
                retracing = False
