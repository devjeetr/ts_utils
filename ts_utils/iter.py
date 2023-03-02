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
from typing import Callable, Generator, Iterator, Optional, Tuple, TypeVar

from tree_sitter import Node, TreeCursor
from ts_utils.cursor_utils import Cursor
from ts_utils.traversals import CursorLike, Moves, filter_moves, walk_tree

__all__ = [
    "iternodes",
    "iternodes_with_parent",
    "iternodes_with_edges",
    "iternodes_indexed",
    "Predicate",
    "TraversalFilter",
]

T = TypeVar("T")
Predicate = Callable[[T], bool]

TraversalFilter = Predicate[Node]
always = lambda val: lambda _: val
default_traversal_filter = always(True)


def iternodes(
        cursor: TreeCursor,
        traversal_filter: Optional[TraversalFilter] = None) -> Iterator[Node]:
    """Performs a preorder traversal starting from the position of the current cursor.

    The node from which the given cursor is derived is considered to be the root of the
    tree. The traversal_filter can be used to determine whether the subtree starting
    at a given node should be traversed, or skipped entirely.

    Args:
        cursor: a tree cursor at which to start the traversal
        traversal_filter: a predicate that determines which parts of
        the tree should be explored.. Defaults to None.

    Returns:
        an iterable of nodes in pre-order
    """

    iterator = walk_tree(
        cursor,
        should_traverse=lambda cursor: traversal_filter(cursor.node)
        if traversal_filter else True)
    iterator = filter_moves(Moves.DOWN, Moves.RIGHT)(iterator)
    return map(lambda cursor: cursor[0].node, iterator)


def iternodes_indexed(
    cursor: TreeCursor,
    traversal_filter: Optional[Predicate[Node]] = None
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
    traversal_filter: Optional[Predicate[Node]] = None,
    parent_filter: Optional[Predicate[Node]] = None,
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
    if parent_filter is None:
        parent_filter = always(True)

    if traversal_filter is None:
        traversal_filter = always(True)

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
    cursor: TreeCursor,
    traversal_filter: Optional[Predicate[Node]] = None
) -> Generator[Tuple[Node, Optional[Node], Optional[str]], None, None]:
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
    if traversal_filter is None:
        traversal_filter = always(True)
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


def iterchildren(cursor: TreeCursor) -> Iterator[Node]:
    """Creates an iterator that iterates over all the siblings
    of the node at the cursor position

    Parameters
    ----------
    cursor : TreeCursor
        cursor at which to start sibling
        iteration

    Yields
    -------
    Iterator[Node]
        sibling nodes
    """
    if not cursor.goto_first_child():
        return

    while cursor.goto_next_sibling():
        yield cursor.node


def itersiblings(cursor: TreeCursor) -> Iterator[Node]:
    """Creates an iterator that iterates over all the siblings
    of the node at the cursor position

    Parameters
    ----------
    cursor : TreeCursor
        cursor at which to start sibling
        iteration

    Yields
    -------
    Iterator[Node]
        sibling nodes
    """
    while cursor.goto_next_sibling():
        yield cursor.node


def iterancestors(cursor: TreeCursor) -> Iterator[Node]:
    """Creates an iterator that successively yields the
    path from the cursor's current position to the
    root of the subtree from which the cursor was created

    Parameters
    ----------
    cursor : TreeCursor
        cursor from which to start the iteration

    Yields
    -------
    Iterator[Node]
        All ancestors of the node at the initial
        cursor position
    """
    while cursor.goto_parent():
        yield cursor.node
