import enum
from typing import (Callable,  Iterator,  Optional,
                     TypeVar )

from ts_utils.cursor_utils import Cursor

CursorLike = TypeVar("CursorLike", bound=Cursor)
"""Any object that implements the [Cursor][ts_utils.cursor_utils.Cursor] protocol."""

class Moves(enum.Enum):
    """Enum representing the possible moves that can be made by a TreeCursor."""
    RIGHT = enum.auto()
    """corresponds to `cursor.goto_next_sibling()`"""
    UP = enum.auto()
    """corresponds to `cursor.goto_parent()`"""
    DOWN = enum.auto()
    """corresponds to `cursor.goto_first_child()`"""


def walk_tree(
    cursor: CursorLike,
    should_traverse: Optional[Callable[[CursorLike], bool]] = None
) -> Iterator[tuple[CursorLike, Moves]]:
    """Iteratively walk tree-sitter trees using the TreeCursor API.

    The recommended way to traverse a `tree-sitter` tree is to use the
    `TreeCursor` API. However, the api is stateful and requires some bookkeeping
    for iterative traversals. This function abstracts away the bookkeeping
    and walks the tree using the cursor using the minimum number of moves possible.
    This is a low-level primitive that can be used to build tree traversals such
    as preorder, postorder etc.  
    
    Warning:
        Do not modify the cursor once you start walking the tree. If you want to use
        the cursor during iterations, make a copy using `TreeCursor.copy()`.
    Args:
        cursor: stateful cursor like object. This cursor will be mutated.
        should_traverse: a function that decides whether or not to traverse the subtree
                        rooted at a given node. Defaults to None.
 

    Yields:
        A tuple of the cursor and the move that was made
    """
    reached_root = False
    results = []

    last_move: Moves = Moves.DOWN
    while not reached_root:
        skip_current_node = not should_traverse(
            cursor) if should_traverse else False

        if not skip_current_node:
            yield cursor, last_move

        # Here, we filter if we want to go down this
        # subtree or not
        if not skip_current_node:
            if cursor.goto_first_child():
                last_move = Moves.DOWN
                continue

            # Leaf: No child nodes, but we pretend like
            # we went to the subtree at this node and
            # came back up
            yield cursor, Moves.UP

        if cursor.goto_next_sibling():
            last_move = Moves.RIGHT if not skip_current_node else Moves.DOWN
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                reached_root = True
                break

            yield cursor, Moves.UP

            if cursor.goto_next_sibling():
                last_move = Moves.RIGHT
                break
    return results
